from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from manager.models import Opus, Corpus, OpusMeta
from workflow.Workflow import Workflow
import string
from django.core.files import File

from django.core.files.base import ContentFile

import os.path, io
import pymysql
import pymysql.cursors


class Command(BaseCommand):
    """Import a corpus from the Sequentia source"""

    MYSQL_HOST='localhost'
    MYSQL_DB = 'sequentia'
    MYSQL_USER='adminLiturgics'
    MYSQL_PWD='mdpAdmin'
    
    # Path to MusicXML files in Sequentia
    MXML_PATH = "/Applications/MAMP/htdocs/sequentia/www/files/musicxml/"
    
    help = 'Import a corpus from the Sequentia source'

    def add_arguments(self, parser):
        # Arguments: the id of the "Document" item in Sequentia, and the corpus ref
        # a corpus in Neuma
        parser.add_argument('-s', dest='source_id')
        parser.add_argument('-c', dest='corpus_ref')

        # Third argument: the action (can be 'sources' or 'import')
        parser.add_argument('-a', dest='action')
        
    def handle(self, *args, **options):
        
        connexion = pymysql.connect(self.MYSQL_HOST, self.MYSQL_USER, 
                         self.MYSQL_PWD, self.MYSQL_DB,
        cursorclass=pymysql.cursors.DictCursor)

        # Get the list of sources
        curseur = connexion.cursor()
        curseur.execute("select d.id, d.titreUniforme, count(*) as nb_pieces" 
                         + " from Document as d, Piece as p where p.idDocument=d.id group by d.id")
        docs = curseur.fetchall()
        sources = {}
        for doc in docs:
            sources[str(doc['id'])] = doc
        
        if options['action'] == 'sources':
            for doc in docs:
                cpieces = connexion.cursor()
                cpieces.execute("select * from Piece as p where p.idDocument=%s" % doc['id'])
                pieces = cpieces.fetchall()
                nb_mxml =0
                for piece in pieces:
                    mxml_name = self.MXML_PATH + "musicxml-" +  str(piece['idPiece']) + ".xml"
                    if os.path.exists(mxml_name):
                        nb_mxml = nb_mxml+1
                
                if nb_mxml > 0:
                    print("%s (id %s), nb pieces: %s. Nb MusicXML: %s" % (doc['titreUniforme'], doc['id'],  doc["nb_pieces"], nb_mxml))
                      
        elif options['action'] == 'import':
            print ("Source id = " + options['source_id'])
            source = sources [options['source_id']]
            
            # Check the corpus: for safety, it must have been created before
            try:
                corpus = Corpus.objects.get(ref=options['corpus_ref'])
            except Corpus.DoesNotExist:
                raise CommandError('Corpus "%s" does not exist. Did you use the -c options?' % options['corpus_ref'])

            print ("Ready to import source '" + str(source['titreUniforme']) 
                   + "' with " + str(source['nb_pieces']) + " pieces in " + corpus.title  + "?")
            
            # Loop on pieces
            curseur = connexion.cursor()
            curseur.execute("select p.*, t.incipit, t.texte, o.intitule as office, f.intitule as fete, m.intitule as mode, "
                            + "d.intitule as solennite, g.intitule as genre" 
                            + " from Piece as p, Texte as t, Office as o, Fete as f, Mode as m, "
                            + "Genre as g, DegreSolennite as d"
                            + " where p.idTexte =t.id and p.idDocument=%s" % options['source_id']
                            + " and p.codeOffice=o.code and p.codeMode=m.code and p.codeFete=f.code"
                            + " and p.codeGenre=g.code and p.degre_solennite=d.code" )
            for piece in curseur.fetchall():
                opus_ref = corpus.ref + settings.NEUMA_ID_SEPARATOR + str(piece['idPiece'])
                try:
                    opus = Opus.objects.get(ref=opus_ref)
                except Opus.DoesNotExist as e:
                    print ("Opus %s does not exists : creation " % opus_ref) 
                    opus = Opus()
                    
                opus.corpus = corpus
                opus.ref = opus_ref
                opus.title = piece['incipit'] 
                opus.save()
                
                # add fields as meta pairs 
                opus.add_meta (OpusMeta.MK_OFFICE, piece["office"])
                opus.add_meta (OpusMeta.MK_MODE, piece["mode"])
                opus.add_meta (OpusMeta.MK_FETE, piece["fete"])
                opus.add_meta (OpusMeta.MK_GENRE, piece["genre"])
                opus.add_meta (OpusMeta.MK_SOLENNITE, piece["solennite"])
                opus.add_meta (OpusMeta.MK_TEXTE, piece["texte"])
                
                # Try to get the MusicXML
                mxml_name = self.MXML_PATH + "musicxml-" +  str(piece['idPiece']) + ".xml"
                try:
                    mxml_file = open(mxml_name)
                    print("Importing the MusicXML file for this piece.")
                except IOError:
                    print("No MusicXML file for this piece. I take the default 'missing score' doc")
                    mxml_name = settings.BASE_DIR + '/static/missing_score.xml'
                    mxml_file = open(mxml_name)

                xml_content = mxml_file.read()
                xml_content = xml_content.replace("MusicXML Part","")
                xml_content = xml_content.replace("<staff-lines>4","<staff-lines>5")
                xml_content = xml_content.replace("<line>5</line>","<line>4</line>")

                
                opus.musicxml.save("score.xml", ContentFile(xml_content))
                Workflow.produce_opus_mei(opus, True) # With replacement    
                    
                opus.save()

        else:
            print ("Unknown action " + str(options['action']) + " can be sources, import. Did you use -a ? ")

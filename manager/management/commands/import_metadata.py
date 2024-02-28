from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from manager.models import Opus, OpusMeta

import os 
import json 


class Command(BaseCommand):
	"""Import metadata from a JSON file"""

	help = 'Import a JSON file with opus metadata'

	def add_arguments(self, parser):
		parser.add_argument('-f', dest='file_path')

	def handle(self, *args, **options):
			
		if 'file_path' not in options:
			print ("You must provide the file path")
			exit(1)
		
		if not os.path.exists(options['file_path']):
			print (f"File {file_path} does not exist")
			exit(1)
			
		with  open(options['file_path']) as f: 
			metadata = json.load(f)
			pieces = metadata["pieces"]
			for piece_id in  pieces.keys():
				piece_meta = pieces[piece_id]["opus"]
				opus_ref = piece_id.replace("-", ":").replace("saintsaens:ref", "saintsaens-ref")
			
				try:
					opus = Opus.objects.get(ref=opus_ref)
					print (f"Assign metedata for opus {opus_ref}, {piece_meta['title']}")
					
					if "genre" in piece_meta.keys():
						opus.add_meta (OpusMeta.MK_GENRE, piece_meta["genre"])
					if "meter" in piece_meta.keys():
						opus.add_meta (OpusMeta.MK_METER, piece_meta["meter"])
					if "year" in piece_meta.keys():
						opus.add_meta (OpusMeta.MK_YEAR, piece_meta["year"])
					if "key" in piece_meta.keys():
						opus.add_meta (OpusMeta.MK_KEY_TONIC, piece_meta["key"])
					if "collection" in piece_meta.keys():
						opus.add_meta (OpusMeta.MK_COLLECTION, piece_meta["collection"])

					if "contributors" in piece_meta.keys():
						contribs = piece_meta["contributors"]
						if "lyricist" in contribs.keys():
							opus.add_meta (OpusMeta.MK_LYRICIST, contribs["lyricist"])
											
					opus.save()
				except Opus.DoesNotExist:
					print (f"Warning: opus {opus_ref} does not exist. Metadata ignored")

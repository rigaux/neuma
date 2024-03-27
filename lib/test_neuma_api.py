
import sys, os
import argparse
import json
from pathlib import Path

from neuma_client.client import NeumaClient

from neuma_client.proxies import Collections, Corpus, Opus, Source, Manifest

def main(argv=None):
	"""
	 Test of Neuma API client
	"""

	# On accepte des arguments
	parser = argparse.ArgumentParser(description='Neuma API tests')
	parser.add_argument('-b', '--base_url', dest='base_url',
                   help='URL of Neuma services', default="http://neuma.huma-num.fr")
	args = parser.parse_args()
	
	print (f"Base URL for Neuma services : {args.base_url}")
	
	client = NeumaClient (None, auth_scheme="Token", base_url=args.base_url)
	
	# Test the welcome message
	res = client.request ("NeumaApi_v3")
	print (f"Welcome service -- {res['message']}")
		
	res = client.request ("Element", full_neuma_ref= "all:collabscore:saintsaens-ref")
	print (f"Recherche d'un corpus -- {res['title']}\n")

	"""
	    Test with proxies
	"""
	corpus_ref = "all:collabscore:saintsaens-ref"
	print ("\n\n")
	print ("\t\t Test of proxies\n")
	neuma_coll = Collections (client)
	corpus = neuma_coll.get_corpus (corpus_ref)
	print (f"Got corpus {corpus.ref}")
	opuses = corpus.get_opus_list()
	for op in opuses:
		print (f"\tOpus {op.ref} with title {op.title}")
		iiif = op.get_source(Source.IIIF_REF)
		if iiif is None:
			print (f"Unable to find source IIIF for opus {op.ref}")
		elif iiif.has_manifest:
			manifest = iiif.get_manifest()
			print (f"\t\tSource IIIF : {iiif.ref}. Nb pages: {manifest.nb_pages()}")
			for i in range (manifest.nb_pages()):
				page = manifest.get_page(i)
				print (f"\t\t\tPage {i+1}. URL: {page['url']} ({page['width']}) Nb systems: {manifest.nb_systems(i)}")
				for j in range (manifest.nb_systems(i)):
					system = manifest.get_system(i,j)
					print (f"\t\t\t\tSystem {j+1} : Nb staves: {manifest.nb_staves(i,j)}")
					print (f"\t\t\t\tSystem {j+1} : Region: {manifest.system_region(i,j)}")
					print (f"\t\t\t\tSystem {j+1} : Nb measures: {manifest.nb_measures(i,j)}")
					for k in range (manifest.nb_measures(i, j)):
						measure = manifest.get_measure(i, j, k)
						print (f"\t\t\t\t\tMeasure {measure['number_in_system']}. Region {measure['region']}")
						
		#break
	
if __name__ == "__main__":
	main()
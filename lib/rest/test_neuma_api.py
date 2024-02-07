
import sys, os
import argparse
import json
from pathlib import Path

from client import NeumaClient

from proxies import Collections, Corpus, Opus, Source

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
	res = client.request ("Welcome")
	print (f"Welcome service -- {res['message']}")
		
	res = client.request ("Element", full_neuma_ref= "all:collabscore:saintsaens-ref")
	print (f"Recherche d'un corpus -- {res['title']}\n")

	"""
	    Test with proxies
	"""
	print ("\n\n")
	print ("\t\t Test of proxies\n")
	neuma_coll = Collections (client)
	corpus = neuma_coll.get_corpus ("all:collabscore:saintsaens-ref")
	print (f"Got corpus {corpus.ref}")
	opuses = corpus.get_opus_list()
	for op in opuses:
		print (f"\tOpus {op.title}")
		iiif = op.get_source(Source.IIIF_REF)
		if iiif.has_manifest:
			print (f"\t\tSource IIIF : {iiif}. Nb pages: {iiif.nb_pages()}")
			for i in range (iiif.nb_pages()):
				page = iiif.get_page(i)
				print (f"\t\t\tPage {i+1}. URL: {page['url']} ({page['width']}) Nb systems: {iiif.nb_systems(i)}")
				for j in range (iiif.nb_systems(i)):
					print (f"\t\t\t\tSystem {j+1} : Nb staves: {iiif.nb_staves(i,j)}")
					print (f"\t\t\t\tSystem {j+1} : Region: {iiif.system_region(i,j)}")
				
		break
	
if __name__ == "__main__":
	main()
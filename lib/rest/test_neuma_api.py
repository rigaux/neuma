
import sys, os
import argparse
import json
from pathlib import Path

from client import NeumaClient

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
	
	
	print (f"TopLevelCorpuses")
	res = client.request ("TopLevelCorpusList")
	for cor in res['results']:
		print (f"Corpus {cor['title']}")
	print ("\n")
	
	res = client.request ("Element", full_neuma_ref= "all:collabscore:saintsaens-ref")
	print (f"Recherche d'un corpus -- {res['title']}\n")

	print (f"Liste d'opus")
	res = client.request ("OpusList", full_neuma_ref= "all:collabscore:saintsaens-ref")
	for op in res['results']:
		print (f"\tOpus {op['title']}")

if __name__ == "__main__":
	main()
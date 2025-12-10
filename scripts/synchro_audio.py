
import time
import sys, os
import socket
import argparse
from pathlib import Path

import jsonschema
import jsonref
import json
from jsonref import JsonRef

from datetime import datetime

sys.path.append("..")
import lib.music.source as source_mod


# List of actions

SHOW_MANIFEST = "show"
SPLIT_TIMEFRAME = "split"
MERGE_TIMEFRAMES = "merge"
CONVERT_FROM_AUDACITY = "cnv_audacity"
MEASURE_NUMBERING = "meas_numbering"
#
# Example: 
#   python3 synchro_audio.py -i data/EtqPelleasa2s1.txt -a cnv_audacity -o pelleas.json
#   python3 synchro_audio.py -i pelleas.json  -a split -r m14 -n m14bis 

def main(argv=None):
	""" 
	Utilities to manipulate the content of internal audio manifests
	"""

	# On accepte des arguments
	parser = argparse.ArgumentParser(description='Audio Manifest utilities')
	parser.add_argument('-a', '--action', dest='action', help='')
	parser.add_argument('-r', '--object_ref', dest='object_ref', help='')
	parser.add_argument('-n', '--new_ref', dest='new_ref', help='')
	parser.add_argument('-i', '--infile', dest='input_file',
                   help='Path to the current audio manifest')
	parser.add_argument('-o', '--outfile', dest='output_file', 
                   help='Path to the new manifest')
	args = parser.parse_args()
	
	if args.action is None:
		action = SHOW_MANIFEST
	else:
		action  = args.action
		
	if args.input_file is None:
		sys.exit ("You must provide an input file name with -i ")

	if action == SHOW_MANIFEST:
		print (f"Action: show the content of an audio manifest")
		with open(args.input_file) as manifest_file:
			synchro_data = json.load (manifest_file)
			audio_mnf = source_mod.AudioManifest.from_json(synchro_data)
		audio_mnf.show()
	elif action == SPLIT_TIMEFRAME:
		if args.object_ref is None:
			sys.exit ("Split action. You must provide an object ref")
		if args.new_ref is None:
			sys.exit ("Split action. You must provide the new ref")
		if args.output_file is None:
			sys.exit ("Split action. You must provide the output file name")
		with open(args.input_file) as manifest_file:
			synchro_data = json.load (manifest_file)
			audio_mnf = source_mod.AudioManifest.from_json(synchro_data)
		print (f"Action: split time frame for object {args.object_ref}")
		audio_mnf.split_tframe (args.object_ref, args.new_ref)
		output = open(args.output_file, 'w', encoding='utf-8')
		json.dump (audio_mnf.to_json(), output, indent=4)
		print (f"Manifest after split of {args.object_ref} has been written in {args.output_file}")
	elif action == MERGE_TIMEFRAMES:
		if args.object_ref is None:
			sys.exit ("Merge action. You must provide an object ref")
		if args.output_file is None:
			sys.exit ("Merge action. You must provide the output file name")
		with open(args.input_file) as manifest_file:
			audio_mnf = source_mod.AudioManifest.from_json(json.load (manifest_file))
		print (f"Action: merge time frames from object {args.object_ref}")
		audio_mnf.merge_tframes (args.object_ref)
		output = open(args.output_file, 'w', encoding='utf-8')
		json.dump (audio_mnf.to_dict(), output, indent=4)
		print (f"Manifest after merge of {args.object_ref} has been written in {args.output_file}")
	elif action == CONVERT_FROM_AUDACITY:
		if args.output_file is None:
			sys.exit ("Convert action. You must provide the output file name")
		audio_mnf = source_mod.AudioManifest ("","")
		audio_mnf.load_from_audacity (args.input_file)
		output = open(args.output_file, 'w', encoding='utf-8')
		json.dump (audio_mnf.to_dict(), output, indent=4)
		print (f"Manifest has been loaded from {args.input_file} and written to {args.output_file}")
	if action == MEASURE_NUMBERING:
		print (f"Action: assign a measure number to the old audi manifest format")
		with open(args.input_file) as manifest_file:
			synchro_data = json.load (manifest_file)
			audio_mnf = source_mod.AudioManifest.from_json(synchro_data)
			audio_mnf.measure_numbering()
			output = open(args.output_file, 'w', encoding='utf-8')
			json.dump (audio_mnf.to_dict(), output, indent=4)
	else:
		sys.exit (f"Unknown action {action}")
		
if __name__ == "__main__":
	main()
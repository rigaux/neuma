
import time
import sys, os

import argparse
from pathlib import Path
import shutil
from datetime import datetime


# Example: 
#   python3 synchro_audio.py -i data/EtqPelleasa2s1.txt -a cnv_audacity -o pelleas.json
#   python3 synchro_audio.py -i pelleas.json  -a split -r m14 -n m14bis 

def main(argv=None):
	""" 
	Utilities to manipulate the content of internal audio manifests
	"""

	# On accepte des arguments
	parser = argparse.ArgumentParser(description='Rename image files')
	parser.add_argument('-d', '--dir', dest='dir', help='')
	args = parser.parse_args()
			
	if args.dir is None:
		sys.exit ("You must provide the image dir with -d ")

	i_file = 1
	for fname in sorted(os.listdir(args.dir)):
		entry = Path(fname)
		if  entry.suffix == ".jpg":
			print(f"Found image'{entry.name}' with extension {entry.suffix}")
			new_name = args.dir + f"/pm{i_file}.jpg"
			i_file += 1
			print(f"Copy {fname} in {new_name}")
			shutil.copy (args.dir + "/" + fname, new_name)
		
if __name__ == "__main__":
	main()
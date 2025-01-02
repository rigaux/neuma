
import time
import sys, os
import socket
import argparse
from pathlib import Path

import jsonschema
import jsonref
import json
from jsonref import JsonRef

from iiif_prezi.factory import ManifestFactory

sys.path.append("..")
from lib.collabscore.parser import CollabScoreParser, OmrScore

import lib.music.source as source_mod

def main(argv=None):
	""" 
	IIIF manifests
	"""

	current_path = os.path.dirname(os.path.abspath(__file__))
	out_dir = os.path.join(current_path, 'out')

	# On accepte des arguments
	parser = argparse.ArgumentParser(description='IIIF Manifest creation')
	parser.add_argument('-i', '--indir', dest='input_dir',
                   help='Path to the list of images (in alphanumeric order)')
	parser.add_argument('-u', '--url', dest='url_prefix', 
                   help='URL of the IIIF server')
	parser.add_argument('-p', '--path', dest='path_to_images', 
                   help='Path to the directory of images')
	parser.add_argument('-o', '--outdir', dest='output_dir', 
                   help='Output directory for the manifest.json file')
	args = parser.parse_args()
	
	if args.output_dir is None:
		output_dir = "/tmp"
	else:
		output_dir = args.output_dir
		
	if args.path_to_images is None:
		path_to_images = ""
	else:
		path_to_images = args.path_to_images

	if args.input_dir is None:
		sys.exit ("Please supply the path to the images directory.")
	if args.url_prefix is None:
		sys.exit ("Please supply a IIIF server URL.")
	if args.output_dir is None:
		sys.exit ("Please supply an output directory.")
	if not os.path.exists(args.input_dir):
		sys.exit ("Directory " + args.images_dir + "  does not exist. Please check.")
	if not os.path.exists(args.output_dir):
		sys.exit ("Directory " + args.output_dir + "  does not exist. Please check.")

	print (f"Processing images from {args.input_dir}")	
	jpegs=[]
	for fname in os.listdir(args.input_dir):
		basename = os.path.basename(fname)
		components = os.path.splitext(basename) 
		extension = components[len(components)-1]
		if extension == ".jpg":
			jpegs.append(fname)
	jpegs.sort()
	
	fac = ManifestFactory()
	# Where the resources live on the web
	fac.set_base_prezi_uri(args.url_prefix)
	# Where the resources live on disk
	fac.set_base_prezi_dir(args.input_dir)

	# Default Image API information
	fac.set_base_image_uri(args.url_prefix)
	fac.set_iiif_image_info(2.0, 2) # Version, ComplianceLevel

	# 'warn' will print warnings, default level
	# 'error' will turn off warnings
	# 'error_on_warning' will make warnings into errors
	fac.set_debug("warn") 
	
	manifest = fac.manifest(ident="identifier/manifest", label="Example Manifest")
	manifest.set_metadata({"Date": "Some Date", "Location": "Some Location"})
	manifest.description = "This is a longer description of the manifest"
	manifest.viewingDirection = "left-to-right"
	i_jpg = 0
	seq = manifest.sequence()  # unlabeled, anonymous sequence

	for jpg_name in jpegs:
		i_jpg += 1
		print (f"File {jpg_name}")
	
		# Create a canvas with uri slug of page-1, and label of Page 1
		cvs = seq.canvas(ident="page-%s" % i_jpg, label="Page %s" % i_jpg)
		# Create an annotation on the Canvas
		anno = cvs.annotation()

		# Add Image: http://www.example.org/path/to/image/api/p1/full/full/0/native.jpg
		img = anno.image(path_to_images + "%2F" + jpg_name, iiif=True)

		# Set image height and width, and canvas to same dimensions
		imagefile = os.path.join(args.input_dir, jpg_name)
		img.set_hw_from_file(imagefile) 
		
		# OR if you have a IIIF service:
		# img.set_hw_from_iiif()
		cvs.height = img.height
		cvs.width = img.width

		
	data = manifest.toString(compact=False)
	output_file= os.path.join(args.output_dir, 'manifest.json')
	fh = open(output_file, "w")
	fh.write(data)
	fh.close()
	print(f"Manifest has been written to {output_file}")
if __name__ == "__main__":
	main()
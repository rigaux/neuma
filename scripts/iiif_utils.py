
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

from iiif_prezi.factory import ManifestFactory
from iiif_prezi.loader import ManifestReader

sys.path.append("..")
from lib.collabscore.parser import CollabScoreParser, OmrScore

import lib.iiif.IIIFProxy as iiif_proxy

import lib.music.source as source_mod


# List of actions

CREATE_MANIFEST = "create_manifest"
TEST_API = "test_api"

#
# Example: python3 iiif_utils.py -i ~/tmpdir/damoiselle/ -u https://deptfod.cnam.fr/ImageS/iiif/2 -p damoiselle -o . 
#

def main(argv=None):
	""" 
	IIIF manifests
	"""

	# On accepte des arguments
	parser = argparse.ArgumentParser(description='IIIF Manifest creation')
	parser.add_argument('-a', '--action', dest='action', help='')
	parser.add_argument('-i', '--indir', dest='input_dir',
                   help='Path to the list of images (in alphanumeric order)')
	parser.add_argument('-u', '--url', dest='url_prefix', 
                   help='URL of the IIIF server')
	parser.add_argument('-p', '--path', dest='path_to_images', 
                   help='Path to the directory of images')
	parser.add_argument('-o', '--outdir', dest='output_dir', 
                   help='Output directory for the manifest.json file')
	args = parser.parse_args()
	
	if args.action is None:
		action = CREATE_MANIFEST
	else:
		action  = args.action
	if args.output_dir is None:
		output_dir = "/tmp"
	else:
		output_dir = args.output_dir
	
	if args.path_to_images is None:
		path_to_images = ""
	else:
		path_to_images = args.path_to_images

	if action == CREATE_MANIFEST:
		print (f"Action: generate a manifest from a list of images")
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

		now = datetime.now()
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
	
		manifest = fac.manifest(ident=args.url_prefix + "/" + path_to_images + "/manifest.json", label="Manifest")
		manifest.set_metadata({"Date": now.strftime("%m/%d/%Y"), "Creator": "Neuma"})
		manifest.description = ""
		manifest.viewingDirection = "left-to-right"
		i_jpg = 0
		seq = manifest.sequence()  # unlabeled, anonymous sequence

		for jpg_name in jpegs:
			i_jpg += 1
			print (f"File {jpg_name}")
			image_path = path_to_images + "%2F" + jpg_name
	
			# Create a canvas with uri slug of page-1, and label of Page 1
			cvs = seq.canvas(ident=f"{image_path}/info.json", label="Page %s" % i_jpg)
			# Create an annotation on the Canvas
			anno = cvs.annotation()

			# Add Image: http://www.example.org/path/to/image/api/p1/full/full/0/native.jpg
			img = anno.image(image_path, iiif=True)

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
	else:
		#print ("TESTING THE IIIF API")
		
		#source_url = f"https://neuma.huma-num.fr/home/opus/all:collabscore:saintsaens-audio:asciano"
		source_url = "http://test.fr/asciano"
		image_url = "https://gallica.bnf.fr/iiif/ark:/12148/bpt6k11620688/f2/full/full/0/native.jpg"
		audio_url =  "https://openapi.bnf.fr/iiif/audio/v3/ark:/12148/bpt6k88448791/3.audio"
		duration = 257
		height = 6174
		width = 4564
		manifest = iiif_proxy.Manifest(source_url, "Asciano")
		
		# One single canvas 
		canvas = iiif_proxy.Canvas (source_url+"/canvas", "Combined image-audio canvas")

		# We create the content list
		content_list_id = source_url+"/list-media"
		content_list = iiif_proxy.AnnotationList(content_list_id,"List of source media")
		# The annotation  list contains the audio and all the pages
		content_list.add_audio_item (f"{source_url}/audio", canvas, audio_url, "audio/mp3", duration)
		content_list.add_image_item (f"{source_url}/image", canvas, image_url, "application/jpg", height, width)
		canvas.add_content_list (content_list)

		# Next we add annotations to link 
		synchro_list = iiif_proxy.AnnotationList(source_url+"/synchro","Synchronisation list")

		polygon = "1221,1589 2151,1589 1221,2266 2161,2266"
		time_frame = "0,4.852608"
		synchro_list.add_synchro(canvas, source_url + "/m1", content_list_id, polygon, time_frame)

		polygon = "2151,1589 2766,1589 2161,2266 2775,2266"
		time_frame = "4.852608,8.707483"
		synchro_list.add_synchro(canvas, source_url + "/m2", content_list_id, polygon, time_frame)

		#canvas.add_annotation_list (synchro_list)

		manifest.add_canvas (canvas)
		print (manifest.json (2))
		
		
if __name__ == "__main__":
	main()
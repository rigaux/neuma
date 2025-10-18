
import time
import sys, os
import socket
import argparse
from pathlib import Path

#
# Classes that encapsulate the IIIF Prezi3 implementation
#   Github: https://github.com/iiif-prezi/iiif-prezi3
#   Documentation: https://iiif-prezi.github.io/iiif-prezi3/
#
import iiif_prezi3


class IIIF3Manifest ():

	'''
		Acts as a proxy for the Prezi3 manifest class
	'''
	
	def __init__(self, id, label) :
		self.prezi_manifest = iiif_prezi3.Manifest(id=id, label={"en":[label]})
		self.prezi_manifest.items = []
	
	def json(self, indent=2):
		return self.prezi_manifest.json(indent)
	
	def add_canvas (self, canvas):
		self.prezi_manifest.items.append (canvas.prezi_canvas)

class Canvas ():
	
	def __init__(self, id, label) :
		self.prezi_canvas = iiif_prezi3.Canvas (id=id, label=label)

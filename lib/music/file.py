import json
import csv

# for XML editions
from lxml import etree

'''
 Classes that manipulate the content of music files
'''


class MEI:
	'''
		
	'''

	def __init__(self, file_path=None):
		self.file_path = file_path
	
		# Try to parse the MEI file
		self.mei_root = etree.parse(file_path)

		# Record the list of namespaces
		self.prefix_map = {"mei": "http://www.music-encoding.org/ns/mei",
						"xml": "http://www.w3.org/XML/1998/namespace"}			
						
	
	def set_measures_id(self):
		"""
		 Injest measure IDs in the file
		"""
		measures = self.mei_root.findall(".//mei:measure", self.prefix_map)
		for measure in measures:
			#print (f"Found measure {measure.get('n')}")
			tag = etree.QName('http://www.w3.org/XML/1998/namespace', 'id')
			measure.set(tag, "m" + measure.get('n'))
		return 

	def write(self, file_path=None):
		if file_path==None:
			# We rewrite the same file
			file_path = self.file_path
		self.mei_root.write (file_path)

	def to_dict (self):
		source_dict =  {
			"id": self.id,
			"ref": self.ref, 
			"description": self.description,
			"source_type": self.source_type, 
			"mime_type": self.mime_type, 
			"url": self.url,
			"metadata": self.metadata,
			"copyright": self.copyright,
			"organization": self.organization,
			"licence":  self.licence,
			"thumbnail":  self.thumbnail,
			"file_path": self.file_path,
			"has_manifest": self.has_manifest,
			"has_iiif_manifest": self.has_iiif_manifest,
			}
		
		if self.ref == self.IIIF_REF and len(self.images) > 0:
			source_dict["images"] = []
			for img in self.images:
				source_dict["images"].append(img.to_dict())
		return source_dict

	@staticmethod
	def from_dict (source_dict):
				
		return ItemSource (source_dict["id"], 
					source_dict["ref"], 
					source_dict["source_type"], 
					source_dict["mime_type"], 
					source_dict["url"], 
					source_dict["metadata"], 
					source_dict["licence"], 
					source_dict["copyright"], 
					source_dict["thumbnail"], 
					source_dict["organization"], 
					source_dict["description"],
					ItemSource.FROM_DICT
					)

	def json(self):
		return json.dumps(self.to_dict())
		
'''
  Classes describing sources of abstract scores: images, audio, etc.
  
  Used mostly to map the structure of a score with components of the source
  via the concept of "Manifest" inspired by IIIF 
'''

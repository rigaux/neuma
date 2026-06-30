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

	def set_pages_id(self):
		"""
		 Number pages
		"""
		pages = self.mei_root.findall(".//mei:pb", self.prefix_map)
		page_no = 1
		for page in pages:
			page_id = f"p{page_no}"
			#print (f"Found page {page_no}")
			tag = etree.QName('http://www.w3.org/XML/1998/namespace', 'id')
			page.set(tag, page_id)
			# Get systems
			system_no = 2 
			# Start at 2 because a pb implies a first system which remains implicit
			systems = page.xpath("following-sibling::mei:sb",
						namespaces={'mei': "http://www.music-encoding.org/ns/mei"})
			for system in systems:
				system_id = f"{page_id}-s{system_no}"
				#print (f"Yes, system {system_id}")
				tag = etree.QName('http://www.w3.org/XML/1998/namespace', 'id')
				system.set(tag, system_id)
				system_no += 1
			page_no += 1
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

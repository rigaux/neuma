
import time
import sys, os
import socket
import argparse
from pathlib import Path

import lib.iiif.IIIF3 as iiif3_mod

"""
	Utility functions that create ad-hoc manifests	
"""

def create_collection (coll):
	"""
	  We receive a Neuma Collection (lib/music/collection.py)
	  from which we produce a manifest
	"""
	title_prop = iiif3_mod.Property (coll.short_title)
	collection = iiif3_mod.Collection(coll.url, title_prop)
	
	add_descriptive_properties(collection, coll.description, 
				coll.thumbnail, coll.licence, 
				coll.copyright, coll.organization)
					
		
	# Add metadata
	title_meta =  iiif3_mod.Metadata (iiif3_mod.Property("title"), 
								iiif3_mod.Property(coll.title))
	collection.add_metadata (title_meta)

	return collection
	

def create_combined_manifest (item, sync_source, audio_source, 
						image_source, images,
						sorted_images, sorted_audio):
	"""
	  Create a combined manifest from an audio + a video source
	"""
	#title_prop = iiif3_mod.Property (item.title)
	#collection = iiif3_mod.Collection(item., title_prop)
	
	if "duration" in audio_source.metadata:
		duration = audio_source.metadata["duration"]
	else:
		print (f"Create_combined_manifest WARNING: no duration in metadata. Assuling a default value...")
		duration = 180

	# Create the combined manifest
	if item.subtitle is not None or item.subtitle != "":
		list_labels =  iiif3_mod.Property ([item.title, item.subtitle])
	else:
		list_labels = iiif3_mod.Property (item.title) 

	manifest = iiif3_mod.Manifest(item.url, list_labels)
	# Add a description/summary
	add_descriptive_properties(manifest, sync_source.description, 
				sync_source.thumbnail, sync_source.licence, 
				sync_source.copyright, sync_source.organization)
					
	# Add metadata
	title_meta =  iiif3_mod.Metadata (iiif3_mod.Property("title"), 
									iiif3_mod.Property(item.title))
	manifest.add_metadata (title_meta)
	if item.composer is not None:
		composer_meta =  iiif3_mod.Metadata (iiif3_mod.Property("creator"), 
								iiif3_mod.Property(item.composer["name_and_dates"]))
		manifest.add_metadata (composer_meta)

	# One single canvas 
	canvas_label = iiif3_mod.Property ("Combined image-audio canvas")

	canvas = iiif3_mod.Canvas (item.url+"/canvas", canvas_label)

	# The height and width of the canvas are those of the first image.
	# Unclear, should be clarified
	for img in images:
		canvas.prezi_canvas.height = img.height
		canvas.prezi_canvas.width = img.width
		break
			
	# We create the content list
	content_list_id = item.url+"/list-media"
	content_list = iiif3_mod.AnnotationList(content_list_id)
		
	# The audio file is in the URL of the source. At some point
	# it will be more consistent to use this URL to point to
	# the audio manifest, and the file URL will have to be extracted
	if audio_source.source_type == "MP3":
		mpeg_type = iiif3_mod.Annotation.SOUND_TYPE
		mpeg_id = f"{item.url}/audio"
	else:
		mpeg_type = iiif3_mod.Annotation.VIDEO_TYPE
		mpeg_id = f"{item.url}/video"
		
	mpeg_item = content_list.add_audio_item (mpeg_id, mpeg_type, canvas, 
				audio_source.url, audio_source.mime_type, duration)
	add_descriptive_properties(mpeg_item, audio_source.description, 
				audio_source.thumbnail, audio_source.licence, 
				audio_source.copyright, audio_source.organization)
		
	if image_source.description is not None:
		summary_image = iiif3_mod.Property (image_source.description)
	else:
		summary_image = None

	# We need the time duration of each page wrt to the audio. 
	# The source of the body tells us the page Id
		
	# First we create a dict of pages and measures range
	pages_measures = {}
	for measure_ref, annot_image in sorted_images.items():
		no_measure = int(measure_ref.replace ("m",""))
		if  annot_image.body.source not in  pages_measures.keys():
			# print (f"Found a new page {annot_image.body.source}.")
			pages_measures[annot_image.body.source] = {"first_measure" : no_measure,
								"start_at": None, "stop_at": None}
		else:
			pages_measures[annot_image.body.source]["last_measure"] = no_measure

	# Now we scan the audio annotations and aggregate the time ranges
	for measure_ref, audio_annot in sorted_audio.items():
		no_measure = int(measure_ref.replace ("m",""))
		# extract time range
		t_range = audio_annot.body.selector_value.replace("t=","").split(",")
		# 	Find the page of the measure
		for page_id, measure_range  in pages_measures.items():
			if (no_measure >= measure_range["first_measure"] 
			     and no_measure <= measure_range["last_measure"]):
				#print (f"Measure {no_measure} is in page {page_id}")
				if measure_range["start_at"] is None:
					measure_range["start_at"] = t_range[0]
				else:
					measure_range["stop_at"] = t_range[1]
				
	#for page_id, measure_range  in pages_measures.items():
	#	print (f"Page {page_id}. Range {measure_range}")

	# We should know the first page of music
	if "first_page_of_music" in image_source.metadata:
		first_page_of_music = image_source.metadata["first_page_of_music"]
	else:
		first_page_of_music = 1
	if "last_page_of_music" in image_source.metadata:
		last_page_of_music = image_source.metadata["last_page_of_music"]
	else:
		last_page_of_music = 99999

	i_img= 0
	for img in images:
		i_img += 1
		if i_img >= first_page_of_music and i_img <= last_page_of_music :
			if img.url in pages_measures.keys():
				start_at = pages_measures[img.url]['start_at']
				stop_at = pages_measures[img.url]['stop_at']
				t_range = f"t={start_at},{stop_at}"
			else:
				# THIS SHOULD NOT HAPPEN
				raise Exception(f"Unable to find annotations on image {img.url} when creating the sync manifest")
				t_range=""
			target = canvas.id + "#" + t_range
			#print (f"Image {img.native}. URL {img.url} Time range {t_range} Width {img.width} Height {img.height}")
			label_image = iiif3_mod.Property (f"Page {i_img}")
			content_list.add_image_item (f"{item.url}/img{i_img}", target, img.native, "application/jpg", 
						img.height, img.width, label_image, summary_image)
			#if i_img > 2:
			#	break

	canvas.add_content_list (content_list)
	# Next we add annotations to link 
	synchro_list = iiif3_mod.AnnotationList(item.url+"/synchro")
	i_measure = 0
	for measure_ref in list(sorted_images.keys()):
		i_measure += 1
		if measure_ref in sorted_audio:
			annot_image = sorted_images[measure_ref]
			annot_audio = sorted_audio[measure_ref]
			time_frame = annot_audio.body.selector_value
			polygon = annot_image.body.selector_value.replace(")("," ").replace("P","").replace("((","").replace("))","")
			#print (f"Found both annotations for measure {measure_ref}. Region {polygon} Time frame {time_frame}")
			synchro_list.add_synchro(canvas, item.url + "/"+measure_ref, content_list_id, polygon, time_frame)
		#if i_measure > 3:
		#	break

	manifest.add_canvas (canvas)
	return manifest

def add_descriptive_properties(iiif_object, summary, thumbnail,
					licence, copyright, organization):
		# Add a description/summary
	if summary is not None:
		summary_prop = iiif3_mod.Property (summary)
		iiif_object.set_summary (summary_prop)
	if thumbnail is not None:
		thumbnail_prop =  iiif3_mod.ImageBody (thumbnail["url_default"], 
				thumbnail["width"], thumbnail["height"],  thumbnail["url"])
		iiif_object.set_thumbnail (thumbnail_prop)
	if licence is not None:
		iiif_object.set_rights (licence["url"])
	if copyright is not None:
		require_stmt_prop = iiif3_mod.Metadata (iiif3_mod.Property("attribution"), 
								iiif3_mod.Property(copyright))
		iiif_object.set_required_statement (require_stmt_prop)
	if organization is not None:
		label_prop = iiif3_mod.Property (organization["name"])
		if organization["logo"] is not None:
			logo_prop =  iiif3_mod.ImageBody (organization["logo"]["url_default"], 
				organization["logo"]["width"], 
				organization["logo"]["height"],
				organization["logo"]["url"])
		else:
			logo_prop =None
		hp_prop = iiif3_mod.Property (organization["name"])
		homepage_prop =  iiif3_mod.Homepage (
			id=organization["homepage"], label=hp_prop
		)
		provider = iiif3_mod.Provider (
			id=iiif_object.id + "provider", 
			label=label_prop,
			logo=logo_prop,
			homepage=homepage_prop)
		iiif_object.set_provider (provider)

def create_image_item(neuma_image):
	return iiif3_mod.ImageBody (neuma_image["url_default"], 
				neuma_image["width"], 
				neuma_image["height"],
				neuma_image["url"])
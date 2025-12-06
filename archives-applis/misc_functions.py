	def create_sync_source(self, iiif_source, audio_source):
		print (f"Create synchronization source for opus {self.ref} between source {iiif_source.ref} and source {audio_source.ref}")
		base_url =settings.NEUMA_BASE_URL
		opus_url = base_url + self.ref
		
		#image_url = "https://gallica.bnf.fr/iiif/ark:/12148/bpt6k11620688/f2/full/full/0/native.jpg"
		#audio_url =  "https://openapi.bnf.fr/iiif/audio/v3/ark:/12148/bpt6k88448791/3.audio"

		if "duration" in audio_source.metadata:
			duration = audio_source.metadata["duration"]
		else:
			print (f"Create_combined_manifest WARNING: no duration in metadata. Assuling a default value...")
			duration = 180
			
		print (f"Take the image manifest from the source")	
		with open(iiif_source.iiif_manifest.path, "r") as f:
			iiif_doc = iiif2_mod.Document(json.load(f))

		# Create the combined manifest
		title_prop = iiif3_mod.Property (self.title)
		manifest = iiif3_mod.Manifest(opus_url, title_prop)
		# Add a description/summary
		if self.description is not None:
			summary_prop = iiif3_mod.Property (self.description)
			manifest.set_summary (summary_prop)
		# Add metadata
		title_meta =  iiif3_mod.Metadata (iiif3_mod.Property("title"), 
										iiif3_mod.Property(self.title))
		manifest.add_metadata (title_meta)
		if self.get_composer() is not None:
			composer_meta =  iiif3_mod.Metadata (iiif3_mod.Property("creator"), 
										iiif3_mod.Property(self.get_composer().name_and_dates()))
			manifest.add_metadata (composer_meta)
			
		# One single canvas 
		canvas = iiif3_mod.Canvas (opus_url+"/canvas", "Combined image-audio canvas")

		# The height and width of the canvas are those of the first image.
		# Unclear, should be clarified
		images = iiif_doc.get_images()
		for img in images:
			canvas.prezi_canvas.height = img.height
			canvas.prezi_canvas.width = img.width
			break
			
		# We create the content list
		content_list_id = opus_url+"/list-media"
		content_list = iiif3_mod.AnnotationList(content_list_id)
		
		# The audio file is in the URL of the source. At some point
		# it will be more consistent to use this URL to point to
		# the audio manifest, and the file URL will have to be extracted
		label_audio = iiif3_mod.Property ("Source audio/vidéo")
		if audio_source.description is not None:
			summary_audio = iiif3_mod.Property (audio_source.description)
		else:
			summary_source = None
		
		if audio_source.source_type == "MP3":
			mpeg_type = iiif3_mod.Annotation.SOUND_TYPE
			mpeg_id = f"{opus_url}/audio"
		else:
			mpeg_type = iiif3_mod.Annotation.VIDEO_TYPE
			mpeg_id = f"{opus_url}/video"
		
		content_list.add_audio_item (mpeg_id, mpeg_type, canvas, 
				audio_source.url, audio_source.source_type.mime_type, duration)
			
		if iiif_source.description is not None:
			summary_image = iiif3_mod.Property (iiif_source.description)
		else:
			summary_image = None

		# Get the images URLs from the IIIF image manifest
		if not (iiif_source.iiif_manifest) or iiif_source.iiif_manifest == {}:
			raise Exception (f"Missing manifest in the IIIF image source for opus {self.ref}. Synchronization aborted")
			return

		# Get annotations both are dictionary indexed by the measure id
		annotations_images = Annotation.for_opus_and_concept(self,
					IREGION_MEASURE_CONCEPT)
		annotations_audio = Annotation.for_opus_and_concept(self,
					TFRAME_MEASURE_CONCEPT)
		sorted_images = dict(natsorted(annotations_images.items())) 
		sorted_audio = dict(natsorted(annotations_audio.items())) 

		# We need the time duration of each page wrt to the audio. The source
		# of the body tells us the page Id
		
		# First we create a dict of pages and measures range
		pages_measures = {}
#		for measure_ref in list(sorted_audio.keys()):
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
						
		for page_id, measure_range  in pages_measures.items():
			print (f"Page {page_id}. Range {measure_range}")

		# We should now the first page of music
		if "first_page_of_music" in iiif_source.metadata:
			first_page_of_music = iiif_source.metadata["first_page_of_music"]
		else:
			first_page_of_music = 1
		if "last_page_of_music" in iiif_source.metadata:
			last_page_of_music = iiif_source.metadata["last_page_of_music"]
		else:
			last_page_of_music = 99999
		images = iiif_doc.get_images()
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
				print (f"Image {img.native}. URL {img.url} Time range {t_range} Width {img.width} Height {img.height}")
				label_image = iiif3_mod.Property (f"Page {i_img}")
				content_list.add_image_item (f"{opus_url}/img{i_img}", target, img.native, "application/jpg", 
						img.height, img.width, label_image, summary_image)
			#if i_img > 2:
			#	break

		canvas.add_content_list (content_list)

		# Next we add annotations to link 
		synchro_list = iiif3_mod.AnnotationList(opus_url+"/synchro")

		i_measure = 0
		for measure_ref in list(sorted_images.keys()):
			i_measure += 1
			if measure_ref in annotations_audio:
				annot_image = annotations_images[measure_ref]
				annot_audio = annotations_audio[measure_ref]
				time_frame = annot_audio.body.selector_value
				polygon = annot_image.body.selector_value.replace(")("," ").replace("P","").replace("((","").replace("))","")
				#print (f"Found both annotations for measure {measure_ref}. Region {polygon} Time frame {time_frame}")
				synchro_list.add_synchro(canvas, opus_url + "/"+measure_ref, content_list_id, polygon, time_frame)
			#if i_measure > 3:
			#	break

		manifest.add_canvas (canvas)
		
		manifest_fname = "/tmp/combined_manifest.json"
		with open(manifest_fname, "w") as manifest_file:
				manifest_file.write(manifest.json (2))
		self.create_source_with_file(source_mod.OpusSource.SYNC_REF, 
								SourceType.STYPE_SYNC, "", 
								manifest_fname, "combined_manifest.json", "rb")

								
								
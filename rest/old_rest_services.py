
#Not used for the time being
def handle_import_request(request, full_neuma_ref, upload_id):

	#Request related to a corpus import file
	

	corpus, object_type = get_object_from_neuma_ref(full_neuma_ref)
	if object_type != CORPUS_RESOURCE:
		return Response(status=status.HTTP_404_NOT_FOUND)

	if request.method == "POST":

		try:
			upload = Upload.objects.get(id=upload_id)
		except Upload.DoesNotExist:
			return JSONResponse({"error": "Unknown import file"})

		list_imported = Workflow.import_zip(upload)
		# task_id = async(workflow_import_zip, upload)

		answer_list = []
		if list_imported == None:
			return JSONResponse(
			{"error": "Empty list to import"})
		for opus in list_imported:
			answer_list.append(opus.to_json(request))
		return JSONResponse(
			{"imported_file": upload.description, "imported_opera": answer_list}
		)


############
###
### Comparison services
###
############


## Save temporary the opus on the NEUMA database and return the reference
# INPUT: the URL of a score (MEI or MusicXML)
# return the reference of the saved opus


def save_external_opus(url_score):
	"""
	Save the score (MusicXML or MEI) linked in the URL to the neuma DB and return the reference
	:param url_score: the URL of the score
	:return: the reference of the score in the DB
	"""
	response = urllib.request.urlopen(url_score)
	data = response.read()
	# The score is stored in the external corpus
	external = Corpus.objects.get(ref=settings.NEUMA_EXTERNAL_CORPUS_REF)
	# The reference of the opus is a hash of the URL
	hash_object = hashlib.sha256(data).hexdigest()
	opus_ref = (
		settings.NEUMA_EXTERNAL_CORPUS_REF
		+ settings.NEUMA_ID_SEPARATOR
		+ hash_object[:16]
	)
	doc = minidom.parseString(data)
	root = doc.documentElement

	if root.nodeName == "mei":
		try:
			opus = Opus.objects.get(ref=opus_ref)
		except Opus.DoesNotExist as e:
			opus = Opus()
		opus.corpus = external
		opus.ref = opus_ref  # Temporary
		opus.mei.save("mei1.xml", ContentFile(data))
	else:
		# Hope this is a mMusicXML file
		opus = Opus.createFromMusicXML(external, opus_ref, data)
		# Produce the MEI file
		Workflow.produce_opus_mei(opus)
	opus.external_link = url_score
	opus.save()
	print("Opus created. Ref =" + opus.ref)
	return opus_ref


def compute_midi_distance(request):
	""" Compute the distance and the list of differences between two MIDI 
		The body must be a form-data with the fields: 
			"midi1" a monophonic .mid file with one track
			"midi2" a monophonic .mid file with one track
			"consider_offsets" a boolean string value ("True" or "False") saying if we consider also note offsets or only onsets
		return: the distance value and the list of differences to go from score1 to score2
				or an error 
	"""
	# check if the body is correctly formatted
	try:
		consider_offsets = request.data["consider_offsets"] == "True"
	except Exception as e:
		return JSONResponse(
			{
				"error": "consider_offsets (True or False) must be specified in the body "
			},
			status=status.HTTP_406_NOT_ACCEPTABLE,
		)

	if not "midi1" in request.FILES and "midi2" in request.FILES:
		return JSONResponse(
			{"error": "No midi1 and midi2 present in the request"},
			status=status.HTTP_400_BAD_REQUEST,
		)

	midifile1 = request.FILES["midi1"]
	midifile2 = request.FILES["midi2"]
	tmp_midi1_path = os.path.join(
		settings.TMP_DIR, "tmp_midi1.mid"
	)  # the path of the temporary midi files
	tmp_midi2_path = os.path.join(settings.TMP_DIR, "tmp_midi2.mid")
	if os.path.exists(tmp_midi1_path):  # first delete them if they already exist
		os.remove(tmp_midi1_path)
	if os.path.exists(tmp_midi2_path):  # first delete them if they already exist
		os.remove(tmp_midi2_path)
	default_storage.save(tmp_midi1_path, ContentFile(midifile1.read()))  # save it
	default_storage.save(tmp_midi2_path, ContentFile(midifile2.read()))

	print(tmp_midi1_path)
	midi1 = mido.MidiFile(tmp_midi1_path)
	midi2 = mido.MidiFile(tmp_midi2_path)

	try:
		cost, annotation_list = ComparisonProcessor.midi_comparison(
			midi1, midi2, consider_rests=consider_offsets
		)
		return JSONResponse(
			{"comparison_midi": cost, "annotation_list": annotation_list},
			status=status.HTTP_200_OK,
		)
	except Exception as e:
		print("Unable to retrieve the cost and annotations. Error: " + str(e))
		return JSONResponse(
			{"error": "Unable to retreive the cost and comparison annotations"},
			status=status.HTTP_404_NOT_FOUND,
		)


def compute_score_distance(request):
	""" Compute the distance and the list of differences between two scores 
		The body must be a form-data with the fields: 
			"score1" a score with one voice
			"score2" a score with one voice
	"""
	if not "score1" in request.FILES and "score2" in request.FILES:
		return JSONResponse(
			{"error": "No score1 and score present in the request"},
			status=status.HTTP_400_BAD_REQUEST,
		)

	# save localy the scores from the request
	scorefile1 = request.FILES["score1"]
	scorefile2 = request.FILES["score2"]
	tmp_score1_path = os.path.join(
		settings.TMP_DIR, "tmp_score1.xml"
	)  # the path of the temporary score
	tmp_score2_path = os.path.join(settings.TMP_DIR, "tmp_score2.xml")
	if os.path.exists(tmp_score1_path):  # first delete them if they already exist
		os.remove(tmp_score1_path)
	if os.path.exists(tmp_score2_path):  # first delete them if they already exist
		os.remove(tmp_score2_path)
	default_storage.save(tmp_score1_path, ContentFile(scorefile1.read()))  # save it
	default_storage.save(tmp_score2_path, ContentFile(scorefile2.read()))

	mei_path1 = Workflow.produce_temp_mei(tmp_score1_path, 1)["path_to_temp_mei"]
	mei_path2 = Workflow.produce_temp_mei(tmp_score2_path, 2)["path_to_temp_mei"]

	# now open the mei file with music21
	with open(mei_path1, "r") as f1:
		mei_string1 = f1.read()
	with open(mei_path2, "r") as f2:
		mei_string2 = f2.read()
	conv1 = mei.MeiToM21Converter(mei_string1)
	score1 = conv1.run()
	conv2 = mei.MeiToM21Converter(mei_string2)
	score2 = conv2.run()

	# compute distance score and annotations
	try:
		cost, annotation_list = ComparisonProcessor.score_comparison(score1, score2)
		print(cost)
		print(annotation_list)
		return JSONResponse(
			{
				"scores_distance": cost,
				"annotation_list": annotation_list,
				"score1": mei_string1,
				"score2": mei_string2,
			},
			status=status.HTTP_200_OK,
		)
	except Exception as e:
		print("Unable to retrieve the cost and annotations. Error: " + str(e))
		return JSONResponse(
			{"error": "Unable to retreive the cost and comparison annotations"},
			status=status.HTTP_404_NOT_FOUND,
		)

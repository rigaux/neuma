	// Solution taken from
	// https://docs.djangoproject.com/en/1.7/ref/contrib/csrf/

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
function sameOrigin(url) {
    // test that a given url is a same-origin URL
    // url could be relative or scheme relative or absolute
    var host = document.location.host; // host + port
    var protocol = document.location.protocol;
    var sr_origin = '//' + host;
    var origin = protocol + sr_origin;
    // Allow absolute or scheme relative URLs to same origin
    return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
        (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
        // or any other URL that isn't scheme relative or absolute i.e relative.
        !(/^(\/\/|http:|https:).*/.test(url));
}

/**
 * Call Ajax to retrieve a list of annotations for an opus, a model
 */

function ShowAnnotations(opus_ref, model_code, concept_type, show_annotations) {
	console.log("Call to ShowAnnotations for concept " + concept_type + " show/hide " +  show_annotations)

	// First, clear all annotations
	console.log ("Clear current annotations")
	ClearAnnotationAnchors("_all")
	
	// Check or uncheck the concepts checkboxes for all the input concept
	// descendant
	
	// get all annotations for the input concept and its descendants
	url_rest = '/rest/collections/' + opus_ref.replace(/:/g, "/")  + '/_annotations/' + model_code + "/"
			+ concept_type + "/_all"
	console.log("Call URL for ShowAnnotations " + url_rest)
	$.ajax({
		url : url_rest,
		type : 'GET',
		data : {},
		dataType : 'json',
		success : function(annotations) {
			AddAnnotationAnchors(model_code, opus_ref, annotations,
					show_annotations)
		},
		error : function(request, error) {
			alert("Request: " + JSON.stringify(request));
		}
	});
}

/*
 * Manage a list of concept as a checkbox list that shows/hides the annotations
 */

function ManageCheckboxConceptsList(opus_ref, model_code, 
		      parent_concept_code, container, concepts, show_hide) {
	
	// The list is identified after the parent's code
	concept_list_id = "concepts_list:" + parent_concept_code
	list = document.getElementById(concept_list_id);
	if (list == null) {
		// We need to create it
		var list = document.createElement('ul');
		list.setAttribute ("id", concept_list_id)
		container.appendChild(list);
	}

	for (i in concepts) {
		// The id of the concept item and of the concept checkbox
		concept_checkbox_id = "concept_checkbox:" + concepts[i].code
		concept_item_id = "concept_item:" + concepts[i].code
		item = document.getElementById(concept_item_id);
		if (item == null) {
			var item = document.createElement('li');
			item.setAttribute ("id", concept_item_id)
			// Set its contents:
			var checkbox = document.createElement('input');
			checkbox.setAttribute ("id", concept_checkbox_id)
			checkbox.type = 'checkbox';
			checkbox.checked = true
			checkbox.name = concepts[i].code;
			checkbox.onclick = function() {
				// Trick: the concept code will be lost at execution time, so we
				// store it in the cbox attributes as the 'name'
				ShowModelConcepts(opus_ref, model_code, $(this).attr("name"), 	$(this).is(':checked')) 
				// ShowAnnotations(opus_ref, model_code, ,
				// $(this).is(':checked'))
			}
			item.appendChild(checkbox);

			var textContainer = document.createElement("span");
			textContainer.className = "tooltip"

			// Add the SVG icon for leaf nodes
			if (concepts[i].children.length == 0) {
				var svgContainer = document.createElement("span");
				svgContainer.setAttribute("class", "svg-icon-container");
				var svg = document.createElementNS("http://www.w3.org/2000/svg", 'svg')
				svg.setAttribute("class", "svg-icon");
				svg.setAttribute ("viewBox", "0 0 5 5");
				var path = document.createElementNS("http://www.w3.org/2000/svg", 'path');
				path.setAttribute ("d" , concepts[i].icon);
				path.setAttribute ("id" , "icon-" + concepts[i].name);
				path.setAttribute ("style", "fill:"+ concepts[i].display_options + ";fill-opacity:1;stroke:none;");
				svg.appendChild(path)
				svgContainer.appendChild(svg)
				textContainer.appendChild(svgContainer);
			}

			// Append a text node to the item
			var text = document.createTextNode(" " + concepts[i].name + " " + concepts[i].display_options);
			text = document.createTextNode(" " + concepts[i].name)
			textContainer.appendChild(text);
			textContainer.style.color = concepts[i].display_options

			// Question mark
			var qm = document.createElement("img"); 
			qm.setAttribute("src", "/static/images/question_mark_icon.jpg");
			qm.setAttribute("width", "15");
			qm.setAttribute("height", "15");
			qm.setAttribute("class", "question-mark");
			textContainer.appendChild(qm);

			// Tooltip text
			var tooltipContainer = document.createElement("span");
			tooltipContainer.className = "tooltiptext"
				var tooltip = document.createTextNode(" " + concepts[i].description);
			tooltipContainer.appendChild (tooltip)
			textContainer.appendChild(tooltipContainer);
			item.appendChild(textContainer);

			// Add the concept item to the list:
			list.appendChild(item);
		}
		else
			{
			// Just change the checked status of the checkbox
			concept_checkbox = document.getElementById(concept_checkbox_id);
			concept_checkbox.checked = show_hide
			}
		
		// Recursive call for the children
		ManageCheckboxConceptsList(opus_ref, model_code, concepts[i].code, item,
				concepts[i].children, show_hide)
	}
}

/*
 * Create a tree-like list of options for a select list given as an argument
 */

function ManageConceptsSelectList(select_list, concepts, level) {

	var level_separator =" "
	for (i=0; i< level; i++){
		// level_separator += "&nbsp;&nbsp;"
		level_separator += "--"
	}
	level_separator += " "
		
	for (i in concepts) {
	    var option = document.createElement("option");
	    option.value = concepts[i].code;
	    option.text = level_separator + concepts[i].name + " ";

		if (concepts[i].children.length > 0) {
			option.disabled = true
		}
		
	    select_list.append(option);
		
		// Recursive call for the children
		ManageConceptsSelectList(select_list, concepts[i].children, level+1)
	}
}

/**
 * Call Ajax to retrieve a list of concepts for a given model
 */

function ShowModelConcepts(opus_ref, model_code, concept_code="_all", show_hide=true) {
	// Make sure the initial container is empty
	//console.log ("Clear the container of the concepts list")
	listRef = document.getElementById("concepts_list");
	listRef.innerHTML = ""
	
	// Get the list of annotations for this opus, this model and this concept
	ShowAnnotations(opus_ref, model_code, concept_code, show_hide)

	// Show the list of concepts of the model
	url_rest = '/rest/analysis/_models/' + model_code + '/_concepts/' + concept_code + "/_all/"
	console.log ("ShowModelConcepts. REST call to " + url_rest)
	$.ajax({
		url : url_rest,
		type : 'GET',
		data : {},
		dataType : 'json',
		success : function(data) {
			// Show the concept list as a set of check box
			listRef = document.getElementById("concepts_list");
			if (listRef != null) {
				ManageCheckboxConceptsList(opus_ref, model_code, concept_code, listRef, data, show_hide)
				// $('#list_of_modifications').html(data["list_of_modifications"]);
			}
			
			// Also put the concept list as a select list for manual annotation
			annotation_form = document.getElementById("create_annotation_form");
			if (annotation_form != null) {
				var select_list = $("#create_annotation_concept_list")
				ManageConceptsSelectList(select_list, data, 0)
			}
			
			// Same for the update form
			ManageConceptsSelectList($("#update_annotation_concept_list"), data, 0)
		},
		error : function(request, error) {
			alert("Request: " + JSON.stringify(request));
		}
	});
	
	// Set the current model code (has to be available for the computation of annotations)
	$("#compute_model_code").val (model_code)
	
	// Make the compute form visible (There is no longer such a thing ?!)
	$("#compute_annotation_form").show()
}

/**
 * Call Ajax to insert a new annotation
 */
function InsertAnnotation(form) {
	// var annotation_id = form.querySelector("#annotation_id").value
	var note_id = form.querySelector("#create_annotation_note_id").value
	var opus_ref = form.querySelector("#create_annotation_opus_ref").value
	var comment = form.querySelector("#create_annotation_comment").value
	var e = form.querySelector("#create_annotation_concept_list");
	var selectedConcept = e.options[e.selectedIndex].value;

	// POST are in principle protected by the same origin policy
	// Solution taken from
	// https://docs.djangoproject.com/en/1.7/ref/contrib/csrf/
	var csrftoken = $.cookie('csrftoken');
	console.log ("CSRF cookie: " + csrftoken)
	$.ajaxSetup({
		   beforeSend: function(xhr, settings) {
		        if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
		            // Send the token to same-origin, relative URLs only.
		            // Send the token only if the method warrants CSRF
					// protection
		            // Using the CSRFToken value acquired earlier
		            xhr.setRequestHeader("X-CSRFToken", csrftoken);
		        }
		   }
    });
	
	// Insert a user annotation for this opus and this element (synchronous
	// call)
	url_insert_annot = '/rest/collections/' + opus_ref.replace(/:/g, "/") + '/_annotations/'
	console.log ("Call insert request" + url_insert_annot)
 
	$.ajax({
		url : url_insert_annot,
		type : 'PUT',
		data : {"concept": selectedConcept, "note_id": note_id, "comment": comment},
		dataType : 'json',
		async: false,
		success : function(data) {
			$('#create_annotation_form').fadeOut('fast');
			$('#annotation_create_feedback').fadeIn('fast');
			// cleanFormFields();
		},
		error : function(request, error) {
			alert("Request: " + JSON.stringify(request));
		}
	});
	
	// OK refresh the description
	getNoteDescription(opus_ref, note_id)
	// Refresh the annotations markup
	ShowModelConcepts(opus_ref, $("#compute_model_code").val(), selectedConcept)
}


/**
 * Call Ajax to insert/update a new XML fragment
 */
function InsertXmlFragment(form, xml_string) {

	// var annotation_id = form.querySelector("#annotation_id").value
	var note_id = form.querySelector("#xmlfragment_note_id").value
	var opus_ref = form.querySelector("#xmlfragment_opus_ref").value
	var annotation_id = form.querySelector("#xmlfragment_annotation_id").value
	var mei_url  = $("#mei_url").val()

	// alert ("Fragment with id " + note_id + " in opus " + opus_ref +
		// " has been replaced by " + xml_string)
	// POST are in principle protected by the same origin policy
	$.ajaxSetup({
		   beforeSend: function(xhr, settings) {
		        if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
			            xhr.setRequestHeader("X-CSRFToken", $.cookie('csrftoken'));
		        }
		   }
    });
	
	// Insert a user annotation for this opus and this element (synchronous
	// call)
	url_insert_annot = '/rest/collections/' + opus_ref.replace(/:/g, "/") + '/_annotations/'
	console.log ("Call insert request" + url_insert_annot)
 
	$.ajax({ url : url_insert_annot, type : 'PUT', async: false, 
		data : {"xml_fragment": xml_string, "note_id": note_id}, 
		dataType : 'json', async: false, success : function(data) { },
	  error : function(request, error) { alert("Request: " +
	  JSON.stringify(request)); } 
	});
	

	// Get all XML fragments
	var model_code = "quality" // Temporary
	var concept_type = "composer" // Temporary
	alter = GetAnnotations(opus_ref, model_code, concept_type) 
	showScore(vrvToolkit, mei_url, document.getElementById("verovio"), alter);
	
 	return
}


/**
 * Call Ajax (async) to retrieve a list of annotations
 */
function GetAnnotations(opus_ref, model_code, concept_type) 
{
	url_rest = '/rest/collections/' + opus_ref.replace(/:/g, "/")  + '/_annotations/' + model_code + "/"
	+ concept_type + "/_all"

	console.log("Call URL to get all annot " + url_rest)

	alter = []
	$.ajax({
		url : url_rest,
		type : 'GET',
		data : {},
		async : false,
		dataType : 'json',
		success : function(annotations) {
			for (var note_id in annotations) {
				if( annotations.hasOwnProperty(note_id) ) {
				nb_annotations = annotations[note_id].length
				for (var i = 0; i < nb_annotations; i++) {
					annotation = annotations[note_id][i]
					if (annotation.xml_fragment != "") {
					console.log ( " Found annotation with fragment " + annotation.xml_fragment)
					alter.push({"note_id": note_id, "xml_fragment": annotation.xml_fragment})
				}
				}
				}
			}
		},
		error : function(request, error) {
			alert("Request: " + JSON.stringify(request));
		}
	});
	
 	return alter
}

/**
 * Call Ajax to update an existing annotation
 */
function UpdateAnnotation(form) {
	var note_id = form.querySelector("#update_annotation_note_id").value
	var opus_ref = form.querySelector("#update_annotation_opus_ref").value
	var annotation_id = form.querySelector("#update_annotation_id").value
	var comment = form.querySelector("#update_annotation_comment").value
	var e = form.querySelector("#update_annotation_concept_list");
	var selectedConcept = e.options[e.selectedIndex].value;

	var csrftoken = $.cookie('csrftoken');
	$.ajaxSetup({
		   beforeSend: function(xhr, settings) {
		        if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
		            xhr.setRequestHeader("X-CSRFToken", csrftoken);
		        }
		   }
    });
	
	// Insert a user annotation for this opus and this element (synchronous
	// call)
	url_update_annot = '/rest/collections/' + opus_ref.replace(/:/g, "/") 
	    + '/_annotations/' + annotation_id + '/'
	console.log ("Call update request" + url_update_annot)
 
	$.ajax({
		url : url_update_annot,
		type : 'POST',
		data : {"concept": selectedConcept, "note_id": 0, "comment": comment},
		dataType : 'json',
		async: false,
		success : function(data) {
		},
		error : function(request, error) {
			alert("Request: " + JSON.stringify(request));
		}
	});
	
	// OK refresh the description
	getNoteDescription(opus_ref, note_id)
}

/**
 * Call Ajax to compute the annotations for an Opus and an analytic ;odel
 */

function ComputeAnnotations() {
	var opus_ref = $("#compute_opus_ref").val()
	var model_code = $("#compute_model_code").val()

	// POST are in principle protected by the same origin policy
	// Solution taken from
	// https://docs.djangoproject.com/en/1.7/ref/contrib/csrf/
	var csrftoken = $.cookie('csrftoken');
	console.log ("ComputeAnnotations. CSRF cookie: " + csrftoken)
	$.ajaxSetup({
		   beforeSend: function(xhr, settings) {
		        if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
		            // Send the token to same-origin, relative URLs only.
		            // Send the token only if the method warrants CSRF
					// protection
		            // Using the CSRFToken value acquired earlier
		            xhr.setRequestHeader("X-CSRFToken", csrftoken);
		        }
		   }
    });
	

	// First show that we are doing something
	$('#waiting_gif').html('<img id="loader-img" alt="" src="/static/themes/neumaThemeV2/images/loader.svg" width="100" height="100" align="center" />');
	 
	// Compute annotations for this opus and this model (synchronous call)
	url_cpt_annot = '/rest/collections/' + opus_ref.replace(/:/g, "/")  + "/_annotations/"  + model_code + '/_compute/'
	console.log ("Call " + url_cpt_annot)
	$.ajaxSetup({async: false});
	$.ajax({
		url : url_cpt_annot,
		type : 'POST',
		data : {},
		dataType : 'json',
		success : function(data) {
		},
		error : function(request, error) {
			alert("Request: " + JSON.stringify(request));
		}
	});
	$.ajaxSetup({async: true});
	
	// OK remove the waiting GIF
	$('#waiting_gif').html("");

	// Show the list of annotations for this opus and this model
	ShowAnnotations(opus_ref, model_code, "_all", true)
	
	return true
}

/**
 * Call Ajax to compute Comparison Opus and an analytic model
 */

function ComputeComparison() {
	var opus_ref1 = $("#compute_opus_ref1").val()
	var opus_ref2 = $("#compute_opus_ref2").val()
	var model_code = $("#compute_model_code").val()

	// POST are in principle protected by the same origin policy
	// Solution taken from
	// https://docs.djangoproject.com/en/1.7/ref/contrib/csrf/
	var csrftoken = $.cookie('csrftoken');
	console.log ("ComputeComparison. CSRF cookie: " + csrftoken)
	$.ajaxSetup({
		   beforeSend: function(xhr, settings) {
		        if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
		            // Send the token to same-origin, relative URLs only.
		            // Send the token only if the method warrants CSRF
					// protection
		            // Using the CSRFToken value acquired earlier
		            xhr.setRequestHeader("X-CSRFToken", csrftoken);
		        }
		   }
	});
	
	// First show that we are doing something
	$('#waiting_gif').html('<img id="loader-img" alt="" src="/static/themes/neumaThemeV2/images/loader.svg" width="100" height="100" align="center" />');

	// Compute annotations for this opus and this model (synchronous call)
	url_cpt_annot = '/rest/collections/' + opus_ref1.replace(/:/g, "/")  + "/_comparison/" + opus_ref2.replace(/:/g, "/") + "/_model/"  + model_code + '/_compute/'
	console.log ("Call " + url_cpt_annot)
	$.ajaxSetup({async: false});
	$.ajax({
        url : url_cpt_annot,
		type : 'POST',
		data : {},
		dataType : 'json',
		success : function(data) {
            if(data) {   // DO SOMETHING
				$('#cost').html("Comparison Cost: " + data["cost"]);
            } else { // DO SOMETHING
                $('#cost').html("The cost was not compiled");
            }
		},
		error : function(request, error) {
			alert("Request: " + JSON.stringify(request));
		}
	});
	$.ajaxSetup({async: true});

	// OK remove the waiting GIF
	$('#waiting_gif').html("");

	// Show the list of annotations for this opus and this model
	ShowAnnotations(opus_ref1, model_code, "_all", true)
	ShowAnnotations(opus_ref2, model_code, "_all", true)
	return true
}



/**
 * Call Ajax to retrieve the description of a note
 */

function getNoteDescription(opus_ref, note_id) {

	console.log ("Call element description for opus " + opus_ref + " and element " +  note_id) 
	url_user = '/rest/misc/user/'
	console.log ("Call current user description " + url_user)
	var current_user = ""
		
	$.ajax({
		url : url_user,
		type : 'GET',
		data : {}, 
		dataType : 'json',
		async: false,
		success : function(data) {
			current_user = data
		},
		error : function(request, error) {
			alert("Request: " + JSON.stringify(request));
		}
	});
	
	url_rest = '/rest/collections/' + opus_ref.replace(/:/g, "/")  + '/' +  note_id
	console.log ("Call element description at " + url_rest)

	/* Load the MEI file using HTTP GET */
	url_mei = '/rest/collections/' + opus_ref.replace(/:/g, "/")  + '/mei.xml/'
	console.log ("Load MEI file  " + url_mei)
  $.ajax({
    type: "GET" ,
    url: url_mei ,
    dataType: "xml" ,
    success: function(xml) {
    	
    // Find the note thanks to its id
    var children = $(xml).find('note[xml\\:id="' + note_id + '"]')
    
    children.each(function(iNote){
    	// Put the serialized note element in the XML editor
    	var xmlText = new XMLSerializer().serializeToString(children[iNote]);
    	var infobox = document.getElementById("infobox")
		
		if (infobox) {
			var editor = document.getElementById("xml_edit");
			//Xonomy.setMode("laic");
			Xonomy.render(xmlText, editor, xonomy_note_spec);
		}
    	// $("#infobox").find("#xml_edit").val (xmlText);
    }); 
    }       
  });            

	$.ajax({
		url : url_rest,
		type : 'GET',
		data : {},
		dataType : 'json',
		success : function(data) {
			var infobox = document.getElementById("infobox")
			
			if (infobox) {

				// Annotation creation
				if (current_user.username != "") {
					$("#annotation-create-form" ).empty()
					create_annot = $("#annotation_form_div" ).clone();
					create_annot.show()
					create_annot.find("#create_annotation_opus_ref").val (opus_ref);
					create_annot.find("#create_annotation_note_id").val (note_id);
					$("#annotation-create-form" ).append(create_annot)
				}
				
				// Element description, including list of annotations
				$("#score_element_id").html (note_id)
				$("#annotation_element_id").html (note_id)
				console.log ("Affectation Note id " + note_id)
				$("#annotations_list").empty ()
				for (i in data.annotations) {
					annotation = data.annotations[i]
					annot_elem = $( "#annotation_description" ).clone();
					// Change the annotation values in the form
					annot_elem.find("#annotation_opus_ref").val (opus_ref);
					annot_elem.find("#annotation_id").val (annotation.id);
					annot_elem.find("#annotation_note_id").val (note_id);
					annot_elem.find("#annotation_creator_type").html (annotation.creator.type);
					annot_elem.find("#annotation_creator_name").html (annotation.creator.name);
					annot_elem.find("#annotation_motivation").html (annotation.motivation);
					annot_elem.find("#annotation_class").html (annotation.annotation_model);
					annot_elem.find("#annotation_target").html (annotation.annotation_concept);
					annot_elem.find("#annotation_created_at").html (annotation.created);
										
					annot_elem.find("#annotation_target_source").html (annotation.target.resource.source);
					annot_elem.find("#annotation_target_selector_type").html (annotation.target.resource.selector.type);
					annot_elem.find("#annotation_target_selector_value").html (annotation.target.resource.selector.value);
	
					if (annotation.body.type == "SpecificResource") {
						annot_elem.find("#annotation_body_source").html (annotation.body.resource.source);
						annot_elem.find("#annotation_body_selector_type").html (annotation.body.resource.selector.type);
						annot_elem.find("#annotation_body_selector_value").html (annotation.body.resource.selector.value);
					}
					if (annotation.body.type == "TextualBody") {
						//body_source = annot_elem.find("#annotation_body_source");
						//body_source.parentNode.removeChild(body_source)
						annot_elem.find("#annotation_body_selector_value").html (annotation.body.value);
					}
					annot_elem.show()
					annot_elem.appendTo( $("#annotations_list"));
					
					// If the annotation belongs to the user: show the
					// Update form
					if (current_user.username == annotation.creator.name) {
							form_elem = $( "#annotation_update" ).clone();
							form_elem.find("#update_annotation_opus_ref").val (opus_ref);
							form_elem.find("#update_annotation_id").val (annotation.id);
							form_elem.find("#update_annotation_note_id").val (note_id);
							form_elem.find("#update_annotation_comment").val (annotation.comment);
							form_elem.show()
							form_elem.appendTo( $("#annotations_list"));
						}
				}
				
				// XML fragment edition
				if (current_user.username != "") {
					$("#annotation-xmlfragment" ).empty()
					xmlfragment_form_div = $("#xmlfragment_form_div" ).clone();
					xmlfragment_form_div.show()
					$("#xmlfragment_element_id").html (note_id)
					xmlfragment_form_div.find("#xmlfragment_opus_ref").val (opus_ref);
					xmlfragment_form_div.find("#xmlfragment_note_id").val (note_id);
					xmlfragment_form_div.find("#xmlfragment_annotation_id").val (note_id);
					$("#annotation-xmlfragment" ).append(xmlfragment_form_div)
				}

				// Make the info box visible
				$("#infobox").show()

				// Add a link to play from this note
				/*
				 * var item = document.createElement('li'); var button =
				 * document.createElement("input"); button.type = "button";
				 * button.value = "Play MIDI from this note ";
				 * button.setAttribute('id', opus_ref + "@" + note_id);
				 * button.onclick = function(event) { var opus_ref =
				 * $(this).attr("id").split('@')[0] var note_id =
				 * $(this).attr("id").split('@')[1] play_midi(vrvToolkit,
				 * note_id) } item.appendChild (button) list.appendChild (item)
				 */
 
				// infobox.appendChild (list)
								
			}
		},
		error : function(request, error) {
			alert("Request: " + JSON.stringify(request));
		}
	});

}

/* For quality only */

function GetQualityConcepts(opus_ref) {
	ShowModelConcepts(opus_ref, 'quality')
}

/* For comparison only */

function GetComparisonConcepts(opus_ref) {
	ShowModelConcepts(opus_ref, 'comparison')
}

/**
 * Ajax call to import a file in async mode
 */

function ImportFile(corpus_ref, upload_id) {
	url_rest = '/rest/collections/' + corpus_ref.replace(/:/g, "/")  + '/_uploads/' +  upload_id + '/_import/'
	console.log ("Call import request " + url_rest)

	var csrftoken = $.cookie('csrftoken');
	console.log ("ComputeAnnotations. CSRF cookie: " + csrftoken)
	$.ajaxSetup({
		   beforeSend: function(xhr, settings) {
		        if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
		            xhr.setRequestHeader("X-CSRFToken", csrftoken);
		        }
		   }
    });
	
	alert("Import in progress for corpus " + corpus_ref + " and file " + upload_id)

	$.ajax({
		url : url_rest,
		type : 'POST',
		data : {},
		async: false,
		dataType : 'json',
		success : function(data) {
			list = ""
			for (i in data.imported_opera) {
				list += 		data.imported_opera[i].id + " : " + data.imported_opera[i].title + "\n"
			}
			alert("List of imported opera:\n " + list)

		},
		error : function(request, error) {
			alert("Request: " + JSON.stringify(request));
		}
	});
}

/**
 * Chooses a score from the list of samples, and evaluate its quality
 */
function SelectSampleScore(form) {
	var e = form.querySelector("#selected_sample_score");
	var selected_url = e.options[e.selectedIndex].value;
	$("#url_score").val(selected_url)
	$("#form_submit_score").submit()
	// alert ("Select URL: " + selected_url)
}


/**
 * Chooses an annotation model, and loads its annotations
 */
function SelectAnnotationModel(form) {
	var opus_ref = form.querySelector("#opus_ref").value;
	var e = form.querySelector("#selected_annotation_model");

	console.log ("Load the annotation model  for opus " + opus_ref + 
	     " model "+  e.options[e.selectedIndex].value)
      ShowModelConcepts(opus_ref, e.options[e.selectedIndex].value) 

}
/**
 * Verovio functions
 **/


/**
 A custom element to display and interact with scores
**/


class DisplayVerovioScore extends HTMLElement {
	
  static observedAttributes = ["opus_ref"];
  static verovio = null
  static shadow = null
 
  
  constructor() {
    super();
    
    // Properties
    this.opus_ref = ""
  	this.current_page = 1
  	

	// Load the template	
  	let template = document.getElementById("display-verovio-score");
    let templateContent = template.content;

	// Create a shadow root
    this.shadow = this.attachShadow({ mode: "open" });
    this.shadow.appendChild(templateContent.cloneNode(true));


  }
  
  connectedCallback() {
	
    // Take attribute content and put it inside the info span
    this.opus_ref = this.getAttribute('opus_ref');
    this.mei_url = this.getAttribute('mei_url');
    
    var vrv_options = {
				scale : 35,
				breaks: "encoded",
				condense : 'auto',
				condenseFirstPage : 1
	};

	// Create the Vevorio toolkit instance
	this.vrvToolkit = new verovio.toolkit()
	this.vrvToolkit.setOptions(vrv_options);
 
 	DisplayVerovioScore.verovio = this.vrvToolkit
	DisplayVerovioScore.shadow = this.shadow

	// Where do we show the score
	this.score_div = this.shadow.getElementById("verovio");

	if (this.score_div == null) {
		console.log("Cannot find target = " + target);
		return;
	} else {
		// Get all XML fragments
		 console.log("Calling ShowScore");
		showScore(this.vrvToolkit, this.mei_url, this.score_div)
		
		// Add event handlers
		this.shadow.getElementById("nextPage").addEventListener("click", 
		            () => { this.current_page = Math.min(this.current_page + 1, this.vrvToolkit.getPageCount());
		                    this.nextPageHandler (this.vrvToolkit, 
		                             this.score_div, this.current_page);
		                  });
		this.shadow.getElementById("prevPage").addEventListener("click", 
		            () => { this.current_page = Math.max(this.current_page - 1, 1);
		                    this.prevPageHandler (this.vrvToolkit, 
		                             this.score_div, this.current_page);
		                  });
		this.shadow.getElementById("playMIDI").addEventListener("click", 
		            () => { 
		                    this.playMIDIHandler (this.vrvToolkit);
		                  });
		this.shadow.getElementById("stopMIDI").addEventListener("click", 
									this.stopMIDIHandler);


 		 /**
 		  Set the function as message callback
 		 */
 		 MIDIjs.player_callback = this.midiHightlightingHandler;

	}

	console.log ("Fin callback avec texte " + this.opus_ref + " / "  + this.mei_url)
  }

  disconnectedCallback() {
    console.log("Custom element removed from page.");
  }

  adoptedCallback() {
    console.log("Custom element moved to new page.");
  }

  attributeChangedCallback(name, oldValue, newValue) {
   console.log(`Attribute ${name} has changed.`);
  }
  
  
  nextPageHandler (verovio, target, current_page) {
       target.innerHTML = verovio.renderToSVG(current_page);
   }

  prevPageHandler (verovio, target, current_page) {
       target.innerHTML = verovio.renderToSVG(current_page);
   }

  /**
        The handler to start playing the file
  **/
  playMIDIHandler (verovio) {
       // Get the MIDI file from the Verovio toolkit
       let base64midi = verovio.renderToMIDI();
       // Add the data URL prefixes describing the content
        let midiString = 'data:audio/midi;base64,' + base64midi;
           // Pass it to play to MIDIjs
           MIDIjs.play(midiString);
   }
   
  /**
        The handler to stop playing the file
   **/
   stopMIDIHandler () {
           MIDIjs.stop();
       }

	/**
      Notes highlighting
   **/
   
    midiHightlightingHandler (event) {
	console.log ("Callling midi handler")
     // Remove the attribute 'playing' of all notes previously playing
           let playingNotes = DisplayVerovioScore.shadow.querySelectorAll('g.note.playing');
           for (let playingNote of playingNotes) {
               playingNote.classList.remove("playing");
			}
           // Get elements at a time in milliseconds (time from the player is in seconds)
           let currentElements = DisplayVerovioScore.verovio.getElementsAtTime(event.time * 1000);

           if (currentElements.page == 0) {
        	    console.log ("Page 0")
        	    return;
           }

           if (currentElements.page != currentPage) {
               currentPage = currentElements.page;
               DisplayVerovioScore.shadow.getElementById("notation").innerHTML = DisplayVerovioScore.vrvToolkit.renderToSVG(currentPage);
           }

           // Get all notes playing and set the class
           for (let note of currentElements.notes) {
				console.log ("Show playing")
               let noteElement = DisplayVerovioScore.shadow.getElementById(note);
               if (noteElement) noteElement.classList.add("playing");
           }
       }

}


/**

 * Use Verovio to load and display a MEI doc.
 */


function displayWithVerovio(opusRef, meiUrl, target, highlights, options) {
	/* Create the Vevorio toolkit instance */
	var vrvToolkit = new verovio.toolkit();


	vrvToolkit.setOptions(options);

 	console.log("Verovio has loaded!");
 
	// Where do we show the score
	var vrvDiv = document.getElementById(target);

	// Get the page parameter
	currentPage = getURLParameter('page');
	if (currentPage == null)
		currentPage = 1;

	if (vrvDiv == null) {
		alert("Cannot find target = " + target);
		return;
	} else {
		// Get all XML fragments
		 console.log("Calling ShowScore");
		showScore(vrvToolkit, meiUrl, vrvDiv)
		
		 console.log("ShowScore  has been called!");
		// Links to the pages produced by Verovio
		var links = document.getElementById("links");
		var nbPages = vrvToolkit.getPageCount()

		if (nbPages > 1) {
			var pageRef = 1;
			for (iPage = 0; iPage <= nbPages + 1; iPage++) {
				var liTag = document.createElement('li');
					if (iPage == 0) {
						liTag.setAttribute("class", "leftend");
						pageRef = 1
					} else if (iPage == nbPages + 1) {
						liTag.setAttribute("class", "lastRight");
						pageRef = nbPages
					} else {
						pageRef = iPage
					}
					var aTag = document.createElement('a');
					aTag.setAttribute('href', "?page=" + pageRef);
					if (iPage > 0 && iPage <= nbPages)
						aTag.innerHTML = iPage;
					liTag.appendChild(aTag);
					links.appendChild(liTag);
				}
			}

			/* Highlight the score elements */
			for (var i = 0; i < highlights.length; i++) {
				match = document.getElementById(highlights[i]);
				if (match != null) {
					match.style.stroke = "#ff0487";
					;
					match.style.fill = "#ff0000";
					;
					match.style.fillOpacity = 1.0;
					// var sXML = serializer.serializeToString(match);
					// alert ("Found !" + sXML);
				} else {
					// alert ("Element " + match + " not found ?");
				}
			}

			// Add event handlers on notes
			EventOverNotes(opusRef);
	}
	console.log ("Leave displayWithVerovio")
	return vrvToolkit
}

function compDisplayWithVerovio(meiUrl, target1,target2) {
	/* Create the Vevorio toolkit instance */
	var vrvToolkit = new verovio.toolkit();
	var vrvOptions = {
		scale : 35,
		pageHeight : 20000,
		adjustPageHeight : 1,
		pageMarginLeft : 0,
		breaks : "auto"
	};
	vrvToolkit.setOptions(vrvOptions);

	/* Load the MEI file using HTTP GET */
	$.ajax({
		type: 'GET'
		, url: meiUrl
		, dataType: "json"
		, success: function(data) {
			var svg1 = vrvToolkit.renderData(data.score1_mei, {});
			$(target1).html(svg1);
			var svg2 = vrvToolkit.renderData(data.score2_mei, {});
			$(target2).html(svg2);

		}
	});
	highlights = ["d1e150","d1e262"]

	return highlights
}	

function displayHighlights(highlights) {
	/* Highlight the score elements */
	for (var i = 0; i < highlights.length; i++) {
		match = document.getElementById(highlights[i]);
		console.log(match)
		if (match != null) {
			match.style.stroke = "#ff0487";
			;
			match.style.fill = "#ff0000";
			;
			match.style.fillOpacity = 1.0;
			// var sXML = serializer.serializeToString(match);
			// alert ("Found !" + sXML);
		} else {
			// alert ("Element " + match + " not found ?");
		}
	}
}

function displayComparisonWithVerovio(opusRef, meiUrl, target, highlights) {
	/* Create the Vevorio toolkit instance */
	var vrvToolkit = new verovio.toolkit();
	var vrvOptions = {
		scale : 35,
		pageHeight : 20000,
		adjustPageHeight : 1
	};
	vrvToolkit.setOptions(vrvOptions);

	// Where do we show the score
	var vrvDiv = document.getElementById(target);

	// Get the page parameter
	currentPage = getURLParameter('page');
	if (currentPage == null)
		currentPage = 1;

	if (vrvDiv == null) {
		alert("Cannot find target = " + target);
		return;
	} else {
		// Get all XML fragments
		alter = GetAnnotations(opusRef, "comparison",  "composer")

		showScore(vrvToolkit, meiUrl, vrvDiv, alter)

		// Links to the pages produced by Verovio
		var links = document.getElementById("links");
		var nbPages = vrvToolkit.getPageCount()

		if (nbPages > 1) {
			var pageRef = 1;
			for (iPage = 0; iPage <= nbPages + 1; iPage++) {
				var liTag = document.createElement('li');
					if (iPage == 0) {
						liTag.setAttribute("class", "leftend");
						pageRef = 1
					} else if (iPage == nbPages + 1) {
						liTag.setAttribute("class", "lastRight");
						pageRef = nbPages
					} else {
						pageRef = iPage
					}
					var aTag = document.createElement('a');
					aTag.setAttribute('href', "?page=" + pageRef);
					if (iPage > 0 && iPage <= nbPages)
						aTag.innerHTML = iPage;
					liTag.appendChild(aTag);
					links.appendChild(liTag);
				}
			}

			/* Highlight the score elements */
			for (var i = 0; i < highlights.length; i++) {
				match = document.getElementById(highlights[i]);
				if (match != null) {
					match.style.stroke = "#ff0487";
					;
					match.style.fill = "#ff0000";
					;
					match.style.fillOpacity = 1.0;
					// var sXML = serializer.serializeToString(match);
					// alert ("Found !" + sXML);
				} else {
					// alert ("Element " + match + " not found ?");
				}
			}

			// Add event handlers on notes
			EventOverNotes(opusRef);
	}
	return vrvToolkit
}


/**
 * Call Ajax to insert/update a new XML fragment
 */
function reloadScore() {
	var opus_ref = $("#compute_opus_ref").val()
	var mei_url  = $("#mei_url").val()

	// Get all XML fragments
	var model_code = "quality" // Temporary
	var concept_type = "composer" // Temporary
	alter = GetAnnotations(opus_ref, model_code, concept_type) 
	showScore(vrvToolkit, mei_url,  document.getElementById("verovio"), alter);
}


/**
 * Ajax call: get the MEI file and show the score
 */

function showScore(vrvToolkit, meiUrl, vrvDiv, alter=[]) 
{
	  // Load MEI file
	  fetch(meiUrl)
	        .then( (response) => response.text() )
	        .then( (meiXML) => {
	          let svg = vrvToolkit.renderData(meiXML, {});
	          vrvDiv.innerHTML = svg;
	    });

 			/*
             Old code managing "'alter" data. Do not know what it means
			for (var j = 0; j < alter.length; j++){
				frag = alter[j]
				console.log ("Found alter for " + frag.note_id + ": " + frag.xml_fragment)
				//var new_node_doc = $.parseXML("<xml version='1.0'>" + frag.xml_fragment + "</xml>")
				// var new_node = $(new_node_doc).find('note')
				var current_node = $(data).find('note[xml\\:id="' + frag.note_id + '"]')
				$(data).find('note[xml\\:id="' + frag.note_id + '"]').replaceWith (frag.xml_fragment)
			}
         */
}

/**
 * Add annotation anchors to the score
 */

function EventOverNotes(opus_ref) {
	$(".note").each(function(i) {
		var note = document.getElementById($(this).attr("id"))

		if (note) {
			note.onmouseover = function(event) {
				// alert ("Color for note")
				note.style.stroke = "#FE9A2E";
				note.style.fill = "#FE9A2E";
				note.style.fillOpacity = 1.0;
			}
			note.onmouseout = function(event) {
				note.style.stroke = "#000000";
				note.style.fill = "#000000";
				note.style.fillOpacity = 1.0;
			}
			note.onclick = function(event) {
				if ($('body').hasClass("quality"))
					{
					    if ($('#playOnClick').is(':checked')) {
					play_midi(vrvToolkit, $(this).attr("id"))
					    }
					}
				else {
					play_midi(vrvToolkit, $(this).attr("id"))
				}
			}
		}
	})
}

/**
 * Add annotation anchors to the score
 */

function AddAnnotationAnchors(model_code, opusRef, annotations, show_annotation) {
	 scanElementByType("note", model_code, opusRef, annotations, show_annotation) ;
	 scanElementByType("measure", model_code, opusRef, annotations, show_annotation); 
	}
	
function scanElementByType(type_elt, model_code, opusRef, annotations, show_annotation) {
	
	console.log("AddAnnotationAnchors to element of type " + type_elt 
	       + " for model " + model_code + " and opus "
			+ opusRef + " show/hide " + show_annotation)
	// Loop on the notes, search for annotations 
	$("." + type_elt).each(
			function(i) {
				var note = document.getElementById($(this).attr("id"))
				// Keeping the list of offsets to stack the vertical position of anchors
				var offsets = new Object();
				
				console.log ("Searching element with id " + note.id)
				if (annotations.hasOwnProperty(note.id)) {
					nb_annotations = annotations[note.id].length
					for (var i = 0; i < nb_annotations; i++) {
					console.log ("Found annotation " + i)
						// We identify the anchor with
						// opus_ref@note_id@annotation_id@model_code
						annotation = annotations[note.id][i]
						annotation_id = opusRef + '@' + $(this).attr("id")
								+ '@' + annotation.id + '@' + model_code
					
						// Find the vertical offset
						if (offsets[note.id]) {
							offsets[note.id] += 180
						}
						else {
							offsets[note.id] = 600
						}
						
						var circle = CreateAnchor(note, annotation, offsets[note.id])
						circle.setAttributeNS(null, 'id', annotation_id);
						if (show_annotation == true) {
							circle.onclick = function(event) {
								console.log ("Click on circle")
								var opus_ref = $(this).attr("id").split('@')[0]
								var note_id = $(this).attr("id").split('@')[1]
								var annotation_id = $(this).attr("id").split(
										'@')[2]
								var model_code = $(this).attr("id").split('@')[3]
								getNoteDescription(opus_ref, note_id, annotation_id, model_code)
							}
							note.append(circle);
						} else {
							// We need to remove the circle
							var circle = document.getElementById(annotation_id)
							if (circle != null) {
								$(jq(annotation_id)).remove()
							}
						}
					}
				}
			});
}

// Function that creates an anchor for an annotation of a note
function CreateAnchor(note, annotation, delta_y=0) {
	// Get the offset info, which should be a score element that determines the anchor position
	var scoreElement = document.getElementById(note.id)
	if (scoreElement == null){
		console.log ("No way to find the offset defined by " + note.id)
		scoreElement = note
	}
	
	var bbBox = scoreElement.getBBox()
	var yCircle = bbBox.y
	var xCircle = bbBox.x

	// Find the staff the note belongs to
	var staffNode = note.closest(".staff")
	if (staffNode != null) {
		// Find the paths
		var pathNodes = staffNode.childNodes
		for (var i = 0; i < pathNodes.length; i++) {
			if (pathNodes[i].tagName == "path") {
				var pathCoord = pathNodes[i].getAttribute('d').split(' ');
				yCircle = parseInt(pathCoord[1])
				break;
			}
		}
	}
	
	//	console.log ("Annotation for element 135. Offset  = " + annotation.offset + " X coord = " + xCircle
	//		+ " Y coord " + yCircle)

	// Create the circle
	var svg = document.createElementNS("http://www.w3.org/2000/svg", 'svg')
	svg.setAttribute ("x",  xCircle);
	svg.setAttribute ("y",  yCircle  - delta_y);
	svg.setAttribute ("width",  380);
	svg.setAttribute ("height",  380);
	svg.setAttribute ("viewBox", "0 0 5 5");

	var path = document.createElementNS("http://www.w3.org/2000/svg", 'path');
	
	// The icon takes the id of the note, prefixed by 'icon'
	path.setAttribute('id', 'icon:' + note.id);
	path.setAttributeNS(null, 'd', annotation.style.icon);
	path.setAttributeNS(null, 'fill-opacity', 0.6);
	path.setAttributeNS(null, 'fill', annotation.style.color);
	path.setAttributeNS(null, 'stroke', "none");

	svg.appendChild(path)

	//var svg = document.createElementNS(
	//		"http://www.w3.org/2000/svg", 'circle');
	//svg.setAttributeNS(null, 'cx', xCircle + 150);
	//svg.setAttributeNS(null, 'cy', yCircle - 400 - delta_y);
	//svg.setAttributeNS(null, 'r', 150);
	//svg.setAttributeNS(null, 'fill-opacity', 0.6);
	
	return svg
}

// Function that protects special characters in IDs
function jq(myid) {

	return "#" + myid.replace(/(:|\.|\[|\]|,|=|@)/g, "\\$1");

}

/**
 * Clear annotation anchors
 */

function ClearAnnotationAnchors(concept_type) {
	// Maybe check that this indeeds correspond to an annotation
console.log ("Clear annnotation for  " + concept_type)

	$("path").each(function(i) {
		if ($(this).attr("id") != null && $(this).attr("id").startsWith("icon"))
		{
			// Removing all icons
    	    	var circle = document.getElementById($(this).attr("id"))

	        	if (concept_type == "_all") {
		    	circle.parentNode.removeChild(circle);
	        	}
       }
	})
}



/*******************************************************************************
 * MIDI Player function
 ******************************************************************************/

/**
 * Play the MIDI content
 */

function play_midi(vrvToolkit, note_id) {
	var base64midi = vrvToolkit.renderToMIDI();
	var song = 'data:audio/midi;base64,' + base64midi;
	if (note_id != undefined) {
		var time = vrvToolkit.getTimeForElement(note_id);
		// $("#player").midiPlayer.play(song);
		// alert("Playing from note " + note_id + " at time " + time)
		$("#player").midiPlayer.seek(time / 2);
	}
	else {
		$("#player").show();
		//alert("Play from the begining")
		$("#player").midiPlayer.play(song);
	}
}

// ////////////////////////////////////////////////////
/* Two callback functions passed to the MIDI player */
// ////////////////////////////////////////////////////
var midiUpdate = function(time) {
	// bug! time needs to be * 2 (- 800 for adjustment)
	console.log(time);

	var elementsattime = vrvToolkit.getElementsAtTime(time);
	if (elementsattime.page > 0) {
		if (elementsattime.page != page) {
			page = elementsattime.page;
			loadPage();
		}
		if ((elementsattime.notes.length > 0) && (ids != elementsattime.notes)) {
			ids
					.forEach(function(noteid) {
						if ($.inArray(noteid, elementsattime.notes) == -1) {
							$("#" + noteid).attr("fill", "#000").attr("stroke",
									"#000");
						}
					});
			ids = elementsattime.notes;
			ids
					.forEach(function(noteid) {
						if ($.inArray(noteid, elementsattime.notes) != -1) {
							$("#" + noteid).attr("fill", "#c00").attr("stroke",
									"#c00");
							;
						}
					});
		}
	}
}

/**
 * Set back a note to its original display when it is not longer played
 */
var midiStop = function() {
	ids.forEach(function(noteid) {
		$("#" + noteid).attr("fill", "#000").attr("stroke", "#000");
	});
	//$("#player").hide();
	isPlaying = false;
}



   /**
      Navigation functions
   */
   const nextPageHandler = function () {
       currentPage = Math.min(currentPage + 1, vrvToolkit.getPageCount());
       notationElement.innerHTML = vrvToolkit.renderToSVG(currentPage);
   }

   const prevPageHandler = function () {
       currentPage = Math.max(currentPage - 1, 1);
       notationElement.innerHTML = vrvToolkit.renderToSVG(currentPage);
   }

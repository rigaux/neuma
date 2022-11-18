/* rapide test useragent */

function getBrowser() {
ua = navigator.userAgent.toLowerCase();
if ( ua.indexOf('webkit') > 0 ) {
return 'webkit';
} else if ( ua.indexOf('opera') > 0 ) {
return 'opera';
} else if ( ua.indexOf('msie') > 0 ) {
return 'msie';
} else if ( ua.indexOf('ipad') > 0 ) {
return 'ipad';
} else if ( ua.indexOf('iphone') > 0 ) {
return 'iphone';
} else if ( ua.indexOf('ipod') > 0 ) {
return 'ipod';
} else {
return 'gecko';
}
}



// calcul la largeur totale du train

total = 0;
number = 1;

$(function() {

	var totalWidth = 0;
	$('#train .wagon').each( function(i, wagon) {
		totalWidth += $(wagon).width();
		totalWidth += parseFloat($(wagon).css('margin-right'));
		total += 1;
		totalVisible = total - 3;
	});
	// totalWidth = 3100;
	totalWidth += 210;
	/* $('#slider').css('width', totalWidth + 'px'); */
	$('#train').css('width', totalWidth + 'px');
});


$(function() {
		$(".buttonRight").click(function() { 
		
		/* alert(number+" "+total+" "+totalVisible); */
		if (number < totalVisible) {
			number=number+3;
			target="#coll"+number;
			$('.slider').scrollTo(target, 500, {axis:'x'} );
			} else { 
			number=1;
			target="#coll"+number;
			$('.slider').scrollTo(target, 300, {axis:'x'} );
			return false;
			 }
			
		});
	});
$(function() {
		$(".buttonLeft").click(function() { 
			if (number > 3) {
			number=number-3;
			target="#coll"+number;
			$('.slider').scrollTo(target, 500, {axis:'x'} );
			} else { 
			/*
			 * number=total; target="#coll"+number;
			 * $('.slider').scrollTo(target, 5000, {axis:'x'} );
			 */
			return false; }
	
			
		});
	});

/*
 * $(function() { $(".train").draggable({ axis: 'x'}) })
 */




/** **************** */
/* la connexion */
/** **************** */

/* ouverture */


$(function() {
		$("#connexionLink").click(function(event) { 
			$(".attrape-clic").fadeOut("fast");
			$("#connexionZone").toggle('fast');
			event.stopPropagation();
		});
	});

/* fermeture */

/*
 * $(function() { $('html').click(function() { $("#connexionZone").hide('slow');
 * });
 * 
 * $('#connexionZone').click(function(event){ event.stopPropagation(); }); });
 */


/* contenu par d�faut */


/*
 * The default action is chosen by the controller and triggered at the end of the layout
   $(function() {
		$("#connexionZone").load("/ajax/login?");  
	});
	*/
	
/* apr�s identification */


$("#identification").click (function() { 
	s = $("#form_login").serialize();
			
			$("#connexionZone").load("/home/auth?" + s); 
			return false;
		}); 

	
/* apr�s inscription */


$("#inscription").click(function() { 
			
	s = $("#form_user").serialize();
	$("#connexionZone").load ("/home/register?" + s); // append(retour);

			return false;
		});
	
	
/* apr�s d�connexion */


$("#deconnexion").click (function() { 
			
			$("#connexionZone").load("/home/auth?logout=1"); 
			return false;
		}); 

/** **************** */
/* le menu about */
/** **************** */


/* ouverture */

$(function() {
	$(".menuAbout li a").click(function(event) { 
		closeMenuAccess();
		$(".attrape-clic").fadeIn('fast');
		$(".menuAbout ul li").show(200);
		$(".menuAbout ul").addClass("shadow");
	});
});	
function closeMenuAbout() {
	$(".menuAbout li li[class!=selected]").hide(200);
	$(".menuAbout ul").removeClass("shadow");
}
function closeMenuAccess() {
	$(".menuAccess .active").removeClass("active");
	$(".menuAccess li li[class!=selected]").hide(200);
	$(".menuAccess ul li.selected").show(200);
	$(".menuAccess ul").removeClass("shadow");
}
$(function() {
	$(".attrape-clic").click(function() { 
		closeMenuAbout();
		closeMenuAccess();
		$(".attrape-clic").fadeOut("fast");
		
	});
});
	
	

	
/** **************** */
/* le menu access */
/** **************** */

/* fil d'ariane */

$(function() {
			
	$(".menuAccess li.selected").show();
	$(".menuAccess li.selected ul").show();
		
});


/* ouverture par le menu parent */


$(function() {
		$(".menuAccess > li > a").click(function(event) {
		closeMenuAbout(); 
		$(".attrape-clic").fadeIn("fast");
		$(".menuAccess ul").addClass("shadow");
		$(".menuAccess > li > ul > li").show(200);
		$(".menuAccess ul li li").hide(200);
		$(".menuAccess ul li li li").hide(200);
		$(".menuAccess > li > ul").show(200);
		 event.preventDefault();
	});
});
	
/* ouverture par l'enfant */
/* option int�ressante mais peut-�tre contre-intuitive */

/*
 * $(function() { $(".menuAccess > li > ul > li.selected > a").click(function(e) {
 * $(".menuAccess > li > ul > li").show(200); $(".menuAccess ul li
 * li").hide(200); $(".menuAccess ul li li li").hide(200); $(".menuAccess > li >
 * ul").show(200); if ($(this).hasClass("active") == false) {
 * e.preventDefault(); $(this).addClass("active"); } }); });
 */

/* fermeture */
/* merged  */
	
	

/** **************** */
/* le clavier */
/** **************** */

/* ouverture */


$(function() {
	$("#keyboardLink").click(function(event) { 
		
		$("#keyboardZone").toggle('fast');
		$("#keyboardLink").toggleClass('active');
		event.stopPropagation();
	});
});

/* contenu par d�faut 
 * 


$(function() {
		 $("#keyboardZone").load("/home/keyboard");
	});

 */
/** **************** */
/* les corpus */
/** **************** */

/* ouverture */


$(function() {
	$("#collectionsLink").click(function(event) { 
		
		$("#collectionsZone").toggle('fast');
		$("#collectionsLink").toggleClass('active');
		event.stopPropagation();
	});
});
	
	
	/* contenu par d�faut */


$(function() {
		// $("#collectionsZone").load("content/pages/collectionsSearch.php");
	});
	
/** *********** */
/* fermetures */
/** *********** */




$(function() {
	$('html').click(function(event) {
		var $target = $(event.target);
		if ($target.parents('#connexionZone').length == 0) {
     	$("#connexionZone").hide('fast');
  	  } 
  	  
  	  	if ($target.parents('#keyboardZone').length == 0) {
     	$("#keyboardZone").hide('slow');
     	$("#keyboardLink").removeClass('active');
  	  }
  	  
  	  if ($target.parents('#collectionsZone').length == 0) {
     	$("#collectionsZone").hide('slow');
     	$("#collectionsLink").removeClass('active');
  	  }
			
	 });
});

/** *********** */
/* tooltips */
/** *********** */

$(function() {
	$('#concepts_list').on('mouseenter','.tooltip img', function() {
		$(this).parent('.tooltip').addClass('hovered');
	});
	$('#concepts_list').on('mouseleave','.tooltip img', function() {
		$(this).parent('.tooltip').removeClass('hovered');
	});
});



/********************/
/*    QUALITY 		*/
/********************/


/* Welcome message with 7 day cookie save*/

$(function() {
  if ($.cookie('help') == "none") {
  	$('.welcome-help').hide();
  }
  $('body').on('click','.welcome-help .close-parent', function() {
  	$.cookie('help', 'none', { expires: 7 });
    $(this).parent('div').fadeOut('fast');
  });
});

/* Pay on clic with 1 day cookie save*/

$(function() {

	if ($.cookie('playOnClick') == "true") {
		$('#playOnClick').prop('checked', true);
	} else {
		$('#playOnClick').prop('checked', false);
	}

	$('body').on('click','#playOnClick', function() {
		if ($('#playOnClick').is(':checked')) {
			var playOnClickPref = true;
		} else {
			var playOnClickPref = false;
		}
		$.cookie('playOnClick', playOnClickPref, { expires: 1 });
	});
});


/* concepts palette */

$(function() {
  $('body.quality').on('click','.concepts-trigger:not(.on)', function() {
    $('.concepts-palette').fadeIn('fast');
    $('.concepts-trigger').addClass('on');
  });
  $('body.quality').on('click','.concepts-trigger.on, .close-palette', function() {
    $('.concepts-palette').fadeOut('fast');
    $('.concepts-trigger').removeClass('on');
  });
});


/* display quality palette */

function paletteInit() {
    $(".quality-palette").fadeOut('fast');
    $(".quality-palette").addClass('loading'); 
    $(".quality-palette #infobox").hide();
    $(".note-highlighter").fadeOut('slow');
    $(".attrape-clic.leger").fadeOut('fast');
}

$(function() {
  $('.quality').on('click','svg g.note', function() {
    paletteInit();

    var target = $(this);
	var note_id = target.attr('id');
	$('a.playHere').attr('href',note_id);

	// Take the reference to the current opus, stored in a div 
	//var opus_ref = $("#compute_opus_ref").val()
	//console.log ("Opus reference : " + opus_ref)
	// The following function feeds the content of the Infobox
	// getNoteDescription(opus_ref, note_id)
	
    var position = target.offset();
    var targetLeft = position.left;
    var targetTop = position.top + 15;
    console.log("Target : " + targetLeft + " " + targetTop);
    var windowWidth = $(window).width();
    var windowHeight = $(window).height();
    if (targetLeft > windowWidth - 150) {
      targetLeft = windowWidth - 180;
    }
    if (targetLeft < 150) {
      targetLeft = targetLeft + 180 - targetLeft;
    }
    if (targetTop - $(window).scrollTop() > windowHeight - 400) {
      var delta = $(window).scrollTop() + 300 - target.scrollTop();
      $('html, body').animate({scrollTop: target.scrollTop() + delta  }, 1000);
    }
    $(".quality-palette").css({left: targetLeft, top: targetTop});
    $(".quality-palette").fadeIn('fast');
    $(".note-highlighter").css({left: target.offset().left, top: target.offset().top});
    $(".note-highlighter").fadeIn('fast');
    $(".attrape-clic.leger").fadeIn('fast');
    setTimeout(function(){ 
      $(".quality-palette").removeClass('loading');
      $(".quality-palette #infobox").fadeIn();
    }, 1000);
  });
  $('.quality').on('click','.attrape-clic.leger', function() {
    paletteInit();
  });
});

/* buttons tabs */

$(function() {
  $('.quality').on('click','.buttons a:not(.playHere)', function() {
    $('.buttons a.selected').removeClass('selected');
    $(this).addClass('selected');
    if ($(this).hasClass('annotList')) {
    	$('.annotation-create-tab').hide();
    	$('.annotation-list-tab').show();
    	$('.xml-edit-tab').hide();
    }
    if ($(this).hasClass('annotateHere')) {
    	$('.annotation-create-tab').show();
    	$('.annotation-list-tab').hide();
    	$('.xml-edit-tab').hide();
    }
    if ($(this).hasClass('edit')) {
    	$('.xml-edit-tab').show();
    	$('.annotation-list-tab').hide();
    	$('.annotation-create-tab').hide();
    }
  });
});


/* button play here */

$(function() {
	$('.quality').on('click','.buttons a.playHere', function(event) {
		event.preventDefault();
		var note_id = $(this).attr('href');
		if ($(this).hasClass('playing')) {
			$(this).removeClass('playing');
			$(this).html('<span class="awesome">\uf144</span> Play Here');
			pause();
		} else {
			$(this).addClass('playing');
			$(this).html('<span class="awesome">\uf28b</span> Pause');
			play_midi(vrvToolkit, note_id);
		}
	});
});

/* annotation update */

$(function() {
	$('.quality').on('click','#update-this', function(event) {
		event.preventDefault();
		$(this).next('.annotation-update-form').slideToggle('fast');
	});
});
/* annotation new */

$(function() {
	$('.quality').on('click','a.new-annotation', function() {
		$('#infobox #create_annotation_form').show();
		$('#infobox #annotation_create_feedback').hide();
	});
});


	
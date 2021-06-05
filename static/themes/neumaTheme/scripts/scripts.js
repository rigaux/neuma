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
			$('.slider').scrollTo(target, 800, {axis:'x'} );
			} else { 
			number=1;
			target="#coll"+number;
			$('.slider').scrollTo(target, 3500, {axis:'x'} );
			return false;
			 }
			
		});
	});
$(function() {
		$(".buttonLeft").click(function() { 
			if (number > 3) {
			number=number-3;
			target="#coll"+number;
			$('.slider').scrollTo(target, 800, {axis:'x'} );
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

/* fil d'ariane */

$(function() {
					
			$(".menuAbout li.selected li").hide();
			$(".menuAbout li.selected").show();
			$(".menuAbout li.selected ul").show(200);
			
	});


/* ouverture par le menu parent */

$(function() {
		$(".menuAbout > li > a").click(function(event) { 
			
			$(".menuAbout ul li").show(200);
			$(".menuAbout ul").show(200);
			 event.preventDefault();
			
		});
	});
	
/* ouverture par l'enfant */
$(function() {
		$(".menuAbout ul li.selected a").click(function(e) { 
			
			$(".menuAbout ul li").show(200);
			$(".menuAbout ul").show(200);
			if ($(this).hasClass("active") == false) {
				e.preventDefault();
				$(this).addClass("active");
			}
		});
	});


$(function() {
		$(".menuAbout").mouseleave(function() { 
			$(".menuAbout .active").removeClass("active");
			$(".menuAbout li li[class!=selected]").hide(200);
			$(".menuAbout ul li.selected").show(200);
			
		});
	});
	
	

	
/** **************** */
/* le menu access */
/** **************** */

/* fil d'ariane */

$(function() {
					
			$(".menuAccess li.selected li").hide();
			$(".menuAccess li.selected").show();
			$(".menuAccess li.selected ul").show(200);
			
	});


/* ouverture par le menu parent */

$(function() {
		$(".menuAccess > li > a").click(function(event) { 
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

$(function() {
		$(".menuAccess").mouseleave(function() { 
			$(".menuAccess .active").removeClass("active");
			$(".menuAccess li li[class!=selected]").hide(200);
			$(".menuAccess ul li.selected").show(200);
			
		});
	});
	
	
	

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
     	$("#connexionZone").hide('slow');
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
	
var vis = new Array();


	var memo_obj = new Array();

	function findObj(n) { 
		var p,i,x;

		// Voir si on n'a pas deja memoriser cet element		
		if (memo_obj[n]) {
			return memo_obj[n];
		}
		
		d = document; 
		if((p = n.indexOf("?"))>0 && parent.frames.length) {
			d = parent.frames[n.substring(p+1)].document; 
			n = n.substring(0,p);
		}
		if(!(x = d[n]) && d.all) {
			x = d.all[n]; 
		}
		for (i = 0; !x && i<d.forms.length; i++) {
			x = d.forms[i][n];
		}
		for(i=0; !x && d.layers && i<d.layers.length; i++) x = findObj(n,d.layers[i].document);
		if(!x && document.getElementById) x = document.getElementById(n); 
		
		// Memoriser l'element
		memo_obj[n] = x;
		
		return x;
	}
	
	function hide_obj(obj) {
		element = findObj(obj);
		if(element) {
			if (element.style.visibility != "hidden") element.style.visibility = "hidden";
		}
	}

function swap_couche(couche, rtl, dir) {
	triangle = findObj('triangle' + couche);
	tiroir = 'tiroir' + couche;
	if (!(layer = findObj('Layer' + couche))) return;
	if (vis[couche] == 'hide'){
		if (triangle) triangle.src = dir + 'deplierBas.gif';
		layer.style.display = 'block';
		document.getElementById(tiroir).className = 'tiroirActif';
		vis[couche] = 'show';
	} else {
		if (triangle) triangle.src = dir + 'deplierHaut.gif';
		layer.style.display = 'none';
		document.getElementById(tiroir).className = 'tiroirInactif';
		vis[couche] = 'hide';
	}
}
function ouvrir_couche(couche, rtl, dir) {
	triangle = findObj('triangle' + couche);
	tiroir = 'tiroir' + couche;
if (!(layer = findObj('Layer' + couche))) return;
	if (triangle) triangle.src = dir + 'deplierBas' + rtl + '.gif';
	layer.style.display = 'block';
	document.getElementById(tiroir).className = 'tiroirActif';
	vis[couche] = 'show';
}
function fermer_couche(couche, rtl, dir) {
	triangle = findObj('triangle' + couche);
	tiroir = 'tiroir' + couche;
if (!(layer = findObj('Layer' + couche))) return;
	if (triangle) triangle.src = dir + 'deplierHaut' + rtl + '.gif';
	layer.style.display = 'none';
	document.getElementById(tiroir).className = 'tiroirInactif';
	vis[couche] = 'hide';
}
function manipuler_couches(action, rtl, first, last, dir) {

	if (action=='ouvrir') {
		for (j=first; j<=last; j+=1) {
			ouvrir_couche(j, rtl, dir);
		}
		return;
	} else {
		for (j=first; j<=last; j+=1) {
			fermer_couche(j, rtl, dir);
		}
		return;
	}
}

/* <!-- tiroir 1-->
	<div class="tiroir" id="tiroir1">

					<div class="tiroirBandeau">	
						<a href="javascript:swap_couche('1','','ui/images/');">
						<img id="triangle1" src="ui/images/deplierHaut.gif" alt="ouvrir/fermer" width="11" height="11"  style="vertical-align: center;" />&nbsp;&nbsp;Voir dans  le tiroir</a>						
					
					
					<div class="cleaner droit">&nbsp;</div>
					</div><!--  fin tiroirBandeau -->
				
			<!--  affichage du contenu du tiroir -->
			
					
			
			
					<script type="text/javascript">
					<!--
					vis['1'] = 'hide';
					document.write('<div id="Layer1" style="display: none; margin-top: 0;" class="contenuTiroir">');
					//-->
					</script>
					
					<div class="contenuTiroirAlt">

						
						
			<!--  contenu du tiroir -->
			
		
		
<p class="smallText">
Les journalistes se sont pressés hier par centaines au Louvre pour voir Monna Lisa dans ses nouveaux appartements. Le célébrissime portrait a été replacé dans un écrin monumental, dans la salle des Etats, rebaptisée <a href="javascript:void(0);">«salle de la Joconde»</a>, au terme de quatre ans de rénovation, financée par la télévision japonaise qui entend bien associer son nom à la notoriété mondiale de la dame. A partir d'aujourd'hui, le public est à même de découvrir cet espace vaste et lumineux, aux couleurs agréables, dans les tons beiges et bois.
</p>
					
					
					
			<!--  fin du contenu du tiroir -->	
			
					</div><!--  fin du contenuTiroirAlt -->
	
					<script type="text/javascript">
					<!--
					document.write('</div>');
					//--></script>
					
					
				
	</div><!--  fin tiroir 1 -->
	
	*/
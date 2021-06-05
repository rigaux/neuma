function ouvrePopup(fichier,titre,optionsFen) {
  Fen = window.open(fichier,titre,optionsFen);
  Fen.focus();

/*Ce script permet d'ouvrir plusieurs popup et de gérer le focus sur chacun d'entre eux.
développé; par n.taffin et Sara Aubry.

on l'utilise ainsi :
<a href="javascript:ouvrePopup('url','nom de fen&ecirc;tre','location=no,toolbar=no,status=no,directories=no,scrollbars=yes,width=250,height=200,top=150,left=300')">lien</a> */


  } // fin de la fonction ouvrePopup

function fermer() {
 window.close();
}
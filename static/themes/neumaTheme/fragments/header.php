

		<div class="headerWrapper" >
		<div class="header" >
		<div class="headerContent">
		
		
<!-- premier étage : languages -->

			<div class="banner langages">
				<ul class="langSelector">
					<li><a href="#">FR</a> / </li>
					<li><a href="#">EN</a></li>
				</ul>
			</div><!-- fin div .langages -->
			
<!-- deuxième étage : platform -->	
		
			<div class="banner platform">
			
			
	<!-- le menu à propos -->			
				<ul class="menu menuAbout">
					<li <?php if($contenu=="about"){echo"class=\"selected\"";} ?>>
					<a href="index.php?contenu=about">À propos de…</a>
						<ul>
							<li><a href="index.php">Accueil</a></li>
							<li><a href="index.php?contenu=about">Présentation</a></li>
							<li><a href="index.php?contenu=about">Actualités</a></li>
							<li <?php if($contenu=="about"){echo"class=\"selected\"";} ?>><a href="index.php?contenu=about">Publications</a></li>
							<li><a href="index.php?contenu=about">Rest Services</a></li>
							<li><a href="index.php?contenu=about">Contact</a></li>
							<div class="clearer">&nbsp;</div>
						</ul>					
					</li>
					<div class="clearer">&nbsp;</div>
				</ul>
				
				
				
	<!-- la connexion -->				
				<a href="javascript:void(0);" id="connexionLink">Connexion</a>
				
				<div id="connexionZone">
				
					<!-- ajax content here -->
				
				</div><!-- ending connexionZone -->
				
	<!-- le logo -->				
				<a class="logo" href="index.php?contenu=accueil" title="Neuma home page"><span class="accessibility">Neuma home page</span></a>
			
			<div class="clearer">&nbsp;</div>
			</div><!-- fin div .platform -->
			

<!-- troisième étage : access -->	
			
			<div class="banner access">
			
<!-- le menu collections -->				
				<ul class="menu menuAccess">
					
					<li <?php if($contenu=="collections" or $contenu=="corpus" or $contenu=="souscorpus" or $contenu=="partition"){echo"class=\"selected\"";} ?>>
					<a href="index.php?contenu=collections">Collections…</a>
						<ul>
							<li <?php if($contenu=="collections"){echo"class=\"selected\"";} ?>><a href="index.php?contenu=collections">Tout voir…</a></li>
							<li <?php if($contenu=="corpus" or $contenu=="souscorpus" or $contenu=="partition"){echo"class=\"selected\"";} ?>>
								<a href="index.php?contenu=corpus">Psautiers</a>
								<ul>
									<li <?php if($contenu=="souscorpus" or $contenu=="partition"){echo"class=\"selected\"";} ?>>
										<a href="index.php?contenu=souscorpus">Godeau 1655</a>
											<ul>
												<li <?php if($contenu=="partition"){echo"class=\"selected\"";} ?>><a href="index.php?contenu=partition">Psaume 2</a></li>
											</ul>
									</li>
									<li><a href="index.php?contenu=souscorpus">Godeau 1622</a></li>
								</ul>		
							</li>
							<li><a href="index.php?contenu=corpus">Rism</a></li>
							<li><a href="index.php?contenu=corpus">Sequentia</a></li>
							
						</ul>					
					</li>
				</ul>
				
<!-- rechercher -->				
				<div class="searchForm">
				
					<form action="" method="">
					
						<fieldset>
						
						<div id="scoreSnippet" style="">
						<!-- background this div with the score snippet -->	
						<input id="expression" type="text" name="expression" value="Rechercher" id="expression" onfocus="if (this.value=='Rechercher') this.value=''" onblur="if (this.value=='') this.value='Rechercher'">
						</div>
						
						<a id="keyboardLink" title="voir le Clavier"><span class="accessibility">Keyboard</span></a>
						
						<a id="collectionsLink" title="choisir les Collections"><span class="accessibility">Collections</span></a>
						
						<div id="keyboardZone">
					
							<!-- ajax content here -->
					
						</div><!-- ending keyboardZone -->
						
						<div id="collectionsZone">
					
							<!-- ajax content here -->
					
						</div><!-- ending collectionsZone -->
						
						<input id="submitButton" type="submit" value="OK" />
						
						</fieldset>
						
					</form>
				
				</div>
				
				
				
				
				
			<div class="clearer">&nbsp;</div>
			</div><!-- fin div .access -->
			

			<div class="clearer">&nbsp;</div>
		</div><!-- fin div .headerContent -->
		</div><!-- fin div .header -->
		</div><!-- fin div .headerWrapper -->
		
		
	
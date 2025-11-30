
import time
import sys, os
import socket
import argparse
from pathlib import Path

import lib.iiif.IIIF3 as iiif3_mod

"""
	Utility functions that create ad-hoc manifests	
"""

def corpus_collection (coll):
	title_prop = iiif3_mod.Property (coll.short_title)
	collection = iiif3_mod.Collection(coll.url, title_prop)
	
	if coll.description is not None:
		summary_prop = iiif3_mod.Property (coll.description)
		collection.set_summary (summary_prop)
	if coll.licence is not None:
		collection.set_rights (coll.licence["url"])

	if coll.thumbnail is not None:
		thumbnail_prop =  iiif3_mod.ImageBody (coll.thumbnail["url_default"], 
				coll.thumbnail["width"], coll.thumbnail["height"])
		collection.set_thumbnail (thumbnail_prop)

	if coll.organization is not None:
		label_prop = iiif3_mod.Property (coll.organization["name"])
		logo_prop =  iiif3_mod.ImageBody (coll.organization["logo"]["url_default"], 
				coll.organization["logo"]["width"], 
				coll.organization["logo"]["height"])
		hp_prop = iiif3_mod.Property (coll.organization["name"])
		homepage_prop =  iiif3_mod.Homepage (
			id=coll.organization["homepage"], label=hp_prop
		)
		provider = iiif3_mod.Provider (
			id=coll.url + "provider", 
			label=label_prop,
			logo=logo_prop,
			homepage=homepage_prop)
		collection.set_provider (provider)

	if coll.copyright is not None:
		require_stmt_prop = iiif3_mod.Metadata (iiif3_mod.Property("attribution"), 
								iiif3_mod.Property(coll.copyright))
		collection.set_required_statement (require_stmt_prop)
		
	# Add metadata
	title_meta =  iiif3_mod.Metadata (iiif3_mod.Property("title"), 
								iiif3_mod.Property(coll.title))
	collection.add_metadata (title_meta)

	return collection
	

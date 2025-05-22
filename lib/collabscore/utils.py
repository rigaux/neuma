import sys 
import lib.collabscore.parser as parser_mod

from .editions import Edition
#
# Utility functions for the CollabScore parser
#

def check_header_consistency(mnf_system, measure_no, parts, headers):
	"""
	  Each measure begins with a list of headers, one for
	  each staff. They contains clefs, times signatures
	  and key signatures.
	  
	  The function check that thay are consistent, and try to fix problems
	 """
	
	fix_editions = []
	
	 # We need to collect the KS of each part
	list_ks_by_part = {}
	for id_part in parts.keys():
		list_ks_by_part[id_part] = {}
					
	# Measure headers (DMOS) tells us, for each staff, if  one starts with a change of clef or meter
	for header in headers:
		# Identify the part, staff and measure, from the staff id
		mnf_staff = mnf_system.get_staff(header.no_staff)
		id_part = mnf_staff.get_part_id()
		count_ks = list_ks_by_part[id_part]
		
		if header.key_signature is not None:
			key_sign = header.key_signature.get_notation_object()
			if key_sign.code() not in count_ks.keys():
				count_ks[key_sign.code()] = {"part": id_part, "key": key_sign, "count": 1, 
					"errors": header.key_signature.errors}
			else:
				count_ks[key_sign.code()]["count"] += 1
		else:
			count_ks["none"] =  {"part": id_part, "key": None}

	parser_mod.logger.info("")
	parser_mod.logger.info("Checking  signatures for the current measure")
	parser_mod.logger.info("")

	list_part_keys = []	
	# First check that the key signatures are the same inside each part
	for id_part in list_ks_by_part.keys(): 
		count_ks = list_ks_by_part[id_part]
		# There should be only one key signature
		if len(count_ks) > 1:
			# We can assume that the OMR system  has misinterpreted a single alteration as a signature
			parser_mod.logger.warning (f"Measure {measure_no} in part {id_part} has inconsistent key signatures. Assume an OMR misinterpretattion and clear all")

			for header in headers:
				# Identify the part, staff and measure, from the staff id
				mnf_staff = mnf_system.get_staff(header.no_staff)
				id_part_header = mnf_staff.get_part_id()
				if id_part_header == id_part and header.key_signature is not None:
					# Produce an edition to remove the 		
					edition = Edition (Edition.REMOVE_OBJECT, header.key_signature.id)
					fix_editions.append (edition)
			# Now the KS is None for this part
			list_part_keys.append({"part": id_part, "key": None})
		else:
			# OK all the KS of the part are the same. We keep the part's signature
			list_part_keys.append(next(iter(count_ks.values())))

	# Now check that all KS are the same for all the parts
	count_ks = {}
	for part_key in list_part_keys:
		if part_key["key"] is None:
			key_code = "none"
		else:
			key_code = part_key["key"].code()
		if key_code not in count_ks.keys():
			count_ks[key_code] = {"key": part_key["key"], "count": 1}
		else:
			count_ks[key_code]["count"] += 1

	if len (count_ks) > 1:
		# We have distinct keys on all staves. Damned,
		mess = ""
		max_count = 0
		for ks_code in count_ks.keys():
			nb_ks = count_ks[ks_code]["count"]
			if max_count < nb_ks:
				max_count = nb_ks
				best_key = count_ks[ks_code]["key"]				
			mess += f"{ks_code}, {nb_ks} times, "
			  
		parser_mod.logger.warning (f"At measure {measure_no}. Inconsistency of key signatures : {mess}. best key: {best_key}")
		for ks_code in count_ks.keys():
			if ks_code != best_key.code():
				if count_ks[ks_code]["key"] is not None:
					corrected_key = count_ks[ks_code]["key"]
					edition = Edition (Edition.REPLACE_KEYSIGN, target=corrected_key.id,
					             params= {"nb_sharps": best_key.nb_sharps, "nb_flats":  best_key.nb_flats})
					fix_editions.append(edition)
					parser_mod.logger.warning (f"Correcting key {corrected_key} to {best_key}")
					corrected_key.local_copy (best_key)
				else:
					parser_mod.logger.warning (f"We do not know how to correct a missing key...")
					

	return fix_editions
import sys 
import lib.collabscore.parser as parser_mod

from .editions import Edition

import lib.music.notation as score_notation
#
# Utility functions for the CollabScore parser
#

# A class that conveniently represents the distribution
# of reading objects (clef, keysign, timesign) over parts
#
class Headers():
	MISSING_CODE = "missing"
	
	def __init__(self, part_ids, measure_no):
		self.part_signs = {}
		self.measure_no = measure_no
		# Input must be a list of part ids
		for id_part in part_ids:
			self.part_signs[id_part] = {"sign_objects": {}}
			
		# Fixing the headers will result in a list of editions
		self.fix_editions = []
	
	def add_part_sign (self, id_part, sign_code, sign_object):
		# Record that a signature objects has been met
		part_sign = self.part_signs[id_part]
		if sign_code  not in part_sign["sign_objects"].keys():
			part_sign["sign_objects"][sign_code] =  {"sign": sign_object, "count": 1}
		else:
			part_sign["sign_objects"][sign_code]["count"] += 1
	def mark_missing_parts(self):
		# A part might not appear on a system, and thus has not sign
		for id_part in self.part_signs.keys():
			if len(self.part_signs[id_part]["sign_objects"]) == 0:
				self.add_part_sign (id_part, Headers.MISSING_CODE, None)

	def count_signs_for_part (self, id_part):
		# How many distinct signatures for this part ?
		return len (self.part_signs[id_part]["sign_objects"].keys())
	
	def fix_inconsistent_part(self, id_part):
		# We found that a part has distinct signatures: fix it
		part_signs = self.part_signs[id_part]
		# First (best) case: no missing signatures
		if not self.missing_sign (id_part):
			# Compute the best one
			best_sign = None
			mess = ""
			for sign_code, sign_info in part_signs["sign_objects"].items():
				mess += f"{sign_code} / "
				if best_sign is None:
					best_sign = sign_info["sign"]
				else:
					best_sign = best_sign.choose_best (sign_info["sign"])
			parser_mod.logger.warning (f"At measure {self.measure_no}, {id_part} has inconsistent signatures {mess}. Best one : {best_sign.code()}")		
			# Second pass: we produce editions for aligning all signatures 
			to_remove = []
			for sign_code, sign_info in part_signs["sign_objects"].items():
				if sign_code != best_sign.code():
					to_remove.append(sign_code)
					edition = Edition (Edition.REPLACE_KEYSIGN, 
								target=sign_info["sign"].id,
								params= {"nb_sharps": best_sign.nb_sharps, 
								"nb_flats":  best_sign.nb_flats})
					self.fix_editions.append (edition)
			# And we also remove from the current list
			for code in to_remove:
				del part_signs["sign_objects"][code]
		else:
			# We could insert a copy of the signature. Difficult ... so
			# we assume that OMR has made a mistake and clear
			parser_mod.logger.warning (f"At measure {self.measure_no}, {id_part} misses one signature. Assume an OMR misinterpretattion and clear all")
			for sign_code, sign_info in part_sign["sign_objects"].items():
				if sign_code != self.MISSING_CODE:
					id_sign = sign_info["sign_object"].id
					parser_mod.logger.warning (f"We remove signature {id_sign}")
					self.fix_editions.append (Edition (Edition.REMOVE_OBJECT, id_sign))
			# This part has not any signature 
			part_sign["sign_objects"] = {}
			part_sign["sign_objects"][self.MISSING_CODE] =  {"sign": None, "count": 1}

	def get_best_sign (self, count_signs):
		# We found that parts have distinct sign. Try to fix
		mess = ""
		best_sign = None
		for sign_code in count_signs.keys():
			part = count_signs[sign_code]["part"]
			if sign_code != Headers.MISSING_CODE:
				sign = count_signs[sign_code]["sign"]
				if best_sign is None:
					best_sign = sign
				else:
					best_sign = best_sign.choose_best (sign)
				mess += f"{sign_code} ({part}, {sign.id}) / "
			else:
				mess += f"{sign_code} ({part}) / "

		parser_mod.logger.warning (f"At measure {self.measure_no}. Inconsistency of signatures over parts : {mess}. Best one: {best_sign}")
		return best_sign
		
	def missing_sign(self, id_part):
		# Check if one signature is missing for a part
		return self.MISSING_CODE in  self.part_signs[id_part]["sign_objects"].keys()
	
	def get_part_sign_code(self, id_part):
		part_sign = self.part_signs[id_part]["sign_objects"]
		# Sanity : at this point, we should have fixed internally the part
		if len (part_sign.keys()) != 1:
			parser_mod.logger.error (f"PANIC At measure {self.measure_no} part {id_part} should have exactly one sign info {part_sign.keys()}")
		else:
			return next(iter(part_sign.keys()))

	def count_distinct_signatures(self):
		# Determine the part signatures and their count
		count_ks = {}
		for id_part in self.part_signs.keys():
			sign_code = self.get_part_sign_code(id_part)
			part_sign = self.part_signs[id_part]

			sign_info = part_sign["sign_objects"][sign_code]
			if sign_code not in count_ks.keys():
				count_ks[sign_code] = {"sign": sign_info["sign"], "count": 1, "part": id_part}
			else:
				count_ks[sign_code]["count"] += 1
		return count_ks

def check_header_consistency(mnf_system, measure_no, parts, headers):
	"""
	  Each measure begins with a list of headers, one for
	  each staff. They contains clefs, times signatures
	  and key signatures.
	  
	  The function check that thay are consistent, and try to fix problems
	 """

	# We need to collect the KS of each part
	headers_keysign = Headers(parts.keys(), measure_no)

	# Measure headers (DMOS) tells us, for each staff, if  one starts with a change of clef or meter
	for header in headers:
		# Identify the part, staff and measure, from the staff id
		mnf_staff = mnf_system.get_staff(header.no_staff)
		id_part = mnf_staff.get_part_id()
		if header.key_signature is not None:
			key_sign = header.key_signature.get_notation_object()
			headers_keysign.add_part_sign (id_part, key_sign.code(), key_sign)
	headers_keysign.mark_missing_parts()
	
	# First check that the key signatures are the same inside each part
	for id_part in parts.keys(): 
		# There should be only one key signature
		if headers_keysign.count_signs_for_part(id_part) > 1:
			headers_keysign.fix_inconsistent_part(id_part)

	# Now check that all KS are the same for all the parts
	count_signs = headers_keysign.count_distinct_signatures()

	if len (count_signs) > 1:
		best_sign = headers_keysign.get_best_sign(count_signs)
		# Allright. We replace all faulty keys by the best one
		for sign_code in count_signs.keys():
			if sign_code == Headers.MISSING_CODE: 
				parser_mod.logger.warning (f"We do not know how to correct a missing key...")
			elif sign_code != best_sign.code():
				corrected_key = count_signs[sign_code]["sign"]
				edition = Edition (Edition.REPLACE_KEYSIGN, target=corrected_key.id,
					params= {"nb_sharps": best_key.nb_sharps, "nb_flats":  best_key.nb_flats})
				self.fix_editions.append(edition)
				parser_mod.logger.warning (f"Correcting key {corrected_key} to {best_key}")

	#for ed in headers_keysign.fix_editions:
	#	print (f"Resulting edition : {ed}")
	return headers_keysign.fix_editions
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
	MISSING_CODE = "missing_sign"
	KEYSIGN_TYPE = "key"
	TIMESIGN_TYPE = "time"

	def __init__(self, type_sign, measure_no, mnf_system, headers):
		self.measure_no = measure_no

		# We process either keysign ot timesign objects
		if type_sign != self.KEYSIGN_TYPE:
			self.type = self.TIMESIGN_TYPE
		else:
			self.type = self.KEYSIGN_TYPE

		# We will record the fact that we found a signature
		self.signature = None
		
		# We keep the headers, maybe we will have to change them
		self.headers = headers
		
		# Scan the headers and get, for each staff, the signatures of missing info
		self.part_signs = {}
		for header in self.headers:
			# Identify the part, staff and measure, from the staff id
			mnf_staff = mnf_system.get_staff(header.no_staff)
			id_part = mnf_staff.get_part_id()
			# Create the array of signatures
			if id_part not in self.part_signs.keys():
				self.part_signs[id_part] = {"sign_objects": {}}
			
			# What signature do we analyse ?
			if self.type == self.TIMESIGN_TYPE:
				if header.time_signature is not None:
					sign = header.time_signature.get_notation_object()
					sign_code = sign.code()
				else:
					sign = None
					sign_code = Headers.MISSING_CODE
			else:
				if header.key_signature is not None:
					sign = header.key_signature.get_notation_object()
					sign_code = sign.code()
				else:
					sign = None
					sign_code = Headers.MISSING_CODE
				
			self.add_part_sign (id_part, sign_code, sign)

		# Fixing the headers will result in a list of editions
		self.fix_editions = []
	
	def add_part_sign (self, id_part, sign_code, sign_object):
		# Record that a signature objects has been met
		part_sign = self.part_signs[id_part]
		if sign_code  not in part_sign["sign_objects"].keys():
			part_sign["sign_objects"][sign_code] =  {"sign": sign_object, "count": 1}
		else:
			part_sign["sign_objects"][sign_code]["count"] += 1
			
	def part_ids(self):
		return self.part_signs.keys()

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
			parser_mod.logger.warning (f"At measure {self.measure_no}, {id_part} has inconsistent {self.type} signatures {mess}. We choose : {best_sign.code()}")		
			# Second pass: we produce editions for aligning all signatures 
			to_remove = []
			for sign_code, sign_info in part_signs["sign_objects"].items():
				if sign_code != best_sign.code():
					to_remove.append(sign_code)
					if self.type == Headers.KEYSIGN_TYPE:
						edition = Edition (Edition.REPLACE_KEYSIGN, target=sign_info["sign"].id,
								params= {"nb_sharps": best_sign.nb_sharps, 
								"nb_flats":  best_sign.nb_flats})
					else: 
						edition = Edition (Edition.REPLACE_TIMESIGN, target=sign_info["sign"].id,
								params= {"time": best_sign.numer, 
								"unit":  best_sign.denom})
					self.fix_editions.append (edition)
			# And we also remove from the current list
			for code in to_remove:
				del part_signs["sign_objects"][code]
		else:
			# We could insert a copy of the signature. Difficult ... so
			# we assume that OMR has made a mistake and clear
			parser_mod.logger.warning (f"At measure {self.measure_no}, {id_part} misses one {self.type} signature. Assume an OMR misinterpretattion and clear all")
			for sign_code, sign_info in part_signs["sign_objects"].items():
				if sign_code != self.MISSING_CODE:
					id_sign = sign_info["sign"].id
					parser_mod.logger.warning (f"We remove {self.type} signature {id_sign}")
					self.fix_editions.append (Edition (Edition.REMOVE_OBJECT, id_sign))
			# This part has not any signature 
			part_signs["sign_objects"] = {}
			part_signs["sign_objects"][self.MISSING_CODE] =  {"sign": None, "count": 1}

	def align_part_signatures(self):
		# At this point, all parts should have a single signature.
		# We check that they are all the same, and align on the best
		# on if necessary
		count_signs = self.count_distinct_signatures()
		if len (count_signs) > 1:
			# Many signatures, find the best one
			best_sign = self.get_best_sign(count_signs)
			# Allright. We replace all faulty keys by the best one
			for id_part in self.part_signs.keys():
				sign_code = self.get_part_sign_code(id_part)
				part_sign_info = self.get_part_sign_info(id_part)
				if sign_code == Headers.MISSING_CODE:
					parser_mod.logger.warning (f"Missing {self.type} sign. for part {id_part}. Setting key to {best_sign}")
					if self.type == Headers.KEYSIGN_TYPE:
						dmos_key = parser_mod.KeySignature.build_from_notation_key(best_sign)
						# Search for the missing headers and inform them
						for header in self.headers:
							if header.key_signature is None:
								header.key_signature = dmos_key
								parser_mod.logger.warning (f"The missing {self.type} sign. has been informed to match the other ones")
					else:
						parser_mod.PSEUDO_SIGN_COUNTER += 1
						best_sign.id = parser_mod.PSEUDO_SIGN_ID + f"{parser_mod.PSEUDO_SIGN_COUNTER}"
						dmos_tsign = parser_mod.TimeSignature.build_from_notation_key(best_sign)
						# Search for the missing headers and inform them
						for header in self.headers:
							if header.time_signature is None:
								header.time_signature = dmos_tsign
								parser_mod.logger.warning (f"The missing {self.type} sign. has been informed to match the other ones")
						
				elif sign_code != best_sign.code():
					corrected_key = part_sign_info["sign"]
					if self.type == Headers.KEYSIGN_TYPE:
						edition = Edition (Edition.REPLACE_KEYSIGN, target=corrected_key.id,
							params= {"nb_sharps": best_sign.nb_sharps, "nb_flats":  best_sign.nb_flats})
					else: 
						edition = Edition (Edition.REPLACE_TIMESIGN, target=sign_info["sign"].id,
								params= {"time": best_sign.numer, "unit":  best_sign.denom})
					self.fix_editions.append(edition)
					parser_mod.logger.warning (f"Correcting sign {corrected_key} to {best_sign}")
			# Cool. Now all parts are align on best_sign = this is THE signature
			self.signature = best_sign
		else:
			sign_code = next(iter(count_signs.keys()))
			self.signature =  count_signs[sign_code]["sign"]
			#print (f"No pb at measure {self.measure_no} for type {self.type}. Signature is {self.signature}")
		return

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

		parser_mod.logger.warning (f"At measure {self.measure_no}. Inconsistency of {self.type} signatures over parts : {mess}. Best one: {best_sign}")
		return best_sign
		
	def missing_sign(self, id_part):
		# Check if one signature is missing for a part
		missing_sign =  (self.MISSING_CODE in  self.part_signs[id_part]["sign_objects"].keys())
		return missing_sign
	
	def get_part_sign_code(self, id_part):
		part_sign = self.part_signs[id_part]["sign_objects"]
		# Sanity : at this point, we should have fixed internally the part
		if len (part_sign.keys()) != 1:
			parser_mod.logger.error (f"PANIC at measure {self.measure_no} part {id_part} should have exactly one sign info {part_sign.keys()}")
		else:
			return next(iter(part_sign.keys()))
	def get_part_sign_info(self, id_part):
		part_sign_code = self.get_part_sign_code (id_part) 
		return self.part_signs[id_part]["sign_objects"][part_sign_code]

	def count_distinct_signatures(self):
		# Determine the part signatures and their count
		count_ks = {}
		for id_part in self.part_signs.keys():
			sign_code = self.get_part_sign_code(id_part)
			part_sign = self.part_signs[id_part]
			sign = sign_info = part_sign["sign_objects"][sign_code]["sign"]
			
			
			if sign_code not in count_ks.keys():
				count_ks[sign_code] = {"sign": sign, "count": 1, "part": id_part}
			else:
				count_ks[sign_code]["count"] += 1
		return count_ks
		
	def check_consistency(self):
		"""
		  Check the consistency of signatures in the headers
		"""

		# First check that the key signatures are the same inside each part
		for id_part in self.part_ids(): 
			# There should be only one key signature
			if self.count_signs_for_part(id_part) > 1:
				self.fix_inconsistent_part(id_part)
		# Now check that all KS are the same for all the parts
		self.align_part_signatures()
		
		return self.headers
		
	def print(self):
		print (f"SHOWING HEADERS")
		for header in self.headers:
			print (header) 
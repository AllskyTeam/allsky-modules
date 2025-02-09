import allsky_shared as allsky_shared

class ALLSKYMODULEBASE:

	params = []
	event = ''
 
	def __init__(self, params, event):
		self.params = params
		self.event = event
		self.debugmode = self.get_param('ALLSKYTESTMODE', False, bool)
		self.debug_mode = self.debugmode
  
	def get_param(self, param, default, target_type=str, use_default_if_blank=False):
		result = default
		try:
			result = self.params[param]
		except (ValueError, KeyError):
			pass

		try:
			result = target_type(result)
		except (ValueError, TypeError) as e:
			have_debug_mode = hasattr(allsky_shared, 'LOGLEVEL')
			if have_debug_mode and allsky_shared.LOGLEVEL == 4:
				allsky_shared.log(4, f'INFO: Cannot cast "{param}" to {target_type.__name__}, value [{result}]. Using default "{default}"')
			result = default
	
		if target_type == str and use_default_if_blank:
			if result == '':
				result = default

		return result
import allsky_shared as allsky_shared

class ALLSKYMODULEBASE:

	params = []
	event = ''
 
	def __init__(self, params, event):
		self.params = params
		self.event = event
  
	def get_param(self, param, default, target_type=str, use_default_if_blank=False):
		result = default
		try:
			result = self.params[param]
		except (ValueError, KeyError):
			pass

		try:
			result = target_type(result)
		except (ValueError, TypeError) as e:
			allsky_shared.log(4, f'ERROR: Cannot cast "{param}" to {target_type.__name__}. Using default "{default}"')
			result = default
		
		if target_type == str and use_default_if_blank:
			if result == '':
				result = default

		return result
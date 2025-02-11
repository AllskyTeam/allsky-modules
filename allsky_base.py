import allsky_shared as allsky_shared
import os
import json

class ALLSKYMODULEBASE:

	params = []
	event = ''
	metaData = None
 
	def __init__(self, params, event, metaData=None):
		self.params = params
		self.event = event
		self.metaData = metaData
		self.debugmode = self.get_param('ALLSKYTESTMODE', False, bool)
		self.debug_mode = self.debugmode
  
	def get_param(self, param, default, target_type=str, use_default_if_blank=False):
		result = default

		try:
			result = self.params[param]
		except (ValueError, KeyError):
			pass

		if self.metaData is not None:
			if param in self.metaData['argumentdetails']:
				if 'secret' in self.metaData['argumentdetails'][param]:
					env_file = os.path.join(allsky_shared.ALLSKYPATH, 'env.json')
					with open(env_file, 'r', encoding='utf-8') as file:
						env_data = json.load(file)
						env_key = f"{self.metaData['module'].upper()}.{param.upper()}"
						if env_key in env_data:
							result = env_data[env_key]
						else:
							allsky_shared.log(0, f'ERROR: Variable {param} not found in env file. Tried key {env_key}')
   
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
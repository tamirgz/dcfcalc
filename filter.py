

class Filter(object):

	filters = []

	def __init__(self, logger):
		self.logger = logger
		self.filtered = None

	def add_filter(self, new_filter):
		self.filters.append(new_filter)

	def filter(self, df):
		
	
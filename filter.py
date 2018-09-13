

class Filter(object):

	filters = []

	def __init__(self, logger):
		self.logger = logger

	def add_filter(self, new_filter):
		self.filters.append(new_filter)
		self.logger.info("[add_filter] adding filter - %s" % new_filter)

	def filter(self, df, filtered):
		for index, row in df.iterrows():
			for filter in self.filters:
   				if filter == True:
   					filtered = filtered.append(row, sort=False)
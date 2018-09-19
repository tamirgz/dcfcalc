

class Filter(object):

	filters = []

	def __init__(self, logger):
		self.logger = logger

	def add_filter(self, new_filter):
		self.filters.append(new_filter)
		self.logger.info("[add_filter] adding filter - %s" % new_filter)

	def filter(self, data):	
		filtered = data
		# for index, row in data.iterrows():
		for condition in self.filters:
			self.logger.info("condition: %s" % condition)
			exec(condition) # each condition looks like: cond = data["..."] <=> value
			# if cond == True:
			# 	filtered = filtered.append(row, sort=False)
			self.logger.info("LAL")
		return 
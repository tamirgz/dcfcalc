import numpy as np

class Filter(object):

	def __init__(self, logger, filter_name):
		self.logger = logger
		self.name = filter_name
		self.filters = []

	def add_filter(self, new_filter):
		self.filters.append(new_filter)
		self.logger.info("[add_filter][%s] adding filter - %s" % (self.name,new_filter))

	def filter(self, data):
		filtered = data
		for condition in self.filters:
			self.logger.info("[filter][%s] condition --> %s" % (self.name, condition))
			exec(condition) # each condition looks like: cond = data["..."] <=> value
			false_idx = np.where(cond == False)[0]
			filtered = filtered.drop(false_idx)
			filtered = filtered.reset_index(drop = True)
		return filtered
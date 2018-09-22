import numpy as np

class Filter(object):

	filters = []

	def __init__(self, logger):
		self.logger = logger

	def add_filter(self, new_filter):
		self.filters.append(new_filter)
		self.logger.info("[add_filter] adding filter - %s" % new_filter)

	def filter(self, data):
		filtered = data
		for condition in self.filters:
			self.logger.info("[filter] condition --> %s" % condition)
			tmp = condition
			exec(condition) # each condition looks like: cond = data["..."] <=> value
			false_idx = np.where(cond == False)[0]
			filtered = filtered.drop(false_idx)
			filtered = filtered.reset_index(drop = True)
			import pdb; pdb.set_trace()
			print(tmp)
		return filtered
import pickle

class Persistor(object):
	def __init__(self, path: str):
		self.path = path
	def persist(self, obj: object):
		with open(self.path, 'wb') as f:
			pickle.dump(obj, f)
	def load(self):
		with open(self.path, 'rb') as f:
			return pickle.load(f)
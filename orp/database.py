
class Incrementer(object):
	def __init__(self, initial_value: int = 0):
		self.value = initial_value
	def __call__(self):
		value = self.value
		self.value = value + 1
		return value

class PrimaryKey(object):
	def __init__(self, key):
		self.key = key
	def __get__(self, instance, owner):
		if instance is None:
			return self.key
		if isinstance(self.key, tuple):
			return tuple(getattr(instance, key) for key in self.key)
		return getattr(instance, self.key)

class Model(object):
	primary_key = PrimaryKey('id')
	_incrementer = Incrementer()
	def __eq__(self, other):
		return isinstance(other, self.__class__) and self.primary_key == other.primary_key
	def __hash__(self):
		return hash((self.__class__, self.primary_key))
	def __repr__(self):
		return '{}({})'.format(self.__class__.__name__, self.primary_key)
	@classmethod
	def _new_with_primary_key(cls, value):
		obj = cls.__new__(cls)
		try:
			if isinstance(cls.primary_key, tuple):
				for key, new_value in zip(cls.primary_key, value):
					setattr(obj, key, new_value)
			else:
				setattr(obj, cls.primary_key, value)
		except Exception as e:
			print(type(obj), cls.primary_key, value, dir(obj), obj.__dict__)
			raise e
		return obj
	def __reduce__(self):
		return (
			self._new_with_primary_key,
			(self.primary_key,),
			(
				{key: self.__dict__[key] for key in self.__dict__ if not key in self.__class__.primary_key}
				if isinstance(self.__class__.primary_key, tuple) else
				{key: self.__dict__[key] for key in self.__dict__ if not key == self.__class__.primary_key}
			)
		)

class Table(object):
	def __init__(self):
		self._dict = dict()
	def insert(self, item):
		self._dict.__setitem__(item.primary_key, item)
	def values(self):
		return self._dict.values()
	def __getitem__(self, item):
		return self._dict.__getitem__(item)
	def __contains__(self, item):
		return self._dict.__contains__(item)
	def __repr__(self):
		return self._dict.__repr__()
	def __len__(self):
		return self._dict.__len__()
	def __iter__(self):
		return self._dict.__iter__()

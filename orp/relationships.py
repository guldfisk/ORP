import typing as t

T = t.TypeVar('T')

class ManyToMany(set):
	def __init__(self, owner, target_field: str):
		super(ManyToMany, self).__init__()
		self.owner = owner
		self.target_field = target_field
	def add_no_cascade(self, one: T):
		super(ManyToMany, self).add(one)
	def add(self, one: T):
		getattr(one, self.target_field).add_no_cascade(self.owner)
		self.add_no_cascade(one)
	def update(self, other: t.Iterable[T]):
		for item in other:
			self.add(item)
	def remove_no_cascade(self, one: T):
		super(ManyToMany, self).remove(one)
	def remove(self, one: T):
		getattr(one, self.target_field).remove_no_cacade(self.owner)
		self.remove_no_cascade(one)

class ManyToOne(set):
	def __init__(self, owner, target_field: str):
		super(ManyToOne, self).__init__()
		self.owner = owner
		self.target_field = target_field
	def add_no_cascade(self, one: T):
		super(ManyToOne, self).add(one)
	def add(self, one: T):
		getattr(one, self.target_field).set(self.owner)
		self.add_no_cascade(one)
	def update(self, other: t.Iterable[T]):
		for item in other:
			self.add(item)
	def remove_no_cascade(self, one: T):
		super(ManyToOne, self).remove(one)
	def remove(self, one: T):
		getattr(one, self.target_field).disjoint()
		self.remove_no_cascade(one)

class OneToMany(object):
	def __init__(self, owner, target_field: str, initial_value: T = None):
		self.owner = owner
		self.target_field = target_field
		self._one = None
		self.set(initial_value)
	def get(self) -> T:
		return self._one
	def set(self, many: T):
		if self._one is not None:
			getattr(self._one, self.target_field).remove_no_cascade(self.owner)
		if many is not None:
			getattr(many, self.target_field).add_no_cascade(self.owner)
		self._one = many
	def disjoint(self):
		self.set(None)

class OneToManyDescriptor(object):
	def __init__(self, field: str):
		self.field = field
	def __get__(self, instance, owner):
		return getattr(instance, self.field).get()
	def __set__(self, instance, value):
		getattr(instance, self.field).set(value)

# class User(object):
# 	def __init__(self):
# 		self.roles = ManyToMany(self, 'users')
#
# class Role(object):
# 	def __init__(self):
# 		self.users = ManyToMany(self, 'roles')
#
# class Artist(object):
# 	def __init__(self):
# 		self.cards = ManyToOne(self, '_artist')
#
# class Card(object):
# 	def __init__(self, artist: Artist = None):
# 		self._artist = OneToMany(self, 'cards', artist)
# 	artist = OneToManyDescriptor('_artist')

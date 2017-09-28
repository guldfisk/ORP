import typing as t

from abc import ABCMeta, abstractmethod

T = t.TypeVar('T')

class Relationship(object):
	def __init__(self, owner, target_field: str):
		self._owner = owner
		self.target_field = target_field
	@property
	def owner(self):
		return self._owner
	@staticmethod
	def from_owner(owner):
		return owner

# class Gathering(object):
# 	def __init__(self):
# 		self.members = set()
# 	def join(self, member):
# 		self.members.add(member)
# 	def leave(self, member):
# 		self.members.remove(member)
#
# class Group(Relationship):
# 	def __init__(self, owner, target_field: str, initial_group=None):
# 		super().__init__(owner, target_field)
# 		self._group = None
# 		if initial_group is not None:
# 			self.join(initial_group)
# 	def join_no_cascade(self, group):
# 		self._group = group
# 		group.join(self.owner)
# 	def join(self, group):
# 		other_group = getattr(self.from_owner(group), self.target_field)
# 		if other_group._group is None:
# 			other_group.join_no_cascade(Gathering())
# 		if self._group is not None:
# 			self._group.leave(self.owner)
# 		self.join_no_cascade(other_group._group)
# 	def leave(self):
# 		self._group.leave(self.owner)
# 		self._group = None
# 	def __repr__(self):
# 		if self._group is None:
# 			return set().__repr__()
# 		return (self._group.members - {self.owner}).__repr__()
# 	def __iter__(self):
# 		if self._group is not None:
# 			return (self._group.members - {self.owner}).__iter__()

class AbstractCollection(metaclass=ABCMeta):
	@abstractmethod
	def add(self, element):
		pass
	@abstractmethod
	def remove(self, element):
		pass
	@abstractmethod
	def __iter__(self):
		pass
	@abstractmethod
	def __len__(self):
		pass

class Many(Relationship):
	def __init__(self, owner, target_field: str, container_type = set):
		super().__init__(owner, target_field)
		self._many = container_type()
	def join_with(self, one: T):
		self._many.add(one)
	def add(self, one: T):
		getattr(self.from_owner(one), self.target_field).join_with(self.owner)
		self.join_with(one)
	def update(self, other: t.Iterable[T]):
		for item in other:
			self.add(item)
	def disjoint_with(self, one: T):
		self._many.remove(one)
	def remove(self, one: T):
		getattr(self.from_owner(one), self.target_field).join_with(None)
		self.disjoint_with(one)
	def __repr__(self):
		return self._many.__repr__()
	def __iter__(self):
		return self._many.__iter__()
	def __bool__(self):
		return bool(self._many)
	def __len__(self):
		return self._many.__len__()

class One(Relationship):
	def __init__(self, owner, target_field: str, initial_value: T = None):
		super().__init__(owner, target_field)
		self._one = None
		self.set(initial_value)
	def get(self) -> T:
		return self._one
	def join_with(self, many: T):
		self._one = many
	def disjoint_with(self, many: T):
		self._one = None
	def set(self, many: T):
		if self._one is not None:
			getattr(self.from_owner(self._one), self.target_field).disjoint_with(self.owner)
		if many is not None:
			getattr(self.from_owner(many), self.target_field).join_with(self.owner)
		self.join_with(many)

class DummyOne(object):
	def __init__(self, initial_value: T = None):
		self._one = None
		self.set(initial_value)
	def get(self) -> T:
		return self._one
	def set(self, value: T):
		self._one = value

class OneDescriptor(object):
	def __init__(self, field: str):
		self.field = field
	def __get__(self, instance, owner):
		return getattr(instance, self.field).get()
	def __set__(self, instance, value):
		getattr(instance, self.field).set(value)

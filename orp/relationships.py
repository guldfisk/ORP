import typing as t

from abc import ABCMeta, abstractmethod


T = t.TypeVar('T')


class Relationship(t.Generic[T], metaclass=ABCMeta):

	def __init__(self, owner, target_field: str):
		self._owner = owner
		self.target_field = target_field

	@property
	def owner(self):
		return self._owner

	@staticmethod
	def from_owner(owner):
		return owner

	@abstractmethod
	def join_with(self, one: T) -> None:
		pass

	@abstractmethod
	def disjoint_with(self, one: T) -> None:
		pass


class Many(Relationship, t.AbstractSet[T]):

	def __init__(self, owner, target_field: str):
		super().__init__(owner, target_field)
		self._many = set() #type: t.Set[T]

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

	def __repr__(self) -> str:
		return self._many.__repr__()

	def __iter__(self) -> t.Iterator[T]:
		return self._many.__iter__()

	def __bool__(self) -> bool:
		return bool(self._many)

	def __len__(self) -> int:
		return self._many.__len__()

	def __contains__(self, item) -> bool:
		return self._many.__contains__(item)

	def __sub__(self, other) -> t.AbstractSet[T]:
		return self._many.__sub__(other)

	def __or__(self, other) -> t.AbstractSet:
		return self._many.__or__(other)


class ListMany(Relationship, t.List[T]):

	def __init__(self, owner, target_field: str):
		super().__init__(owner, target_field)
		self._many = [] #type: t.List[T]

	def join_with(self, one: T):
		self._many.append(one)

	def add(self, one: T):
		getattr(self.from_owner(one), self.target_field).join_with(self.owner)
		self.join_with(one)

	def disjoint_with(self, one: T):
		self._many.remove(one)

	def remove(self, one: T):
		getattr(self.from_owner(one), self.target_field).join_with(None)
		self.disjoint_with(one)

	def clear(self) -> None:
		for item in list(self._many):
			self.remove(item)

	def append(self, one: T) -> None:
		self.add(one)

	def extend(self, ones: t.Iterable[T]) -> None:
		for one in ones:
			self.add(one)

	def __len__(self) -> int:
		return self._many.__len__()

	def __iter__(self) -> t.Iterator[T]:
		return self._many.__iter__()

	def __getitem__(self, i: int) -> T:
		return self._many.__getitem__(i)

	def __contains__(self, one: T) -> bool:
		return self._many.__contains__(one)


class One(Relationship, t.Generic[T]):

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

	def set(self, many: T, ignore_previous_value = False):
		if self._one is not None and not ignore_previous_value:
			getattr(self.from_owner(self._one), self.target_field).disjoint_with(self.owner)
		if many is not None:
			getattr(self.from_owner(many), self.target_field).join_with(self.owner)
		self.join_with(many)


class OneDescriptor(t.Generic[T]):

	def __init__(self, field: str):
		self.field = field

	def __get__(self, instance, owner) -> T:
		return getattr(instance, self.field).get()

	def __set__(self, instance, value: T):
		getattr(instance, self.field).set(value)

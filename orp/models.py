from __future__ import annotations

import typing as t
from abc import abstractmethod
from itertools import chain

from orp import relationships as _relationships


class Incrementer(object):

    def __init__(self, initial_value: int = 0):
        self.value = initial_value

    def __call__(self):
        value = self.value
        self.value = value + 1
        return value


class Key(object):

    def __init__(
        self,
        target: str,
        calc_value: t.Callable[[Key, Model, dict], t.Any] = None,
        input_values: t.Iterable[str] = None,
    ):
        self._target = target
        self.calc_value = calc_value
        self.input_values = input_values

    @property
    def target(self):
        return self._target

    @property
    def private_target(self):
        return '_' + self._target

    def __repr__(self):
        return self._target


class PrimaryKey(object):

    def __init__(self, keys: t.Union[t.Tuple[t.Union[Key, str], ...], Key, str]):
        self.key = (
            tuple(item if isinstance(item, Key) else Key(item) for item in keys)
            if isinstance(keys, tuple) else
            keys if isinstance(keys, Key) else Key(keys)
        )

    def __get__(self, instance, owner):
        if instance is None:
            return self.key

        if isinstance(self.key, tuple):
            return tuple(
                getattr(instance, key.target) for key in self.key
            )

        return getattr(instance, self.key.target)


class ForeignKey(Key):

    def __init__(self, target: str, foreign_target: str):
        super().__init__(target)
        self._foreign_target = foreign_target

    @property
    @abstractmethod
    def relationship(self):
        pass

    @property
    def foreign_target(self):
        return self._foreign_target


class ForeignOne(ForeignKey):

    @property
    def relationship(self):
        return _relationships.One


def _unlinked_foreign_new(cls, key_map):
    obj = object.__new__(cls)
    keys = (
        cls.primary_key
        if isinstance(cls.primary_key, tuple) else
        (cls.primary_key,)
    )

    for key in keys:
        if isinstance(key, ForeignOne):
            setattr(
                obj,
                key.private_target,
                key.relationship(
                    obj,
                    key.foreign_target,
                )
            )
            try:
                getattr(obj, key.private_target).join_with(key_map[key.target])
            except KeyError:
                getattr(obj, key.private_target).join_with(key.calc_value(key, obj, key_map))
        else:
            try:
                setattr(obj, key.private_target, key_map[key.target])

            except KeyError:
                setattr(obj, key.private_target, key.calc_value(key, obj, key_map))

    return obj


class OrpBase(object):

    @property
    @abstractmethod
    def primary_key(self) -> t.Union[str, int]:
        pass

    def __hash__(self):
        return hash(self.primary_key)

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__)
            and self.primary_key == other.primary_key
        )


class Model(OrpBase):
    primary_key = PrimaryKey(
        Key('id', calc_value = lambda k, o, m: o._INCREMENTER()),
    )
    _INCREMENTER = Incrementer()

    def __new__(cls, *args, **kwargs):
        keys = (
            cls.primary_key
            if isinstance(cls.primary_key, tuple) else
            (cls.primary_key,)
        )

        for key, arg in zip(
            chain(
                *(
                    (filtered_key.target,)
                    if filtered_key.input_values is None else
                    filtered_key.input_values
                    for filtered_key in keys
                    if filtered_key.calc_value is None or filtered_key.input_values is not None
                )
            ),
            args,
        ):
            kwargs[key] = arg

        obj = _unlinked_foreign_new(cls, kwargs)

        for key in keys:
            if isinstance(key, ForeignKey):
                try:
                    getattr(obj, key.private_target).set(
                        kwargs[key.target],
                        ignore_previous_value = True,
                    )
                except KeyError:
                    getattr(obj, key.private_target).set(
                        key.calc_value(key, obj, kwargs),
                        ignore_previous_value = True,
                    )

        return obj

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__)
            and self.primary_key == other.primary_key
        )

    def __hash__(self):
        return hash(self.primary_key)

    def __repr__(self):
        return f'{self.__class__.__name__}({self.primary_key})'

    def __reduce__(self):
        return (
            _unlinked_foreign_new,
            (
                self.__class__,
                {
                    key.target: getattr(self, key.target)
                    for key in
                    self.__class__.primary_key
                }
                if isinstance(self.__class__.primary_key, tuple) else
                {
                    self.__class__.primary_key.target: getattr(self, self.__class__.primary_key.private_target),
                },
            ),
            self.__dict__,
        )

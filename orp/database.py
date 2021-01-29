from __future__ import annotations

import datetime
import typing as t
import hashlib
from abc import abstractmethod

from orp.models import OrpBase, Model


K = t.TypeVar('K')
O = t.TypeVar('O', bound = OrpBase)
M = t.TypeVar('M', bound = Model)


class OrpTable(t.Generic[K, O]):

    @abstractmethod
    def __getitem__(self, item: K) -> O:
        pass

    @abstractmethod
    def __iter__(self) -> t.Iterator[K]:
        pass

    @abstractmethod
    def __contains__(self, item: K) -> bool:
        pass

    def get(self, key: K, default: t.Optional[O] = None) -> t.Optional[O]:
        try:
            return self[key]
        except KeyError:
            return default

    @abstractmethod
    def items(self) -> t.Iterator[t.Tuple[K, O]]:
        pass

    @abstractmethod
    def values(self) -> t.Iterator[O]:
        pass

    @abstractmethod
    def keys(self) -> t.Iterator[K]:
        pass

    @abstractmethod
    def insert(self, item: O) -> None:
        pass


class PickleTable(t.Dict[K, M], OrpTable[K, M]):

    def insert(self, item: M) -> None:
        self.__setitem__(item.primary_key, item)


class OrpDatabase(t.Generic[O]):
    _tables: t.Dict[t.Type[O], OrpTable]

    @classmethod
    def _calc_checksum(cls, values: t.Sequence[t.Tuple[t.Type[O], t.Sequence[t.Union[str, int]]]]) -> bytes:
        hasher = hashlib.sha256()
        for model_type_name, keys in sorted(
            (
                (model_type.__name__, sorted(keys))
                for model_type, keys in
                values
            )
        ):
            hasher.update(model_type_name.encode('utf-8'))
            for k in keys:
                if isinstance(k, str):
                    hasher.update(k.encode('utf-8'))
                else:
                    hasher.update(k.to_bytes(4, 'big'))

        return hasher.digest()

    def calc_checksum(self):
        return self._calc_checksum(
            [
                (
                    model,
                    list(table.keys()),
                ) for model, table in
                self._tables.items()
            ]
        )

    @property
    @abstractmethod
    def created_at(self) -> datetime.datetime:
        pass

    @property
    @abstractmethod
    def checksum(self) -> bytes:
        pass

    def __getitem__(self, model: t.Type[O]) -> OrpTable[t.Any, O]:
        return self._tables.__getitem__(model)

    def __iter__(self) -> t.Iterable[OrpTable]:
        return self._tables.values()

    def __copy__(self):
        return self

    def __deepcopy__(self, memodict):
        return self


class PickleDatabase(OrpDatabase[M]):

    def __init__(self, tables: t.Dict[t.Type[M], PickleTable], created_at: t.Optional[datetime.datetime] = None):
        self._tables = tables
        self._created_at = datetime.datetime.now() if created_at is None else created_at

        self._checksum = self.calc_checksum()

    @property
    def created_at(self) -> datetime.datetime:
        return self._created_at

    @property
    def checksum(self) -> bytes:
        return self._checksum

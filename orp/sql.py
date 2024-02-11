import datetime
import typing as t

from sqlalchemy import Column, DateTime, Integer, LargeBinary, MetaData, Table, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from orp.database import B, K, OrpDatabase, OrpTable


class SqlTable(OrpTable[K, B]):
    def __init__(self, model: object, session_factory: t.Callable[[], Session]):
        self._model = model
        self._session_factory = session_factory

        self._pk = self._model.__mapper__.primary_key[0]

    def __getitem__(self, item: K) -> B:
        _item = self._session_factory().query(self._model).get(item)
        if _item is None:
            raise KeyError(item)
        return _item

    def __contains__(self, item: K) -> bool:
        return self._session_factory().query(self._pk).filter(self._pk == item).scalar() is not None

    def __iter__(self) -> t.Iterator[K]:
        return self._session_factory().query(self._pk).order_by(self._pk).__iter__()

    def items(self) -> t.Iterator[t.Tuple[K, B]]:
        return self._session_factory().query(self._pk, self._model).order_by(self._pk).__iter__()

    def values(self) -> t.Iterator[B]:
        return self._session_factory().query(self._model).order_by(self._pk)

    def keys(self) -> t.Iterator[K]:
        return (vs[0] for vs in self._session_factory().query(self._pk).order_by(self._pk))

    def insert(self, item: B) -> None:
        self._session_factory().add(item)


metadata = MetaData()

meta_info = Table(
    "meta",
    metadata,
    Column("version", Integer, primary_key=True),
    Column("created_at", DateTime),
    Column("checksum", LargeBinary(256)),
)


class SqlDatabase(OrpDatabase[B]):
    def __init__(self, tables: t.Dict[t.Type[B], SqlTable], engine: Engine):
        self._tables = tables
        self._engine = engine

    @property
    def created_at(self) -> datetime.datetime:
        with self._engine.connect() as connection:
            return connection.execute(
                select([meta_info.c.created_at]).order_by(meta_info.c.version.desc()).limit(1)
            ).fetchone()[0]

    @property
    def checksum(self) -> bytes:
        with self._engine.connect() as connection:
            return connection.execute(
                select([meta_info.c.checksum]).order_by(meta_info.c.version.desc()).limit(1)
            ).fetchone()[0]

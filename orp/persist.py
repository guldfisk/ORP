import pickle
from abc import ABCMeta, abstractmethod


class Persistor(metaclass=ABCMeta):

    @abstractmethod
    def save(self, obj):
        pass

    @abstractmethod
    def load(self):
        pass


class PicklePersistor(Persistor):

    def __init__(self, path: str):
        self.path = path

    def save(self, obj: object):
        with open(self.path, 'wb') as f:
            pickle.dump(obj, f)

    def load(self):
        with open(self.path, 'rb') as f:
            return pickle.load(f)
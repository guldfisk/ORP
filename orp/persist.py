import copyreg
import pickle
import types
from abc import ABCMeta, abstractmethod


try:
    import cPickle
except ImportError:
    cPickle = None

if cPickle is None or cPickle.PicklingError is pickle.PicklingError:
    _UniversalPicklingError = pickle.PicklingError
else:

    class _UniversalPicklingError(pickle.PicklingError, cPickle.PicklingError):
        pass


def named_any(name):
    if not name:
        raise Exception("Empty module name")

    names = name.split(".")

    if "" in names:
        raise Exception("invalid path")

    top_level_package = None
    module_names = names[:]
    while not top_level_package:
        trial_name = ".".join(module_names)
        top_level_package = __import__(trial_name)

    obj = top_level_package
    for n in names[1:]:
        obj = getattr(obj, n)

    return obj


def pickle_method(method):
    return (
        unpickle_method,
        (
            method.__name__,
            method.__self__,
            method.__self__.__class__,
        ),
    )


def _method_function(class_object, method_name):
    return getattr(class_object, method_name)


def unpickle_method(im_name, im_self, im_class):
    if im_self is None:
        return getattr(im_class, im_name)
    try:
        method_function = _method_function(im_class, im_name)
    except AttributeError:
        assert im_self is not None, "No recourse: no instance to guess from."
        if im_self.__class__ is im_class:
            raise
        return unpickle_method(im_name, im_self, im_self.__class__)
    else:
        maybe_class = ()
        bound = types.MethodType(method_function, im_self, *maybe_class)
        return bound


def pickle_function(f):
    if f.__name__ == "<lambda>":
        raise _UniversalPicklingError("Cannot pickle lambda function: {}".format(f))
    return (_unpickle_function, tuple([".".join([f.__module__, f.__qualname__])]))


def _unpickle_function(fully_qualified_name):
    return named_any(fully_qualified_name)


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
        copyreg.pickle(types.MethodType, pickle_method, unpickle_method)
        copyreg.pickle(types.FunctionType, pickle_function, _unpickle_function)

        with open(self.path, "wb") as f:
            pickle.dump(obj, f)

    def load(self):
        with open(self.path, "rb") as f:
            return pickle.load(f)

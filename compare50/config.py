import abc

_configs = {}
_default = "win_strip_all"


def register(config):
    global _default
    if not _default:
        _default = config.id()

    _configs[config.id()] = config


def get(id=None):
    if id is None:
        id = _default
    return _configs[id]


def all():
    return list(_configs.values())


class Compare50Config(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def id(self):
        pass

    @abc.abstractmethod
    def description(self):
        pass

    @abc.abstractmethod
    def preprocessors(self):
        pass

    @abc.abstractmethod
    def comparator(self):
        pass

import abc

_configs = {}
_default = None


def register(config):
    global _default
    if not _default:
        _default = config.name()

    _configs[config.name()] = config


def get(name=None):
    if name is None:
        name = _default
    return _configs[name]


def list():
    return list(_configs.keys())


class Compare50Config(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def name(self):
        pass

    @abc.abstractmethod
    def preprocessors(self):
        pass

    @abc.abstractmethod
    def comparator(self):
        pass

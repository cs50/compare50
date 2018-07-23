import abc

def get(name=None):
    if name is None:
        name = PassRegistry.default
    return PassRegistry.passes[name]


def get_all():
    return list(PassRegistry.passes.values())


class PassRegistry(abc.ABCMeta):
    default = "StripAll"
    passes = {}
    def __new__(mcls, name, bases, attrs):
        cls = abc.ABCMeta.__new__(mcls, name, bases, attrs)

        if attrs.get("_{}__register".format(name), True):
            if not PassRegistry.default:
                PassRegistry.default = cls
            PassRegistry.passes[name] = cls

        return cls


class Pass(metaclass=PassRegistry):

    __register = False

    @property
    @abc.abstractmethod
    def description(self):
        pass

    @property
    @abc.abstractmethod
    def preprocessors(self):
        pass

    @property
    @abc.abstractmethod
    def comparator(self):
        pass

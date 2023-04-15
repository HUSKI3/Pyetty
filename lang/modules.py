import pprint

from lang.exceptions import ModuleExceptions, TranspilerExceptions

from .lexer import PyettyLexer
from .pparser import PyettyParser
from .types import *
pprint = pprint.PrettyPrinter(indent=2).pprint
from rich.console import Console
from rich.syntax import Syntax
console = Console()

def rprint(data):
    console.print(
        Syntax(
            str(data),
            "Python", 
            padding=1, 
            line_numbers=True
        )
    )

class Module:
    BUILT_TYPE = str
    class MODULE_TYPES:
        '''
        FUNCTION -> Function module type
        ACTION   -> Internal action used in processing
        '''
        FUNCTION = "Function" 
        ACTION   = "Action"
        SPECIAL_ACTION = "Special Action"
        SPECIAL_ACTION_FUNC = "Special Action Function"

    def __init__(
        self,
        #type: MODULE_TYPES
    ):
        self.type = "Unknown"
        self.built = ""
        self.template = ""
        self.o1 = False
        self.o2 = False
        self.o3 = False

    def __call__(
        self,
        tree,
        no_construct = False
    ):

        _values = self.proc_tree(tree)
        self.override()
        return _values
    
    # Future
    #def optimise(self): pass
    optimise = None

    # Future: Return true for now
    def verify(self): return True

    def override(self):
        """
        Warning: this should be used with caution since it bypasses the default build structure
        """
        pass

    # Implemented in module child
    def proc_tree(self, tree) -> dict: "Return a dict containing values processed from the tree"

    # Format
    def _constructor(
        self,
        arguments: dict
    ) -> BUILT_TYPE:
        if arguments == None:
            raise ModuleExceptions.InvalidModuleConstruction(self)
        try:
            return self.template.format(
                    **arguments
                )
        except Exception:
            raise Exception(f"In '{self.name}' - Failed to unpack elements. Perhaps you need to set `no_construct` to True to avoid this module's construction?")
    
class ResolutionMod(Module):
    name="RESOLUT"
    type = Module.MODULE_TYPES.ACTION

    def __init__(self, compiler_instance):
        super().__init__()
        self.compiler_instance = compiler_instance
    
    def proc_tree(self, tree):
        #pprint(tree)
        
        if tree[0] == 'STRING':
            return String(tree[1]['VALUE'])

        elif tree[0] == 'INT':
            return Int32(tree[1]['VALUE'])

        elif tree[0] == 'HEX':
            return HexInt32(tree[1]['VALUE'])

        elif tree[0] == 'CHAR':
            # if the actual type is string, there will be an array in place of the value
            if type(tree[1]['VALUE']) == tuple:
                return Char(tree[1]['VALUE'][0])
            else:
                return Char(tree[1]['VALUE'])
        
        elif tree[0] == 'ID':

            return ID(tree[1]['VALUE'])

        raise Exception(f"[RESOLUT] Failed to match {tree} is '{tree[0]}' supported?")
    
class FunctionCallMod(Module):
    name="FUNCTION_CALL"
    type = Module.MODULE_TYPES.SPECIAL_ACTION

    def __init__(self, compiler_instance):
        super().__init__()
        self.template_new = "{var} := {value}"
        self.template_assign = "{var} = {value}"
        self.compiler_instance = compiler_instance

    def proc_tree(self, tree):
        # Dependencies
        resolution_module: Module = self.compiler_instance.get_action('RESOLUT')

        if tree['ID'][0] == 'CLASS_ATTRIBUTE':
            # We assume it's part of a namespace
            namespace = tree['ID'][1]['CLASS'][1]['VALUE']
            arguments = tree['FUNCTION_ARGUMENTS']
            funcname = tree['ID'][1]['ATTRIBUTE']
        else:
            funcname = tree['ID'][1]['VALUE']
            arguments = tree['FUNCTION_ARGUMENTS']
            namespace = None

        parsed_args = [
            resolution_module(arg)
            for arg in arguments['POSITIONAL_ARGS']
        ]

        console.log(f"[FunctionCallMod] {funcname}({parsed_args}) from {namespace}")

        if namespace == 'v':
            # We assume it's a builtin!
            done = f"{funcname}({', '.join([arg.value for arg in parsed_args])})"
        
        return done

class VariableAssignMod(Module):
    name="VARIABLE_ASSIGNMENT"
    type = Module.MODULE_TYPES.SPECIAL_ACTION

    def __init__(self, compiler_instance):
        super().__init__()
        self.template_new = "{var} := {value}"
        self.template_assign = "{var} = {value}"
        self.compiler_instance = compiler_instance

    def proc_tree(self, tree):
        # Dependencies
        resolution_module: Module = self.compiler_instance.get_action('RESOLUT')

        expr = tree['EXPRESSION']
        var  = tree['ID']
        vartype = tree['TYPE']

        print(f"[{var}: {vartype}] -> {expr}")

        types = {
            'int': Int32,
            'hex': HexInt32,
            'char': Char,
            'string': String
        }

        special_types = {
            'list': List,
            'id': ID
        }

        if vartype not in types and vartype not in special_types:
            raise TranspilerExceptions.UnkownType(vartype)
        
        resolved = resolution_module(expr, no_construct=True)

        if type(resolved) != types[vartype]:
            raise TranspilerExceptions.TypeMissmatch(var, type(resolved), types[vartype], self.compiler_instance.line)
        
        if var not in self.compiler_instance.variables:
            # We create a new variable
            done = self.template_new.format(
                var = var,
                value = resolved.value
            )
        else:
            # We assign to an existing variable
            done = self.template_assign.format(
                var = var,
                value = resolved.value
            )
        
        return done
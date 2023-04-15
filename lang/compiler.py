


from lang.exceptions import TranspilerExceptions
from .modules import Module
from rich import print as rprint

class Compiler:
    def __init__(
            self,
            tree,
            actions = {}
    ):
        self.code = tree
        self.actions = actions 
        self._modules = {}
        self.line = 0
        self.variables = {}
        self.finished = []
        self.finished_funcs = []
    
    def populate_modules_actions(
        self,
        Modules: list[Module]
    ) -> None:
        self.raw_modules = Modules
        for module in Modules:
            modobj: Module = module(self)
            modobj.type = module.type
            if modobj.type == Module.MODULE_TYPES.FUNCTION:
                self.functions[module.name] = modobj
            else:
                self.actions[module.name] = modobj

            self._modules[module.name] = modobj
    
    def get_action(
        self,
        name
    ) -> Module:
        if name in self.actions:
            return self.actions[name]
        else:
            print(f"At {self.line}")
            raise TranspilerExceptions.ActionRequiredButNotFound(name, self.actions)

    def run(self, code=None):
        if code is None:
            code = self.code
        else:
            code = code
        for action in code:
            if action[0] in self.actions:
                ret = self.actions[action[0]](action[1])
                if self.actions[action[0]].type == Module.MODULE_TYPES.SPECIAL_ACTION:
                    self.finished.append(ret)
                elif self.actions[action[0]].type == Module.MODULE_TYPES.SPECIAL_ACTION_FUNC:
                    self.finished_funcs.append(ret)
            else:
                raise TranspilerExceptions.UnknownActionReference(action[0])
            self.line += 1

    def pause(self):
        rprint("[yellow bold]Compilation paused. Press enter to continue[/yellow bold]")
        input()

    def get_variable(
        self,
        name: str
    ) -> dict:
        if name in self.variables:
            return self.variables[name]
        else:
            print(f"At {self.line}")
            raise TranspilerExceptions.UnkownVar(name, self.variables)

    def create_variable(
        self,
        name: str, 
        type,
        obj,
        force = False
    ) -> None:
        if name in self.variables and not force:
            print(f"At {self.line}")
            raise TranspilerExceptions.VarExists(name)
        
        self.variables[name] = {
                "type": type,
                "object": obj
            }
# Pretty-print
import os
from rich import print
from rich.console import Console

from lang.compiler import Compiler
console = Console()
from rich.syntax import Syntax
from rich.progress import Progress

# Parser and lexer
from lang.lexer import PyettyLexer
from lang.pparser import PyettyParser
from rich.traceback import install
install()

# Load modules
from lang.modules import (
    Module,
    VariableAssignMod,
    ResolutionMod,
    FunctionCallMod
)

### Args proc ###
from sys import argv
flags = ''
if len(argv) < 2: 
    raise Exception("Usage: python3 p <input>")
#################

### Read file ###
text = open(argv[1],"r").read()
#################

### Construct tree ###
lexer = PyettyLexer()
parser = PyettyParser()
######################

### Tasks ###

# Works only on functions that support tasks
def construct_task(
    progress, 
    task,
    target,
    *args,
    tasklen = 100
):
    def _run_task():
        return target(
            *args,
            task = task,
            progress = progress,
            tasklen = tasklen
        )
    return _run_task

with Progress(
    refresh_per_second = 100
) as total_progress:
    # Lex 
    lex = total_progress.add_task("Lex...", total=100)
    lexed_tokens = lexer.tokenize(text)
    # Increases time it takes, but makes it possible to track tree building
    lexed_len    = len(list(lexer.tokenize(text)))
    total_progress.update(lex, advance=100)

    # Build tree task
    build_tree = total_progress.add_task("Building tree...", total=1000)
    build_tree_task = construct_task(
        total_progress,
        build_tree,
        parser.parse,
        lexed_tokens,
        tasklen = lexed_len
    )

    tree = build_tree_task()
    # Force finish
    total_progress.update(build_tree, advance=1000)

print(f"\n[bold green]Tree complete, translating...[/bold green]")

compiler = Compiler(tree)
compiler.populate_modules_actions(
    [
        VariableAssignMod,
        ResolutionMod,
        FunctionCallMod
    ]
)
compiler.run()

pyetty_out_pretty = Syntax(
                    '\n'.join(compiler.finished),
                    "v",
                    padding=1, 
                    line_numbers=True
                )
print(pyetty_out_pretty)

print(f"\n[bold green]Source complete, compiling...[/bold green]")
with open("out.v", "w+") as out:
    out.write('\n'.join(compiler.finished))
os.system(f"v crun out.v")
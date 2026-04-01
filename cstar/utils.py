

from dataclasses import dataclass
from types import NoneType
from tatsu.contexts import closure


@dataclass(frozen=True)
class C_return:
    base : list[str]
    pointer : int = 0
    
    def __str__(self):
        s = ' '.join([x.strip() for x in self.base])
        if self.pointer:
            s += ' ' + ('*' * self.pointer)
        return s

@dataclass(frozen=True)
class OnionFunc:
    name : str
    returns : frozenset[C_return]
    body : str
    bounds : tuple[int, int]
    onion_bounds : tuple[int, int]
    body_bounds : tuple[int, int]
    lines : tuple[int, int]
    filename : str
    declaration : bool
    

@dataclass
class CompilerContext:
    onion_funcs : dict[str, OnionFunc]
    onion_func_names : set[str]
    onion_returns_dict : dict[frozenset[C_return], tuple[str, str]]
    onion_ord_returns_dict : dict[frozenset[C_return], list[C_return]]
    onion_bodies_dict : dict[OnionFunc, str]
    external_headers : set[str]


@dataclass
class TaggedReturn:
    rtype : C_return
    value : str
    bounds : tuple[int, int]
    line : int
    filename : str


@dataclass
class UnwrapDecl:
    symbol : str | NoneType
    name : str
    args : str
    bounds : tuple[int, int]


@dataclass
class UnwrapBranch:
    rtype : C_return
    body : str
    body_bounds : tuple[int, int]

@dataclass
class Unwrap:
    declaration : UnwrapDecl
    branches : list[UnwrapBranch]
    bounds : tuple[int, int]


@dataclass(frozen=True)
class ExternalHeader:
    name : str


def flatten(l : list) -> list:
    flat = []
    for each in l:
        if (type(each) == list) or (type(each) == closure):
            flat += flatten(each)
        else:
            flat.append(each)
    return flat



import typer
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel

console = Console()

def report_error(filename: str, line: int, message: str):
    with open(filename, 'r') as file:
        code_snippet = file.readlines()
    
    code_snippet = code_snippet[max(0, line - 2):min(line + 3, len(code_snippet))]
    code_snippet = '\n'.join(code_snippet)
    
    syntax = Syntax(
        code_snippet, 
        "c", 
        theme="monokai", 
        line_numbers=True, 
        start_line=line,
        highlight_lines={line}
    )

    console.print(Panel(
        syntax, 
        title=f"[bold red]Error: {filename}:{line}[/bold red]",
        subtitle=f"[yellow]{message}[/yellow]",
        expand=True
    ))
    
    raise typer.Exit(1)



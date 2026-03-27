

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
    

@dataclass
class CompilerContext:
    onion_funcs : dict[str, OnionFunc]
    onion_func_names : set[str]
    onion_returns_dict : dict[frozenset[C_return], tuple[str, str]]
    onion_ord_returns_dict : dict[frozenset[C_return], list[C_return]]
    onion_bodies_dict : dict[OnionFunc, str]


@dataclass
class TaggedReturn:
    rtype : C_return
    value : str
    bounds : tuple[int, int]


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



def flatten(l : list) -> list:
    flat = []
    for each in l:
        if (type(each) == list) or (type(each) == closure):
            flat += flatten(each)
        else:
            flat.append(each)
    return flat


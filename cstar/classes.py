from dataclasses import dataclass, field


@dataclass
class FunctionContext:
    return_type : tuple[str, ...]
    var_types : dict[str, str]
    template : tuple[str, ...] | None
    templ_args : str

@dataclass
class MatchCall:
    funcname : str
    params : str
    holder : None | str
    union_type : tuple[str, ...]
    body : str
    rhs : str
    tp : str


@dataclass
class FuncProto:
    name : str
    input_types : tuple[str, ...]
    
    def __hash__(self):
        return self.name.__hash__()


@dataclass
class CompileInfo:
    temp_holders : int = 0
    functions : dict[FuncProto, FunctionContext] = field(default_factory=dict)
    constructed_unions : set[tuple[str, ...]] = field(default_factory=set)
    structs : list[str] = field(default_factory=list)
    current_file : str | None = None



@dataclass
class CodeInfo:
    file_name : str
    line_number : int

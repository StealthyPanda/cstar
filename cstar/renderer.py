
import re
from .utils import *


def get_c_type(rt : C_return) -> str:
    s = ' '.join([x.strip() for x in rt.base])
    if rt.pointer:
        s += ' ' + ('*' * rt.pointer)
    return s

def get_c_alias(rt : C_return) -> str:
    s = '_0_'.join([x.strip() for x in rt.base])
    if rt.pointer:
        s += f'_ptr{str(rt.pointer)}_'
    return s


def get_c_onion(rts : frozenset[C_return], context : CompilerContext) -> tuple[str, str]:
    
    rts_buff = context.onion_ord_returns_dict[rts]
    
    union_name = [get_c_alias(x) for x in rts_buff]
    union_name = '_onion_' + '_1_'.join(union_name)
    
    rts_buff = [x for x in rts_buff if 'void' not in x.base]
    body = [f'\t\t{get_c_type(x)} val_{i};' for i, x in enumerate(rts_buff)]
    body = '\n'.join(body)
    
    render = (
        'typedef struct {\n' +
        '\tu8 flag;\n' +
        '\tunion {\n' +
        body +
        '\n\t};\n' +
        '} ' + union_name + ' ;'
    )
    
    return union_name, render
    




def get_preamble(context : CompilerContext) -> str:
    
    c_unions = context.onion_returns_dict
    
    preamble = ''
    
    for key in c_unions:
        name, body = c_unions[key]
        
        comment = list(key)
        comment = [get_c_type(x) for x in comment]
        comment = ' | '.join(comment)
        comment = f'// C Union for [{comment}]\n'
    
        preamble += '\n' + comment + body + '\n'
    
    preamble = '\n#pragma once\n#include "cstarlib.h"\n\n' + preamble
    
    return preamble


    
    


def render_onions(code : str, ast : list[OnionFunc], context : CompilerContext) -> str:
    
    sections : list[tuple[tuple[int, int], str]] = []
    
    for onion in ast:
        rt, _ = context.onion_returns_dict[onion.returns]
        sections.append((onion.onion_bounds,  rt))
        sections.append((onion.body_bounds,  context.onion_bodies_dict[onion]))
        
    
    sections.sort(key = lambda x: x[0][0])
    
    
    newcode = ''
    prev = 0
    for bounds, rt in sections:
        newcode += code[prev : bounds[0]]
        newcode += rt
        prev = bounds[1]
    
    newcode += code[prev :]
    
    return newcode


def get_c_return_statement(
        value : str,
        c_ret_union : str,
        c_type : C_return, 
        ord : list[C_return]
    ) -> str:
    
    st = '{ '

    ind = ord.index(c_type)

    st += f'{c_ret_union} ret_val; '    
    st += f'ret_val.flag = {ind}; '
    if value.strip():    
        st += f'ret_val.val_{ind} = {value}; '    
    st += f'return ret_val; '
    
    st += ' }'
    
    return st
    
    
    


def render_tagged_returns(
        code : str, 
        ast : list[TaggedReturn], 
        context : CompilerContext, 
        func : OnionFunc
    ) -> str:
    
    sections : list[tuple[tuple[int, int], str]] = []
    
    c_ret_type, _ = context.onion_returns_dict[func.returns]
    
    for tr in ast:
        st = get_c_return_statement(
            tr.value, c_ret_type,
            tr.rtype, context.onion_ord_returns_dict[func.returns]
        )
        
        sections.append((tr.bounds, st))
        
    
    sections.sort(key = lambda x: x[0][0])
    
    
    newcode = ''
    prev = 0
    for bounds, rt in sections:
        newcode += code[prev : bounds[0]]
        newcode += rt
        prev = bounds[1]
    
    newcode += code[prev :]
    
    return newcode
    
    




def replace_c_var(source_code : str, target_var : str, replacement_var : str) -> str:
    # This pattern covers 5 'ignore' cases and 1 'replace' case:
    # 1. Preprocessor directives: #include, #define, etc.
    # 2. Block comments: /* ... */ 
    # 3. Line comments: // ...
    # 4. String literals: " ... "
    # 5. Character literals: ' ... '
    # 6. THE TARGET: \bvar\b
    
    pattern = (
        r'('                               # Group 1: The "Skip" Group
            r'^\s*#.*'                     # Preprocessor lines (starts with #)
            r'|/\*[\s\S]*?\*/'             # Block comments
            r'|//.*'                       # Line comments
            r'|"(?:\\.|[^"\\])*"'          # Strings
            r"|'(?:\\.|[^'\\])*'"          # Character literals
        r')'                               
        r'|'                               # OR
        r'(\b' + re.escape(target_var) + r'\b)'  # Group 2: The actual variable
    )

    def handler(match):
        # If Group 1 (the skip group) has content, return it as-is
        if match.group(1):
            return match.group(1)
        # Otherwise, replace the variable found in Group 2
        return replacement_var

    # We use re.MULTILINE so ^ matches the start of each line for the # check
    return re.sub(pattern, handler, source_code, flags=re.MULTILINE)





def get_branch_body(branch : UnwrapBranch, code : str, symbol : str, ord : list[C_return]) -> str:    
    return replace_c_var(
        code[branch.body_bounds[0] : branch.body_bounds[1]], symbol,
        f'(_unwrap_buffer_.val_{ord.index(branch.rtype)})' 
    )










def get_unwrap(unwrap : Unwrap, code : str, context : CompilerContext) -> str:
    symbol = unwrap.declaration.symbol
    func = context.onion_funcs[unwrap.declaration.name]
    union = context.onion_returns_dict[func.returns][0]
    
    declaration_render = f'{union} _unwrap_buffer_ = {func.name}( {unwrap.declaration.args} );'
    
    branches = []
    for branch in unwrap.branches:
        ind = context.onion_ord_returns_dict[func.returns].index(branch.rtype)
        branches.append(
            f'if (_unwrap_buffer_.flag == {ind}) ' + 
            get_branch_body(
                branch, code,
                symbol, context.onion_ord_returns_dict[func.returns]
            )
        )
    
    branches = ' else '.join(branches)
    
    render = '{ ' + declaration_render + ' ' + branches + ' }'
    
    return render
    
    
    
    


    

def render_unwraps(code : str, ast : list[Unwrap], context : CompilerContext) -> str:
    
    sections : list[tuple[tuple[int, int], str]] = []
    
    for unwrap in ast:
        sections.append((unwrap.bounds, get_unwrap(unwrap, code, context)))
        
    
    sections.sort(key = lambda x: x[0][0])
    
    
    newcode = ''
    prev = 0
    for bounds, rt in sections:
        newcode += code[prev : bounds[0]]
        newcode += rt
        prev = bounds[1]
    
    newcode += code[prev :]
    
    return newcode

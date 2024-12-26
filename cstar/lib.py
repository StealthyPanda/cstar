
from dataclasses import dataclass
import re

union_pattern = r"""


#union itself

    \s*             # Optional whitespace after opening parenthesis
    ([a-zA-Z_]\w*             # At least one alphanumeric character
    (               # Start of optional pipe-separated group
        \s* \| \s*  # Pipe '|' surrounded by optional whitespace
        [a-zA-Z_]\w*         # Another alphanumeric character
    )+)              # Zero or more pipe-separated groups
    \s*             # Optional whitespace before closing parenthesis


"""

union_function = r'\[' + union_pattern + r"""\]
#space after the union
\s+

(
    #function name
    # [a-zA-Z_]+\w*
    [a-zA-Z_]\w*
    \s*


    #function inputs
    # \( .*? \)
    \([^)]*\) 
)

"""

identifier = r'[a-zA-Z_]\w*'

maybe_function = r'([a-zA-Z_]\w*)\s*\?' + r"""
#space after the union
\s+

(
    #function name
    # [a-zA-Z_]+\w*
    [a-zA-Z_]\w*
    \s*


    #function inputs
    # \( .*? \)
    \([^)]*\) 
)

"""

spicy_function = r'([a-zA-Z_]\w*)\s*!' + r"""
#space after the union
\s+

(
    #function name
    # [a-zA-Z_]+\w*
    [a-zA-Z_]\w*
    \s*


    #function inputs
    # \( .*? \)
    \([^)]*\) 
)

"""




return_statement = r"return\[\s*([a-zA-Z_]\w*)\s*\](.*?);"

function_inputs = r"""

(
    ([a-zA-Z_]\w*
    \s*
    [a-zA-Z_]\w*)?

    (
        \s*,\s*
        [a-zA-Z_]\w*
        \s*
        [a-zA-Z_]\w*
    )*

)

"""

function_inputs_section = r'\( \s*' + function_inputs + r'\s* \)'

match_expression = r'''

\[ \s* (([a-zA-Z_]\w*)\s* = )? \s* ([a-zA-Z_]\w*) \s* \( (.*?) \) \s* \] \s*

'''

match_branch = r'([a-zA-Z_]\w*) \s* \{'








# union_type_pattern = re.compile(r'\( \s* \w+ (\s* \| \s* \w+)* \s* \)', re.VERBOSE)
union_type_pattern = re.compile(union_pattern, re.VERBOSE | re.DOTALL)
union_functions_pattern = re.compile(union_function, re.VERBOSE | re.DOTALL)
maybe_function_pattern = re.compile(maybe_function, re.VERBOSE | re.DOTALL)
spicy_function_pattern = re.compile(spicy_function, re.VERBOSE | re.DOTALL)
return_statement_pattern = re.compile(return_statement, re.VERBOSE | re.DOTALL)
function_inputs_pattern = re.compile(function_inputs, re.VERBOSE | re.DOTALL)
function_inputs_section_pattern = re.compile(
    function_inputs_section, 
    re.VERBOSE | re.DOTALL
)
identifier_pattern = re.compile(identifier, re.VERBOSE | re.DOTALL)
match_pattern = re.compile(match_expression, re.VERBOSE | re.DOTALL)
match_branch_pattern = re.compile(match_branch, re.VERBOSE | re.DOTALL)
func_proto_pattern = re.compile(
    identifier + r'\s*' +  function_inputs_section, 
    re.VERBOSE | re.DOTALL
)




def get_union_functions(code : str):
    funcs = [each for each in union_functions_pattern.finditer(code)]
    return funcs

def get_union(code : str) -> tuple[str, ...]:
    m = union_type_pattern.search(code)
    union = m.group().strip().split('|')
    union = list(map(lambda x: x.strip(), union))
    # union = list(filter(lambda x: x != 'void', union))
    union.sort()
    return tuple(union)

def get_body(code : str) -> tuple[int, int]:
    braces = 1
    i = code.index('{')
    start = i
    
    i += 1
    while i < len(code):
        if code[i] == '{': braces += 1
        if code[i] == '}': braces -= 1
            
        i += 1
        
        if braces <= 0: break
    
    return start, i




@dataclass
class FunctionContext:
    return_type : tuple[str, ...]
    var_types : dict[str, str]

return_var_name = '_cmp_return_val'






def replace_returns(code : str, context : FunctionContext) -> str:
    
    new = code + ""
    
    ret = return_statement_pattern.search(new)
    while ret is not None:
    
        left, right = ret.span()
        
        single_type = ret.group(1).strip()
        void = single_type == 'void'
        value = None
        if not void:
            value = ret.group(2).strip()
        
        print(ret, single_type, value)
        print('context:', context)
        
        structname = "_cmp_" + "_or_".join(context.return_type)
        
        newreturn = (
            f'{structname} {return_var_name}; '+
            (f'{return_var_name}.{single_type}_val = {value}; ' if not void else '')+
            f'{return_var_name}._toggle = {context.return_type.index(single_type)}; '+
            f'return {return_var_name}; '
        )
        
        new = new[:left] + newreturn + new[right:]
        
        ret = return_statement_pattern.search(new)
        
    
    return new


def get_union_struct(context : FunctionContext) -> str:
    structname = '_cmp_' + '_or_'.join(context.return_type)
    fields = [f'\t{t} {t}_val;' for t in context.return_type if t != 'void']
    return structname, (
        f"typedef struct {structname} " + '{\n'
        f'\tunsigned char _toggle;\n'
        f'{"\n".join(fields)}\n'
        '}' +  f' {structname} ;'
    )


@dataclass
class MatchCall:
    funcname : str
    params : str
    holder : None | str
    union_type : tuple[str, ...]
    body : str

temp_holders = 0

def convert_match_expression(mc : MatchCall) -> str:
    global temp_holders
    
    structname = '_cmp_' + '_or_'.join(mc.union_type)
    
    holdername = mc.holder
    if holdername is None:
        holdername = f'_cmp_temp_holder{temp_holders}'
        temp_holders += 1
    
    
    branches = []
    
    for branch in match_branch_pattern.finditer(mc.body):
        left, right = branch.span()
        
        branch_type = branch.group(1).strip()
        
        offset = right - 1
        branch_body_left, branch_body_right = get_body(mc.body[offset:])
        branch_body_left += offset
        branch_body_right += offset
        branch_body = mc.body[branch_body_left : branch_body_right]

        
        toggleindex = mc.union_type.index(branch_type)
        
        branches.append(
            f'if ({mc.holder}._toggle == {toggleindex})\n' +
            re.sub(mc.holder, f'{mc.holder}.{branch_type}_val', branch_body)
        )
        
    
    
    return (
        f'{structname} {holdername} = {mc.funcname}({mc.params});\n' +
        '\nelse '.join(branches)
    )
    
    

def get_match_expression(code : str):
    for each in match_pattern.finditer(code):
        print(each.groups())
        _, holder, func, params = each.groups()
        mc = MatchCall(
            func, params, holder, functions[func].return_type, 
            get_body(code[each.span()[1]:])
        )
        
        return convert_match_expression(mc)


@dataclass
class FuncProto:
    name : str
    input_types : tuple[str, ...]
    
    def __hash__(self):
        return self.name.__hash__()


functions : dict[FuncProto, FunctionContext] = dict()
constructed_unions : set[tuple[str, ...]] = set()
structs : list[str] = []




def get_function_proto(code : str) -> FuncProto:
    
    fpmat = func_proto_pattern.search(code)
    
    name = identifier_pattern.search(fpmat.group()).group()
    # print(name)
    inputs = function_inputs_section_pattern.search(fpmat.group())
    if inputs is not None: inputs = inputs.group()
    # print(inputs)
    inputs = inputs[1:-1]
    inputs = list(map(lambda x: x.strip(), inputs.split(',')))
    inputs = list(map(lambda x: x.split(' ')[0], inputs))
    inputs = list(filter(lambda x:x, inputs))
    # print(inputs)
    
    # return FuncProto(name, tuple(inputs))
    return FuncProto(name, None)
    
    
    


def process_maybe_funcs(code : str) -> tuple[str, list[str]]:
    global functions, constructed_unions, structs
    
    newcode = code + ""
    
    
    ufmat = maybe_function_pattern.search(newcode)
    while ufmat is not None:
        
        print('groups:', ufmat.groups())
        funcname = ufmat.groups()[-1]
        
        ret_type = [ufmat.groups()[0], 'void']
        ret_type.sort()
        ret_type = tuple(ret_type)
        
        print('Found maybe type:', ret_type)
        
        context = FunctionContext(
            ret_type,
            dict()
        )
        funcproto = get_function_proto(ufmat.group())
        print('ecnountered function', funcproto)
        functions[funcproto] = context
        
        offset = ufmat.span()[1]
        bodyleft, bodyright = get_body(newcode[offset:])
        bodyleft += offset
        bodyright += offset
        
        
        body = newcode[bodyleft : bodyright]
        print('uf body:', body)
        body = replace_returns(body, context)
        
        
        if ret_type not in constructed_unions:
            structname, structbody = get_union_struct(context)
            print(structbody)
            structs.append(structbody)
            constructed_unions.add(ret_type)
        else:
            structname = '_cmp_' + '_or_'.join(ret_type)
        
        
        newcode = (
            newcode[:ufmat.span()[0]] + 
            f'{structname} {funcname} {body}' + 
            newcode[bodyright:]
        )
        
        ufmat = maybe_function_pattern.search(newcode)
        
    return newcode



def process_spicy_funcs(code : str) -> tuple[str, list[str]]:
    global functions, constructed_unions, structs
    
    newcode = code + ""
    
    
    ufmat = spicy_function_pattern.search(newcode)
    while ufmat is not None:
        
        print('groups:', ufmat.groups())
        funcname = ufmat.groups()[-1]
        
        ret_type = [ufmat.groups()[0], 'error']
        ret_type.sort()
        ret_type = tuple(ret_type)
        
        print('Found spicy type:', ret_type)
        
        context = FunctionContext(
            ret_type,
            dict()
        )
        funcproto = get_function_proto(ufmat.group())
        print('ecnountered function', funcproto)
        functions[funcproto] = context
        
        offset = ufmat.span()[1]
        bodyleft, bodyright = get_body(newcode[offset:])
        bodyleft += offset
        bodyright += offset
        
        
        body = newcode[bodyleft : bodyright]
        print('uf body:', body)
        body = replace_returns(body, context)
        
        
        if not ret_type in constructed_unions:
            structname, structbody = get_union_struct(context)
            print(structbody)
            structs.append(structbody)
            constructed_unions.add(ret_type)
        
        
        newcode = (
            newcode[:ufmat.span()[0]] + 
            f'{structname} {funcname} {body}' + 
            newcode[bodyright:]
        )
        
        ufmat = spicy_function_pattern.search(newcode)
        
    return newcode




def process_union_funcs(code : str) -> tuple[str, list[str]]:
    global functions, constructed_unions, structs
    
    newcode = code + ""
    
    
    ufmat = union_functions_pattern.search(newcode)
    while ufmat is not None:
        
        print('groups:', ufmat.groups())
        funcname = ufmat.groups()[-1]
        ret_type = get_union(ufmat.group())
        context = FunctionContext(
            ret_type,
            dict()
        )
        funcproto = get_function_proto(ufmat.group())
        print('ecnountered function', funcproto)
        functions[funcproto] = context
        
        offset = ufmat.span()[1]
        bodyleft, bodyright = get_body(newcode[offset:])
        bodyleft += offset
        bodyright += offset
        
        
        body = newcode[bodyleft : bodyright]
        print('uf body:', body)
        body = replace_returns(body, context)
        
        
        if not ret_type in constructed_unions:
            structname, structbody = get_union_struct(context)
            print(structbody)
            structs.append(structbody)
            constructed_unions.add(ret_type)
        
        
        newcode = (
            newcode[:ufmat.span()[0]] + 
            f'{structname} {funcname} {body}' + 
            newcode[bodyright:]
        )
        
        ufmat = union_functions_pattern.search(newcode)
        
    return newcode


def process_matches(code : str) -> str:
    global functions
    
    newcode = code + ""
    
    mbmat = match_pattern.search(newcode)
    while mbmat is not None:
        print('match groups:', mbmat.groups())
        _, holder, func, params = mbmat.groups()
        
        offset = mbmat.span()[1]
        bodyleft, bodyright = get_body(newcode[offset:])
        bodyleft += offset
        bodyright += offset
        
        funcproto = FuncProto(func, None)
        
        mc = MatchCall(
            func, params, holder, functions[funcproto].return_type, 
            newcode[bodyleft : bodyright]
        )

        converted = convert_match_expression(mc)
        
        newcode = newcode[:mbmat.span()[0]] + converted + newcode[bodyright:]
        
        mbmat = match_pattern.search(newcode)
    
    return newcode
        



def remove_comments(code : str) -> str:
    
    newcode = code
    left, right = 0, 0
    while (left < len(code)) and (right < len(code)):
        pass
    
    



includes = '''

#include <stdlib.h>
#include <stdbool.h>
#include <stdio.h>

'''


preamble = '''

// This file is generated by the C* compiler.
// Do not change code marked as autogenerated... unless you know what you're doing.

typedef struct error {
    char *message;
} error ;


'''


def process_unit(code : str, flags : dict[str, str]) -> str:
    global structs
    
    newcode = process_union_funcs(code)
    
    newcode = process_maybe_funcs(newcode)
    
    newcode = process_spicy_funcs(newcode)
    
    
    
    structscode = (
        '//' + ('-' * 120) + '\n' +
        '\n\n'.join(structs) +
        '\n//' + ('-' * 120) + '\n\n\n\n'
    )
    
    newcode = process_matches(newcode)
    
    keep_includes = True
    if 'libs' in flags:
        keep_includes = flags['libs'] in ['True', 'true', '']
    if 'strict' in flags:
        keep_includes = False
    
    return f'{includes if keep_includes else ''}\n{preamble}\n{structscode}\n{newcode}'





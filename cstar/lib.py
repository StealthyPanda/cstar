
from .classes import *
import re
from .macros import process_macros
from .funcs import *

valid_ret_type = r'[a-zA-Z_]\w*(<.*?>)? \* *'

valid_func_struct_class_name = r' [a-zA-Z_]\w* (<.*?>)? '

union_pattern = r"""


#union itself

    \s*             # Optional whitespace after opening parenthesis
    (""" + valid_ret_type + r"""
    (               # Start of optional pipe-separated group
        \s* \| \s*  # Pipe '|' surrounded by optional whitespace
        """ + valid_ret_type + r"""
    )+)              # Zero or more pipe-separated groups
    \s*             # Optional whitespace before closing parenthesis


"""


templated_regex = r'''

template \s* <.*?>

'''

optionally_templated = r'(' + templated_regex + r')?\s*'


union_function = optionally_templated + r'\[' + union_pattern + r"""\]
#space after the union
\s+

(
    #function name
    # [a-zA-Z_]+\w*
    """ + valid_func_struct_class_name + r"""
    \s*
    
    #optionally if it is a class member function...
    (::""" + valid_func_struct_class_name + r""")?


    #function inputs
    # \( .*? \)
    \s*
    \([^)]*\) 
)

"""

func_identifier = (
    valid_func_struct_class_name + 
    r'\s* (::' + valid_func_struct_class_name + r')?'
)

identifier = r'[a-zA-Z_]\w*'


maybe_function = optionally_templated + r'(' + valid_ret_type + r') \s* \?' + r"""
#space after the union
\s+

(
    #function name
    # [a-zA-Z_]+\w*
    """ + valid_func_struct_class_name + r"""
    \s*
    
    #optionally if it is a class member function...
    (::\s*""" + valid_func_struct_class_name + r""")?


    #function inputs
    # \( .*? \)
    \s*
    \([^)]*\) 
)

"""

spicy_function = optionally_templated + r'(' + valid_ret_type + r')\s*!' + r"""
#space after the union
\s+

(
    #function name
    # [a-zA-Z_]+\w*
    """ + valid_func_struct_class_name + r"""
    \s*
    
    #optionally if it is a class member function...
    (::""" + valid_func_struct_class_name + r""")?


    #function inputs
    # \( .*? \)
    \s*
    \([^)]*\) 
)

"""




return_statement = r"return\[\s*(" + valid_ret_type + r")\s*\](.*?);"

# function_inputs = r"""

# (
#     ([a-zA-Z_]\w*
#     \s*
#     [a-zA-Z_]\w*)?

#     (
#         \s*,\s*
#         [a-zA-Z_]\w*
#         \s*
#         [a-zA-Z_]\w*
#     )*

# )

# """

function_inputs = r'''
(
    .*?
    
    (\s* , .*?)?
)

'''


function_inputs_section = r'\( \s*' + function_inputs + r'\s* \)'

match_expression = r"""

\[ \s* ([a-zA-Z_]\w*)\s* =  \s* (.*?) \] \s*

"""


match_branch = r'(' + valid_ret_type +  r') \s* \{'

anytype = r'[a-zA-Z_]\w*\s*[\*&]*'

tempform = r'<.*?>'

onlystars = r'\* *'





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
func_identifier_pattern = re.compile(func_identifier, re.VERBOSE | re.DOTALL)
match_pattern = re.compile(match_expression, re.VERBOSE | re.DOTALL)
match_branch_pattern = re.compile(match_branch, re.VERBOSE | re.DOTALL)
func_proto_pattern = re.compile(
    func_identifier + r'\s*' +  function_inputs_section, 
    re.VERBOSE | re.DOTALL
)
anytype_pattern = re.compile(anytype, re.VERBOSE | re.DOTALL)
tempform_pattern = re.compile(tempform, re.VERBOSE | re.DOTALL)
onlystars_pattern = re.compile(onlystars, re.VERBOSE | re.DOTALL)
valid_ret_type_pattern = re.compile(valid_ret_type, re.VERBOSE | re.DOTALL)





def get_union(code : str) -> tuple[str, ...]:
    m = union_type_pattern.search(code)
    union = m.group().strip().split('|')
    union = list(map(lambda x: x.strip(), union))
    # union = list(filter(lambda x: x != 'void', union))
    union.sort()
    return tuple(union)






return_var_name = '_cmp_return_val'



    
def parse_template_def(code : str) -> tuple[str, ...]:
    if code is None: return None
    
    left = code.index('<')
    right = (len(code) - 1) - code[::-1].index('>')
    
    args = code[left + 1 : right]
    
    args = list(map(lambda x: x.strip(), args.split(',')))
    args = tuple(map(
        lambda x: list(filter(
            lambda y:y, x.split(' ')
        ))[-1], 
        args
    ))
    
    print('template found, args:', args)
    
    return (args)

def get_template_part(types : tuple[str, ...], decl : bool) -> str:
    if decl : types = tuple(map(lambda x:f'typename {x}', types))
    return f"<{', '.join(types)}>"



def get_writable_name(typestr : str, depth : int = 0) -> str:
    # print("got:", typestr)
    each = typestr

    base = identifier_pattern.search(each)
    if base is None: raise ValueError(f'Weird type name: {each}')
    rightbound = base.span()[1]
    base = base.group()
    
    tp = get_angle_body(typestr)
    if tp is not None:
        rightbound = tp[1]
        tp = typestr[tp[0] + 1 : tp[1] - 1]
        # print(('tp', tp))
        tp = split_root_commas(tp)
        # print(('tp after split', tp))
        tp = list(map(lambda x: x.strip(), tp))
        tp = list(filter(lambda x:x, tp))
        tp = list(map(lambda x: get_writable_name(x, depth + 1), tp))
        
        tp = f'd{depth}_' + '_'.join(tp)
    
    stars = onlystars_pattern.search(each[rightbound:])
    if stars is not None:
        stars = stars.group()
        stars = list(filter(lambda x:x.strip(), stars.split(' ')))
        if stars: stars = len(stars)
        else: stars = None
    
    return (
        base + 
        (f'_with{base}_{tp}_endwith{base}' if tp is not None else '') +
        (f'_and{base}stars{stars}' if stars is not None else '')
    )


structsprefix = '__cmp_'

def get_struct_writable_name(types : tuple[str, ...]) -> str:
    return (
        structsprefix +
        '__or__'.join([get_writable_name(x) for x in types])
    )

def requires_template_args(typestr : str, template : tuple[str, ...]) -> bool:
    
    if template is None: return False
    
    base = identifier_pattern.search(typestr)
    if base is None: raise ValueError(f'Weird type name: {typestr}')
    base = base.group().strip()
    
    if base in template: return True
    
    tp = get_angle_body(typestr)
    if tp is not None:
        tp = typestr[tp[0] + 1 : tp[1] - 1]
        # print(('tp', tp))
        tp = split_root_commas(tp)
        # print(('tp after split', tp))
        tp = list(map(lambda x: x.strip(), tp))
        tp = list(filter(lambda x:x, tp))
        tp = list(map(lambda x: requires_template_args(x, template), tp))
        
        if any(tp): return True
    
    return False
    
    



def replace_returns(code : str, context : FunctionContext) -> str:
    
    new = code + ""
    
    ret = return_statement_pattern.search(new)
    while ret is not None:
        print('return groups:', ret.groups())
        left, right = ret.span()
        
        single_type = ret.groups()[0].strip()
        void = single_type == 'void'
        value = None
        if not void:
            value = ret.groups()[-1].strip()
        
        
        # structname = "_cmp_" + "_or_".join(context.return_type)
        structname = get_struct_writable_name(context.return_type)
        # tp = ''
        # if context.template: tp = get_template_part(context.template, False)
        tp = context.templ_args
        
        
        wsing = get_writable_name(single_type)
        newreturn = (
            f'{structname}{tp} {return_var_name}; '+
            (f'{return_var_name}.{wsing}_val = {value}; ' if not void else '')+
            f'{return_var_name}._toggle = {context.return_type.index(single_type)}; '+
            f'return {return_var_name}; '
        )
        
        new = new[:left] + newreturn + new[right:]
        
        ret = return_statement_pattern.search(new)
        
    
    return new


def get_union_struct(context : FunctionContext) -> str:
    # structname = '_cmp_' + '_or_'.join(context.return_type)
    structname = get_struct_writable_name(context.return_type)
    fields = [f'\t{t} {get_writable_name(t)}_val;' for t in context.return_type if t != 'void']
    
    rs = any([
        requires_template_args(t, context.template)
        for t in context.return_type
    ])
    return structname, (
        (
            f'template {get_template_part(context.template, True)}\n' 
            if rs else ''
        ) +
        f"{'typedef ' if not rs else ''}struct {structname} " + '{\n'
        f'\tunsigned char _toggle;\n'
        f'{"\n".join(fields)}\n'
        '}' +  (f' {structname} ' if not rs else "") + ';'
    )






def convert_match_expression(mc : MatchCall) -> str:
    
    # structname = '_cmp_' + '_or_'.join(mc.union_type)
    structname = get_struct_writable_name(mc.union_type)
    
    holdername = mc.holder
    if holdername is None:
        holdername = f'_cmp_temp_holder{temp_holders}'
        temp_holders += 1
    
    
    branches = []
    
    print('match body:', mc.body)
    
    for branch in match_branch_pattern.finditer(mc.body):
        
        print('branch groups:', branch.groups())
        
        left, right = branch.span()
        
        branch_type = branch.group(1).strip()
        
        offset = right - 1
        branch_body_left, branch_body_right = get_body(mc.body[offset:])
        branch_body_left += offset
        branch_body_right += offset
        branch_body = mc.body[branch_body_left : branch_body_right]

        
        toggleindex = mc.union_type.index(branch_type)
        
        wbranchtype = get_writable_name(branch_type)
        
        branches.append(
            f'if ({mc.holder}._toggle == {toggleindex})\n' +
            re.sub(mc.holder, f'{mc.holder}.{wbranchtype}_val', branch_body)
        )
        
    tp = mc.tp
    
    return (
        '{\n' + 
        f'{structname}{tp} {holdername} = {mc.rhs};\n' +
        '\nelse '.join(branches) + '\n}' 
    )
    
    

def get_match_expression(code : str, compileinfo : CompileInfo):
    for each in match_pattern.finditer(code):
        _, holder, func, params = each.groups()
        mc = MatchCall(
            func, params, holder, compileinfo.functions[func].return_type, 
            get_body(code[each.span()[1]:])
        )
        
        return convert_match_expression(mc)








def get_function_proto(code : str) -> FuncProto:
    fpmat = func_proto_pattern.search(code)
    
    name = func_identifier_pattern.search(fpmat.group()).group()
    print('got func name:', name)

    inputs = function_inputs_section_pattern.search(fpmat.group())
    inputs = inputs.group()
    
    inputs = inputs[1:-1]
    inputs = list(map(lambda x: x.strip(), split_root_commas(inputs)))
    inputs = list(filter(lambda x:x, inputs))
    inputs = list(map(lambda x: valid_ret_type_pattern.search(x).group(), inputs))
    inputs = list(map(lambda x: re.sub(r'\s+', '', x), inputs))
    
    # print('func proto inputs', inputs)
    
    # return FuncProto(name, tuple(inputs))
    return FuncProto(name, None)
    




def process_maybe_funcs(code : str, compileinfo : CompileInfo) -> tuple[str, list[str]]:
    
    newcode = code + ""
    
    
    ufmat = maybe_function_pattern.search(newcode)
    while ufmat is not None:
        
        print('groups', ufmat.groups())
        
        fullproto = ufmat.groups()[-4]
        
        ret_type = [ufmat.groups()[1], 'void']
        ret_type.sort()
        ret_type = tuple(ret_type)
        print('detected ret type', ret_type)
        
        template_ori = ufmat.groups()[0]
        
        temp_def = parse_template_def(template_ori)
        req_temp_args = any(map(
            lambda x: requires_template_args(x, temp_def), 
            ret_type
        ))
        tp = ''
        if req_temp_args:
            tp = get_template_part(temp_def, False)
        
        context = FunctionContext(
            ret_type,
            dict(),
            temp_def,
            tp
        )
        
        funcproto = get_function_proto(ufmat.group())
        compileinfo.functions[funcproto] = context
        
        offset = ufmat.span()[1]
        nextpart = newcode[offset:]
        if nextpart.strip()[0] == '{':
            bodyleft, bodyright = get_body(nextpart)
            bodyleft += offset
            bodyright += offset
            
            
            body = newcode[bodyleft : bodyright]
            
            #Adding default return[void]
            end = len(body) - 1
            while end >= 0 and body[end] != '}': end -= 1
            body = (
                body[:end] + '\nreturn[void];\n' + body[end:]
            )
            
            body = replace_returns(body, context)
            body = ' ' + body
        else:
            body = ''
            bodyright = ufmat.span()[1]
        
        
        
        if ret_type not in compileinfo.constructed_unions:
            structname, structbody = get_union_struct(context)
            compileinfo.structs.append(structbody)
            compileinfo.constructed_unions.add(ret_type)
        else:
            # structname = '_cmp_' + '_or_'.join(ret_type)
            structname = get_struct_writable_name(ret_type)
            structbody = ''
        
        # tp = ''
        # if template_ori is not None:
        #     tp = ' ' + get_template_part(context.template, False)
        
        newcode = (
            newcode[:ufmat.span()[0]] + 
            '\n\n' + 
            f'{structbody}\n' +
            (f'{template_ori}\n' if template_ori is not None else '') + 
            f'{structname}{tp} {fullproto}{body}' + 
            newcode[bodyright:]
        )
        
        ufmat = maybe_function_pattern.search(newcode)
        
    return newcode



def process_spicy_funcs(code : str, compileinfo : CompileInfo) -> tuple[str, list[str]]:
    
    newcode = code + ""
    
    
    ufmat = spicy_function_pattern.search(newcode)
    while ufmat is not None:
        
        
        fullproto = ufmat.groups()[-4]
        
        ret_type = [ufmat.groups()[1], 'error']
        ret_type.sort()
        ret_type = tuple(ret_type)
        
        template_ori = ufmat.groups()[0]
        
        temp_def = parse_template_def(template_ori)
        req_temp_args = any(map(
            lambda x: requires_template_args(x, temp_def), 
            ret_type
        ))
        tp = ''
        if req_temp_args:
            tp = get_template_part(temp_def, False)
        
        context = FunctionContext(
            ret_type,
            dict(),
            temp_def,
            tp
        )
        
        funcproto = get_function_proto(ufmat.group())
        compileinfo.functions[funcproto] = context
        
        offset = ufmat.span()[1]
        
        nextpart = newcode[offset:]
        if nextpart.strip()[0] == '{':
            bodyleft, bodyright = get_body(nextpart)
            bodyleft += offset
            bodyright += offset
            
            
            body = newcode[bodyleft : bodyright]
            body = replace_returns(body, context)
            body = ' ' + body
        else:
            body = ''
            bodyright = ufmat.span()[1]
        
        
        if not ret_type in compileinfo.constructed_unions:
            structname, structbody = get_union_struct(context)
            compileinfo.structs.append(structbody)
            compileinfo.constructed_unions.add(ret_type)
        else:
            # structname = '_cmp_' + '_or_'.join(ret_type)
            structname = get_struct_writable_name(ret_type)
            structbody = ''
        
        # tp = ''
        # if template_ori is not None:
        #     tp = ' ' + get_template_part(context.template, False)
        
        newcode = (
            newcode[:ufmat.span()[0]] + 
            '\n\n' + 
            f'{structbody}\n' +
            (f'{template_ori}\n' if template_ori is not None else '') + 
            f'{structname}{tp} {fullproto}{body}' + 
            newcode[bodyright:]
        )
        
        ufmat = spicy_function_pattern.search(newcode)
        
    return newcode




def process_union_funcs(code : str, compileinfo : CompileInfo) -> tuple[str, list[str]]:
    
    newcode = code + ""
    
    
    ufmat = union_functions_pattern.search(newcode)
    while ufmat is not None:
        
        
        fullproto = ufmat.groups()[-4]
        
        ret_type = get_union(ufmat.group())
        
        print('detected ret type (general onion)', ret_type)
        
        template_ori = ufmat.groups()[0]
        
        temp_def = parse_template_def(template_ori)
        req_temp_args = any(map(
            lambda x: requires_template_args(x, temp_def), 
            ret_type
        ))
        tp = ''
        if req_temp_args:
            tp = get_template_part(temp_def, False)
        
        context = FunctionContext(
            ret_type,
            dict(),
            temp_def,
            tp
        )
        
        funcproto = get_function_proto(ufmat.group())
        compileinfo.functions[funcproto] = context
        
        offset = ufmat.span()[1]
        nextpart = newcode[offset:]
        if nextpart.strip()[0] == '{':
            bodyleft, bodyright = get_body(nextpart)
            bodyleft += offset
            bodyright += offset
            
            
            body = newcode[bodyleft : bodyright]
            body = replace_returns(body, context)
            body = ' ' + body
        else:
            body = ''
            bodyright = ufmat.span()[1]
        
        
        
        
        if not ret_type in compileinfo.constructed_unions:
            structname, structbody = get_union_struct(context)
            compileinfo.structs.append(structbody)
            compileinfo.constructed_unions.add(ret_type)
        else:
            # structname = '_cmp_' + '_or_'.join(ret_type)
            structname = get_struct_writable_name(ret_type)
            structbody = ''
        
        # tp = ''
        # if template_ori is not None:
        #     tp = ' ' + get_template_part(context.template, False)
        
        newcode = (
            newcode[:ufmat.span()[0]] + 
            '\n\n' + 
            f'{structbody}\n' +
            (f'{template_ori}\n' if template_ori is not None else '') + 
            f'{structname}{tp} {fullproto}{body}' + 
            newcode[bodyright:]
        )
        
        ufmat = union_functions_pattern.search(newcode)
        
    return newcode


def process_matches(code : str, compileinfo : CompileInfo) -> str:
    global functions
    
    newcode = code + ""
    
    mbmat = match_pattern.search(newcode)
    while mbmat is not None:
        print('mbmat groups', mbmat.groups())
        
        holder, rhs = mbmat.groups()
        
        lrb, rrb = get_round_body(rhs)
        funcfull = rhs[:lrb]
        params = rhs[lrb:rrb]
        
        funcname = [x for x in funcfull.split('::') if x]
        for i, each in enumerate(funcname):
            bounds = get_angle_body(each)
            if bounds:
                l, r = bounds
                funcname[i] = each[:l]
        funcname = '::'.join(funcname)
        
        offset = mbmat.span()[1]
        bodyleft, bodyright = get_body(newcode[offset:])
        bodyleft += offset
        bodyright += offset
        
        funcproto = FuncProto(funcname, None)
        context = compileinfo.functions[funcproto]
        
        mc = MatchCall(
            funcname, params, holder, context.return_type, 
            newcode[bodyleft : bodyright], rhs, context.templ_args
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

#include "{fp}_cmp_stuff.h"


'''


def process_unit(code : str, flags : dict[str, str], compileinfo : CompileInfo, folderpart : str) -> str:
    
    newcode = process_macros(code, compileinfo)
    
    newcode = process_union_funcs(newcode, compileinfo)
    
    newcode = process_maybe_funcs(newcode, compileinfo)
    
    newcode = process_spicy_funcs(newcode, compileinfo)
    
    print('functions at the end of all processing of onions:')
    print(compileinfo.functions)
    
    newcode = process_matches(newcode, compileinfo)
    
    keep_includes = False
    if 'libs' in flags:
        keep_includes = flags['libs'] in ['True', 'true', '']
    if 'strict' in flags:
        keep_includes = False
    
    fp = folderpart
    # return f'{includes if keep_includes else ''}\n{preamble}\n{structscode}\n{newcode}'
    return f'{includes if keep_includes else ''}\n{preamble.format(fp=fp)}\n{newcode}'



errorstruct = '''

#pragma once

typedef struct error {
    char *message;
} error ;

'''
def write_structs(path : str, compileinfo : CompileInfo):
    global errorstruct
    
    # structscode = (
    #     '\n#pragma once\n\n' + 
    #     '//' + ('-' * 120) + '\n' +
    #     errorstruct +
    #     '\n\n'.join(compileinfo.structs) +
    #     '\n//' + ('-' * 120) + '\n\n\n\n'
    # )
    with open(path, 'w') as file:
        file.write(errorstruct)









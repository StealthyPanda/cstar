
import re
from typing import Any, Callable
from .classes import *
from .funcs import *
import os


identifier = r'[a-zA-Z_]\w*'
reifitnedi = r'\w*[a-zA-Z_]'

macro_regex = r'@(' + identifier + r'[?!]?)'

macro_pattern = re.compile(macro_regex, re.VERBOSE | re.DOTALL)
onlyid_pattern = re.compile(identifier, re.VERBOSE | re.DOTALL)
backwards_identifier_pattern = re.compile(reifitnedi, re.VERBOSE | re.DOTALL)


def throw_macro(inputs : list[str], **kwargs) -> str:
    
    message = '"Error Thrown!"'
    if inputs: message = inputs[0]
    
    return (
        'error e = { ' + message + ' }; '
        'return[error] e;'
    ), kwargs['span']




def unwrap_macro_by_type(inputs : list[str], **kwargs) -> str:
    
    call, type_to_look, output = inputs
    
    codeinfo : CodeInfo = kwargs['codeinfo']
    line = codeinfo.line_number
    file = codeinfo.file_name
    
    file = os.path.basename(file)

    unwrap_call_temp = f'[ _unwrap_holder = {call} ]'
    unwrap_err_temp = (
        'error { fprintf(stderr, "ERROR::UNHANDLED_ERROR ' +
        f'<{file} @ line {line}>' + ':\\n\\t->%s\\n", _unwrap_holder.message); exit(-1); }'
    )
    unwrap_ok = type_to_look + '{' + f' {output} = _unwrap_holder; ' + '}'

    
    return (
        unwrap_call_temp + '{\n' + unwrap_err_temp + '\n' + unwrap_ok + '\n' + '}'
    ), kwargs['span']


def unwrap_error_macro(inputs : list[str], **kwargs) -> str:
    statement = inputs[0]
    
    codeinfo : CodeInfo = kwargs['codeinfo']
    line = codeinfo.line_number
    file = codeinfo.file_name
    file = os.path.basename(file)

    lhs, rhs = statement.split('=')
    
    lhstatement = f'{lhs.strip()};\n'
    splat = [x for x in lhs.split(' ') if x]
    output = splat[-1]
    type_to_look = ' '.join(splat[:-1])
    call = rhs
    
    unwrap_call_temp = f'[ _unwrap_holder = {call} ]'
    unwrap_err_temp = (
        'error { fprintf(stderr, "ERROR::UNHANDLED_ERROR ' +
        f'<{file} @ line {line}>' + ':\\n\\t->%s\\n", _unwrap_holder.message); exit(-1); }'
    )
    unwrap_ok = type_to_look + '{' + f' {output} = _unwrap_holder; ' + '}'

    
    return (
        lhstatement + 
        unwrap_call_temp + '{\n' + unwrap_err_temp + '\n' + unwrap_ok + '\n' + '}'
    ), kwargs['span']


def unwrap_maybe_macro(inputs : list[str], **kwargs) -> str:
    statement = inputs[0]
    
    codeinfo : CodeInfo = kwargs['codeinfo']
    line = codeinfo.line_number
    file = codeinfo.file_name
    file = os.path.basename(file)

    lhs, rhs = statement.split('=')
    
    lhstatement = f'{lhs.strip()};\n'
    splat = [x for x in lhs.split(' ') if x]
    output = splat[-1]
    type_to_look = ' '.join(splat[:-1])
    call = rhs
    
    unwrap_call_temp = f'[ _unwrap_holder = {call} ]'
    unwrap_err_temp = (
        'void { fprintf(stderr, "WARNING::VOID_RETURN ' +
        f'<{file} @ line {line}>' + f': \\n\\t->Variable <{output}> may be uninitialized.\\n"); ' + '}'
    )
    unwrap_ok = type_to_look + '{' + f' {output} = _unwrap_holder; ' + '}'

    
    return (
        lhstatement + 
        unwrap_call_temp + '{\n' + unwrap_err_temp + '\n' + unwrap_ok + '\n' + '}'
    ), kwargs['span']



macros : dict[str, Callable[[Any, CodeInfo], str]] = {
    'throw' : throw_macro,
    'unwrap!' : unwrap_error_macro,
    'unwrap?' : unwrap_maybe_macro,
}


def define_macro(inputs : list[str], **kwargs) -> str:
    name = inputs[0]
    
    # code = kwargs['code']
    body = kwargs['body']
    
    
    macrostring = f'def {name}_macro(inputs : list[str], **kwargs):\n'
    macrostring += body
    
    localscope = dict()
    exec(macrostring, globals(), localscope)
    
    macrofunc = localscope[f'{name}_macro']
    
    macros[name] = macrofunc
    
    
    return '', kwargs['span']


def mini_unwrap_error_macro(inputs : list[str], **kwargs) -> str:
    # call, type_to_look, output = inputs
    
    codeinfo : CodeInfo = kwargs['codeinfo']
    line = codeinfo.line_number
    file = codeinfo.file_name
    file = os.path.basename(file)
    
    call = inputs[0]
    funcname = re.search(onlyid_pattern, inputs[0]).group()
    print('uw func name:', funcname)
    
    
    code : str = kwargs['allcode']
    l, r = kwargs['bounds']
    subcode = code[:l][::-1]
    b2 = subcode.index('=')
    mainvar = backwards_identifier_pattern.search(subcode[b2 + 1:])
    lb3, rb3 = mainvar.span()
    mainvar = mainvar.group()[::-1]
    
    
    type_to_look = backwards_identifier_pattern.search(subcode[b2 + 1 + rb3:])
    _, leftmost = type_to_look.span()
    type_to_look = type_to_look.group()[::-1]
    
    leftmost = len(subcode) - (leftmost + b2 + 1 + rb3)
    
    
    print('mainvar:', mainvar, 'type_to_look:', type_to_look)
    output = mainvar

    unwrap_call_temp = f'[ _unwrap_holder = {call} ]'
    unwrap_err_temp = (
        'error { fprintf(stderr, "ERROR::UNHANDLED_ERROR ' +
        f'<{file} @ line {line}>' + ':\\n\\t->%s\\n", _unwrap_holder.message); exit(-1); }'
    )
    unwrap_ok = type_to_look + ' {' + f' {output} = _unwrap_holder; ' + '}'

    ls, rs = kwargs['span']
    
    initstatement = f'{type_to_look} {output};\n'
    
    return (
        initstatement +
        unwrap_call_temp + '{\n' + unwrap_err_temp + '\n' + unwrap_ok + '\n' + '}'
    ), (leftmost, rs)



def mini_unwrap_maybe_macro(inputs : list[str], **kwargs) -> str:
    
    codeinfo : CodeInfo = kwargs['codeinfo']
    line = codeinfo.line_number
    file = codeinfo.file_name
    file = os.path.basename(file)
    
    call = inputs[0]
    funcname = re.search(onlyid_pattern, inputs[0]).group()
    print('uw func name:', funcname)
    
    
    code : str = kwargs['allcode']
    l, r = kwargs['bounds']
    subcode = code[:l][::-1]
    b2 = subcode.index('=')
    mainvar = backwards_identifier_pattern.search(subcode[b2 + 1:])
    lb3, rb3 = mainvar.span()
    mainvar = mainvar.group()[::-1]
    
    type_to_look = backwards_identifier_pattern.search(subcode[b2 + 1 + rb3:])
    _, leftmost = type_to_look.span()
    type_to_look = type_to_look.group()[::-1]
    
    leftmost = len(subcode) - (leftmost + b2 + 1 + rb3)
    
    print('mainvar:', mainvar, 'type_to_look:', type_to_look)
    output = mainvar
    
    unwrap_call_temp = f'[ _unwrap_holder = {call} ]'
    unwrap_err_temp = (
        'void { fprintf(stderr, "WARNING::VOID_RETURN ' +
        f'<{file} @ line {line}>' + f': \\n\\t->Variable <{output}> may be uninitialized.\\n"); ' + '}'
    )
    unwrap_ok = type_to_look + '{' + f' {output} = _unwrap_holder; ' + '}'

    ls, rs = kwargs['span']
    
    initstatement = f'{type_to_look} {output};\n'
    
    return (
        initstatement + 
        unwrap_call_temp + '{\n' + unwrap_err_temp + '\n' + unwrap_ok + '\n' + '}'
    ), (leftmost, rs)


macros['define'] = define_macro
macros['uw?'] = mini_unwrap_maybe_macro
macros['uw!'] = mini_unwrap_error_macro



def process_macros(code : str, compileinfo : CompileInfo) -> str:
    
    newcode = code + ""
    
    mmat = macro_pattern.search(newcode)
    
    codeinfo = CodeInfo(compileinfo.current_file, 0)
    
    while mmat is not None:
        
        print('macro matches:', mmat.groups() )
        
        name = mmat.groups()[0]
        
        offset = mmat.span()[1]
        left, right = get_round_body(newcode[mmat.span()[1]:])
        callbody = newcode[left + offset + 1 : right + offset - 1]
        
        body = None
        l, r = 0, 0
        if has_body(newcode[right + offset + 1:]):
            l, r = get_body(newcode[right + offset + 1:])
            body = newcode[right + offset + 1:][l + 1 : r - 1]
            r += 1
        
        inputs = list(map(lambda x: x.strip(), split_root_commas(callbody.strip())))
        inputs = list(filter(lambda x:x, inputs))
        
        
        mac = macros[name]
        
        ind = code.index(newcode[ mmat.span()[0] : right + offset ])
        print(f'searching: `{newcode[ mmat.span()[0] : right + offset ]}` @ {ind}')
        codeinfo.line_number = get_line_number(
            code, 
            code.index(newcode[ mmat.span()[0] : right + offset ]),
        )
        
        spanleft, spanright = mmat.span()[0], right + offset + r
        
        macout, (spanleft, spanright) = mac(
            inputs, 
            codeinfo=codeinfo, 
            code=newcode[mmat.span()[0]:], 
            allcode=newcode,
            originalcode=code, 
            body=body, 
            compileinfo=compileinfo,
            bounds=mmat.span(),
            span=(spanleft, spanright),
        )
        
        print('macout', macout)
        if macout is None or not macout:
            macout = ''
        
        newcode = (
            newcode[:spanleft] + 
            macout + newcode[spanright:]
        )
        
        mmat = macro_pattern.search(newcode)
    
    return newcode
        
        
        
        
    



if __name__ == '__main__':
    
    print(throw_macro('bruh'))
    


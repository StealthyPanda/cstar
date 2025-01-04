

def split_root_commas(typestr : str) -> tuple[str]:
    splits = []
    depth = 0
    last = 0
    for i, each in enumerate(typestr):
        if each == '<': depth += 1
        elif each == '>': depth -= 1
        elif each == ',':
            if depth == 0:
                splits.append(typestr[last : i])
                last = i + 1
    
    if depth == 0:
        splits.append(typestr[last : ])
    
    return splits



def get_round_body(code : str) -> tuple[int, int] | None:
    braces = 1
    try : i = code.index('(')
    except ValueError: return None
    start = i
    
    i += 1
    while i < len(code):
        if code[i] == '(': braces += 1
        if code[i] == ')': braces -= 1
            
        i += 1
        
        if braces <= 0: break
    
    if braces > 0:
        raise ValueError(f'Unbalanced round brackets; `{code}`')
    
    return start, i


def get_angle_body(code : str) -> tuple[int, int] | None:
    braces = 1
    try : i = code.index('<')
    except ValueError: return None
    start = i
    
    i += 1
    while i < len(code):
        if code[i] == '<': braces += 1
        if code[i] == '>': braces -= 1
            
        i += 1
        
        if braces <= 0: break
    
    if braces > 0:
        raise ValueError(f'Unbalanced angle brackets; `{code}`')
    
    return start, i


def get_line_number(string : str, index : int) -> int:
    return string[:index].count('\n') + 1



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

def has_body(code : str) -> bool:
    return code.strip()[0] == '{'


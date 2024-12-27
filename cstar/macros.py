
import re
from typing import Any, Callable

identifier = r'([a-zA-Z_]\w*)'

macro_regex = r'@' + identifier + r'\((.*?)\)'

macro_pattern = re.compile(macro_regex, re.VERBOSE | re.DOTALL)



def throw_macro(inputs : list[str]) -> str:
    
    message = '"Error Thrown!"'
    if inputs: message = inputs[0]
    
    return (
        'error e = { ' + message + ' }; '
        'return[error] e;'
    )



macros : dict[str, Callable[[Any], str]] = {
    'throw' : throw_macro
}




def process_macros(code : str) -> str:
    
    newcode = code + ""
    
    mmat = macro_pattern.search(newcode)
    
    while mmat is not None:
        
        print('macro matches:', mmat.groups() )
        
        name, inputs = mmat.groups()
        
        inputs = list(map(lambda x: x.strip(), inputs.strip().split(',')))
        inputs = list(filter(lambda x:x, inputs))
        
        mac = macros[name]
        
        newcode = (
            newcode[:mmat.span()[0]] + 
            mac(inputs) + newcode[mmat.span()[1]:]
        )
        
        mmat = macro_pattern.search(newcode)
    
    return newcode
        
        
        
        
    



if __name__ == '__main__':
    
    print(throw_macro('bruh'))
    


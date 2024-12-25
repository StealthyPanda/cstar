
from .lib import *

import sys, os
from loguru import logger

logger.remove()
logger.add(
    sys.stdout, 
    format='<level>{message}</level>',
    colorize=True
)


def read_file(filename : str) -> str:
    with open(filename, 'r') as file:
        cont = file.read()
    return cont

def parse_args(args : list[str]) -> tuple[list[str], dict]:
    files = []
    flags = dict()
    flag = None
    for i, each in enumerate(args):
        if flag is not None:
            flag = None
            continue
        
        if '--' == each[:2]:
            flag = each[2:]
            if flag:
                if (i < (len(args) - 1)):
                    flags[flag] = args[i + 1]
                else:
                    flags[flag] = None
            else: flag = None
        else:
            files.append(each)
    
    return files, flags





def main():
    files, flags = parse_args(sys.argv[1:])
    
    for i, each in enumerate(files):
        logger.info(f'Compiling [{i+1}/{len(files)}] `{each}`...')
        
        filename = os.path.basename(each).split('.')[0]
        
        code = read_file(each)
        
        code = process_unit(code)
        
        with open(os.path.join(os.getcwd(), f'{filename}.c'), 'w') as file:
            file.write(code)
        
        
            
    
    
    
    
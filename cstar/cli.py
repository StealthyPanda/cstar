
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
        
        if '-' == each[0]:
            if '--' == each[:2]: flag = each[2:]
            else: flag = each[1:]
            
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
    
    each = files[0]
    logger.info(f'Compiling [{each}]...')
    filename, ext, _ = os.path.basename(each).split('.')
    
    output_file_name = os.path.join(os.path.dirname(each), f'{filename}.{ext}')
    
    if ('output' in flags):
        output_file_name = f'{flags['output']}.{ext}'
    if ('o' in flags):
        output_file_name = f'{flags['o']}.{ext}'    
    
    
    code = read_file(each)
    
    code = process_unit(code)
    
    with open(output_file_name, 'w') as file:
        file.write(code)
        
        
            
    
    
    
    
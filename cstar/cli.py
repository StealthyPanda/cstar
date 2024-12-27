
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
    
    
    if 'idir' in flags:
        folder = flags['idir']
        files = list(filter(
            lambda x: os.path.isfile(x) and (os.path.basename(x).split('.')[-1] == 'cmp'),
            list(map(
                lambda y: os.path.join(folder, y),
                os.listdir(folder)
            ))
        ))
    
    logger.warning('Compiling files:')
    for i, each in enumerate(files):
        if i == (len(files) - 1):
            logger.info(f'╰{each}')
            continue
        logger.info(f'├{each}')
        
    print()
    
    for i, each in enumerate(files):
        logger.info(f'Compiling [{i+1}/{len(files)}][{each}]...')
        
        filename, ext, _ = os.path.basename(each).split('.')
        output_dir_name = os.path.dirname(each)
        
        if 'odir' in flags:
            output_dir_name = flags['odir']
        
        output_file_name = os.path.join(output_dir_name, f'{filename}.{ext}')
        
        if ('output' in flags):
            output_file_name = f'{flags['output']}.{ext}'
        if ('o' in flags):
            output_file_name = f'{flags['o']}.{ext}'
        
        
        code = read_file(each)
        
        code = process_unit(code, flags)
        
        with open(output_file_name, 'w') as file:
            file.write(code)
    
    write_structs(os.path.join(output_dir_name, f'_cmp_stuff.h'))
        
        
            
    
    
    
    
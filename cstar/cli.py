
from .lib import *

import sys, os
from loguru import logger
from dataclasses import dataclass
from .classes import *

import pickle


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


def get_deepest_common_folder(p1 : str, p2 : str) -> str:
    p1 = os.path.normpath(p1)
    p2 = os.path.normpath(p2)
    
    common = []
    for l, r in zip(p1.split(os.path.sep), p1.split(os.path.sep)):
        if l == r: common.append(l)
        else: break
    
    return os.path.join(*common)


cstar = '.cstar'
tempfolder = os.path.join(cstar, 'temp')
compinfopath = os.path.join(cstar, 'compileinfo')
pexts = {
    'c' : 'c',
    'h' : 'c',
    'hpp' : 'cpp',
    'cpp' : 'cpp'
}




def main():
    files, flags = parse_args(sys.argv[1:])
    
    os.makedirs(cstar, exist_ok=True)
    
    cwd = os.getcwd()
    
    compinf = CompileInfo()
    
    if os.path.exists(compinfopath) and ('fresh' not in flags) and (len(files) > 1):
        with open(compinfopath, 'rb') as file:
            compinf = pickle.load(file)
    else:
        logger.info('Using fresh compile info...')
    
    
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
        
        compinf.current_file = each
        
        filename, ext, _ = os.path.basename(each).split('.')
        output_dir_name = os.path.dirname(each)
        
        if 'odir' in flags:
            output_dir_name = flags['odir']
        
        output_file_name = os.path.join(output_dir_name, f'{filename}.{ext}')
        
        if 'root' in flags:
            output_dir_name = os.path.normpath(each).split(os.path.sep)
            output_dir_name = (
                output_dir_name[0] 
                if output_dir_name[0] not in ('', '.') else output_dir_name[1]
            )
        
        if ('output' in flags):
            output_file_name = f"{flags['output']}.{ext}"
        if ('o' in flags):
            output_file_name = f"{flags['o']}.{ext}"
        
        
        output_file_base_ext = os.path.basename(output_file_name)
        output_file_base = output_file_base_ext.split('.')[0]
        # temploc = os.path.join(
        #     os.path.dirname(each), tempfolder, f'{output_file_base}.i'
        # )
        # os.makedirs(os.path.dirname(temploc), exist_ok=True)
        # #preprocess everything...
        # pext = pexts[ext.lower()]
        # precom = f'gcc -E -P -x {pext} {each} -o {temploc}'
        # logger.info('Preprocessing command: ' + precom)
        # ocode = os.system(precom)
        # if ocode:
        #     logger.critical(f"Preprocessing failed; exit code {ocode}")
        
        
        code = read_file(each)
        
        depth = len(os.path.normpath(os.path.relpath(output_file_name, cwd)).split(os.path.sep))
        fp = '/'.join(['..' for _ in range(depth - 1)])
        if fp: fp += '/.cstar'
        else: fp += '.cstar'
        
        fp = f'./{fp}/'
        
        code = process_unit(code, flags, compinf, fp)
        if ext in ['h', 'hpp']:
            code = '\n\n#pragma once\n\n' + code
        
        with open(output_file_name, 'w') as file:
            file.write(code)
    
    write_structs(os.path.join(cstar, '_cmp_stuff.h'), compinf)
    
    
    with open(compinfopath, 'wb') as file:
        pickle.dump(compinf, file)

    print('-'*100)
    logger.success('Compiled C* project successfully')
    print('-'*100)
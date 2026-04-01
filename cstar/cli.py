
import typer, os, rich
from typing import Annotated

from . import transpiler

app = typer.Typer(help='CStar CLI tool')


def get_file_n_exts(path : str) -> list[str]:
    return path.split('.')





@app.command()
def file(src : str, out : Annotated[str, typer.Argument(help='Output path')] = ''):
    """Transpiles a single file."""
    
    if not os.path.exists(src):
        rich.print("[red]Source file does not exist![/red]")
        raise typer.Exit(1)
    
    if not out:
        out = '.'.join(get_file_n_exts(src)[:-1])
    
    dir = os.path.dirname(src)
    
    transpiler.compile_project([src], [out], dir)
    
    

def get_all_cmps(folder : str) -> list[str]:
    files = []
    for each in os.listdir(folder):
        each = os.path.join(folder, each)
        if os.path.isdir(each):
            files += get_all_cmps(each)
        else:
            if each.split('.')[-1].lower() == 'cmp':
                files.append(each)
    return files


@app.command()
def project(
        root : Annotated[str, typer.Argument(
            help='Root location of the project files'
        )],
        target : Annotated[str, typer.Argument(
            help='Target dir, created if doesn\'t exist'
        )] = '',
    ):
    """
    Compiles a CStar project, given the root location. 
    If a target location is provided, the root project structure is mirrored in the new location.
    """
    
    cmpfiles = get_all_cmps(root)
    rich.print(f'[light]Found {len(cmpfiles)} to compile...[/light]')
    
    outpaths = []
    if target:
        for each in cmpfiles:
            rp = os.path.relpath(each, root)
            outpaths.append(os.path.join(target, rp))
    else:
        outpaths = cmpfiles
    
    outpaths = list(map(lambda x: '.'.join(x.split('.')[:-1]), outpaths))
    
    for each in outpaths:
        os.makedirs(os.path.dirname(each), exist_ok=True)
    
    # outpaths = list(map(lambda x: os.path.relpath(x, target), outpaths))
    
    transpiler.compile_project(cmpfiles, outpaths, target)
    
        
    

    


    
        
if __name__ == '__main__':
    app()
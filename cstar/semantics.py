
from .utils import *
from .renderer import get_c_alias, render_tagged_returns


c_void_type = C_return(('void',))
c_error_type = C_return(('error',))



class BaseSemantics:
    
    def __init__(self, context : CompilerContext):
        self.ctx = context
    
    def return_type(self, ast):
        return C_return(
            base = tuple(ast['base_type']),
            pointer = len(ast['pointer']),
        )
    
    def _default(self, ast):
        return ast



class OnionSemantics(BaseSemantics):
    def __init__(self, context, tr_parser):
        super().__init__(context)
        self.tr_parser = tr_parser
    
    def onion_function(self, ast):
        
        buffer = ast['onion_return']
        
        onf = OnionFunc(
            name=ast['func_name'], 
            returns=frozenset(buffer['return']),
            body=''.join(flatten(ast['body']['body'])),
            bounds=(ast.parseinfo.pos, ast.parseinfo.endpos),
            onion_bounds=(
                buffer.parseinfo.pos, 
                buffer.parseinfo.endpos,
            ),
            body_bounds=(
                ast['body'].parseinfo.pos,
                ast['body'].parseinfo.endpos,
            ),
        )
        
        trs = self.tr_parser.parse(onf.body)
        trs = list(filter(lambda x: type(x) == TaggedReturn, trs))
        for tr in trs:
            if tr.rtype not in onf.returns:
                raise TypeError(
                    f"Invalid return type `{str(tr.rtype)}` in `{onf.name}`"
                )
        
        
        if onf.name in self.ctx.onion_func_names:
            raise SyntaxError(
                f"Redefinition of function `{onf.name}`"
            )
        
        self.ctx.onion_func_names.add(onf.name)
        self.ctx.onion_funcs[onf.name] = onf
        
        return onf
    
    def maybe_or_spicy_function(self, ast):
        info = ast['maybe_or_spicy']
        rets = [ info['return'] ]
        
        if '?' in info['type']: rets.append(c_void_type)
        if '!' in info['type']: rets.append(c_error_type)
        
        
        
        onf = OnionFunc(
            name=ast['func_name'], 
            returns=frozenset(rets),
            body=''.join(flatten(ast['body']['body'])),
            bounds=(ast.parseinfo.pos, ast.parseinfo.endpos),
            onion_bounds=(
                ast['maybe_or_spicy'].parseinfo.pos, 
                ast['maybe_or_spicy'].parseinfo.endpos,
            ),
            body_bounds=(
                ast['body'].parseinfo.pos,
                ast['body'].parseinfo.endpos,
            ),
        )
        
        trs = self.tr_parser.parse(onf.body)
        for tr in trs:
            if tr.rtype not in onf.returns:
                raise TypeError(
                    f"Invalid return type `{str(tr.rtype)}` in `{onf.name}`"
                )
        
        if onf.name in self.ctx.onion_func_names:
            raise SyntaxError(
                f"Redefinition of function `{onf.name}`"
            )
        
        self.ctx.onion_func_names.add(onf.name)
        self.ctx.onion_funcs[onf.name] = onf
        
        return onf
    
        
    



class TaggedReturnSemantics(BaseSemantics):
    
    def __init__(self):
        super().__init__(None)

    def tagged_return(self, ast):
        return TaggedReturn(
            rtype=ast['return_type'],
            value=ast['value'],
            bounds=(ast.parseinfo.pos, ast.parseinfo.endpos)
        )



class UnwrapSemantics(BaseSemantics):

    def unwrapping_decl(self, ast):
        
        if ast['func_name'] not in self.ctx.onion_func_names:
            raise TypeError(
                f"`{ast['func_name']}` is not an onion; cannot be unwrapped!"
            )
        
        return UnwrapDecl(
            symbol=ast['symbol'],
            name=ast['func_name'],
            args=ast['args'],
            bounds=(
                ast.parseinfo.pos,
                ast.parseinfo.endpos,
            )
        )
    
    def unwrapping_branch(self, ast):
        return UnwrapBranch(
            rtype=ast['return_type'], 
            body=''.join(flatten(ast['body']['body'])),
            body_bounds=(
                ast['body'].parseinfo.pos,
                ast['body'].parseinfo.endpos,
            ),
        )

    def unwrapping(self, ast):
        uw = Unwrap(
            declaration=ast['decl'],
            branches=ast['branches'],
            bounds=(ast.parseinfo.pos, ast.parseinfo.endpos)
        )
        
        bs = frozenset([x.rtype for x in uw.branches])
        
        funcrts = self.ctx.onion_funcs[uw.declaration.name].returns
        for rt in funcrts:
            if rt not in bs:
                raise TypeError(
                    f"Missing branch for type `{str(rt)}` in unwrapping for `{uw.declaration.name}`"
                )
        
        return uw
            



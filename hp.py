#!/usr/bin/python

import ast

class HotPotato:
    def __init__(self, fn):
        self.ast = compile(open(fn).read(),
                fn,
                'exec',
                ast.PyCF_ONLY_AST)

    def php(self):
        return '<?php\n'+self._php(self.ast)

    def _php(self, a):
        c = a.__class__
        if c == ast.Module:
            s = ''
            for b in a.body:
                s += self._php(b)
                s += '\n'
            return s

        elif c == ast.Assign:
            return self._php(a.targets[0]) + ' = ' + self._php(a.value) + ';'

        elif c == ast.Name:
            return '$'+a.id

        elif c == ast.List:
            s = 'array( '
            s += ' , '.join([self._php(e) for e in a.elts])
            s += ' )'
            return s

        elif c == ast.Num:
            return str(a.n)

        elif c == ast.Str:
            return "'" + a.s + "'"

        elif c == ast.For:
            s = 'foreach ( '
            s += self._php(a.iter)
            s +=' as '
            s += self._php(a.target)
            s += ') {\n'
            s += ';\n'.join([self._php(b) for b in a.body])
            s += '}'
            return s

        elif c == ast.Expr:
            return self._php(a.value) + ';\n'

        elif c == ast.Call:
            s = a.func.id
            s += '( '
            s += ' , '.join([self._php(b) for b in a.args])
            s += ' )'
            return s

        else:
            return repr(a.__class__)

if __name__ == '__main__':
    import sys
    if len(sys.argv) == 2:
        hp = HotPotato(sys.argv[1])
        print(hp.php())
    else:
        print("Usage: python -m hp FILE.py")
        exit(1)

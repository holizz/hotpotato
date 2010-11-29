#!/usr/bin/python

import ast

class HotPotato:
    def __init__(self, fn):
        self.ast = compile(open('test.py').read(),
                'test.py',
                'exec',
                ast.PyCF_ONLY_AST)

    def php(self):
        return self._php(self.ast)

    def _php(self, a):
        b = a.__class__
        if b == ast.Module:
            s = ''
            for b in a.body:
                s += self._php(b)
                s += ';\n'
            return s

        elif b == ast.Assign:
            return self._php(a.targets[0]) + ' = ' + self._php(a.value)

        elif b == ast.Name:
            return '$'+a.id

        elif b == ast.List:
            s = 'array( '
            s += ' , '.join([self._php(e) for e in a.elts])
            s += ' )'
            return s

        elif b == ast.Num:
            return str(a.n)

        elif b == ast.Str:
            return "'" + a.s + "'"

        else:
            return repr(a.__class__)

hp = HotPotato('test.py')
print(hp.php())

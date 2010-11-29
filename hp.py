#!/usr/bin/python

import ast

class HotPotato:
    def __init__(self, fn):
        self.ast = compile(open('test.py').read(),'test.py','exec', ast.PyCF_ONLY_AST)
    def php(self):
        return self._php(self.ast)
    def _php(self, a):
        if a.__class__ == ast.Module:
            s = ''
            for b in a.body:
                s += self._php(b)
            return s
        else:
            return 'UNRECOGNISED'

hp = HotPotato('test.py')
print(hp.php())

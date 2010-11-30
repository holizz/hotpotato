#!/usr/bin/python

import ast

class HotPotato:
    class Actions:
        def __init__(self, hp):
            self.hp = hp

        def Module(self, a):
            return '\n'.join([self.hp._php(b) for b in a.body])

        def Assign(self, a):
            return self.hp._php(a.targets[0]) + ' = ' + self.hp._php(a.value) + ';'

        def Name(self, a):
            return '$'+a.id

        def List(self, a):
            return 'array( ' + ' , '.join([self.hp._php(e) for e in a.elts]) + ' )'

        def Num(self, a):
            return str(a.n)

        def Str(self, a):
            return "'" + a.s + "'"

        def For(self, a):
            return 'foreach ( ' + self.hp._php(a.iter) + ' as ' + self.hp._php(a.target) + ') {\n' + ';\n'.join([self.hp._php(b) for b in a.body]) + '}'

        def Expr(self, a):
            return self.hp._php(a.value) + ';\n'

        def Call(self, a):
            return a.func.id + '( ' + ' , '.join([self.hp._php(b) for b in a.args]) + ' )'

        def If(self, a):
            if a.orelse is None:
                orelse = ''
            elif a.orelse[0].__class__ is ast.If:
                orelse = ' else' + self.hp._php(a.orelse[0])
            else:
                orelse = ' else {\n' + self.hp._php(a.orelse[0]) + '}'

            return 'if ( ' + self.hp._php(a.test) + ' ){\n' + ';\n'.join([self.hp._php(b) for b in a.body]) + '}' + orelse

        def UnaryOp(self, a):
            return self.hp._php(a.op) + ' ' + self.hp._php(a.operand)

        def Not(self, a):
            return '!'

        def Compare(self, a):
            print(dir(a))
            print(a.comparators)
            print(a.left)
            print(a.ops)
            return self.hp._php(a.left) + ' ' + self.hp._php(a.ops[0]) + ' ' + self.hp._php(a.comparators[0])

        def Eq(self, a):
            return '==='


    def __init__(self, fn):
        self.ast = compile(open(fn).read(),
                fn,
                'exec',
                ast.PyCF_ONLY_AST)

    def php(self):
        return '<?php\n'+self._php(self.ast)

    def _php(self, a):
        c = a.__class__
        actions = self.Actions(self)
        try:
            return actions.__getattribute__(c.__name__)(a)
        except AttributeError:
            return repr(a)


if __name__ == '__main__':
    import sys
    if len(sys.argv) == 2:
        hp = HotPotato(sys.argv[1])
        print(hp.php())
    else:
        print("Usage: python -m hp FILE.py")
        exit(1)

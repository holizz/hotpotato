#!/usr/bin/python

import ast

class HotPotato:
    class Actions:
        def __init__(self, hp):
            self.hp = hp

        def p(self, php):
            return self.hp._php(php)

        def Module(self, a):
            return '\n'.join([self.p(b) for b in a.body])

        def Assign(self, a):
            return self.p(a.targets[0]) + ' = ' + self.p(a.value) + ';'

        def Name(self, a):
            return '$'+a.id

        def List(self, a):
            return 'array( ' + ' , '.join([self.p(e) for e in a.elts]) + ' )'

        def Num(self, a):
            return str(a.n)

        def Str(self, a):
            return "'" + a.s + "'"

        def For(self, a):
            return 'foreach ( ' + self.p(a.iter) + ' as ' + self.p(a.target) + ') {\n' + ';\n'.join([self.p(b) for b in a.body]) + '}'

        def Expr(self, a):
            return self.p(a.value) + ';\n'

        def Call(self, a):
            return a.func.id + '( ' + ' , '.join([self.p(b) for b in a.args]) + ' )'

        def If(self, a):
            if a.orelse is None:
                orelse = ''
            elif a.orelse[0].__class__ is ast.If:
                orelse = ' else' + self.p(a.orelse[0])
            else:
                orelse = ' else {\n' + self.p(a.orelse[0]) + '}'

            return 'if ( ' + self.p(a.test) + ' ){\n' + ';\n'.join([self.p(b) for b in a.body]) + '}' + orelse

        def UnaryOp(self, a):
            return self.p(a.op) + ' ' + self.p(a.operand)

        def Not(self, a):
            return '!'

        def Compare(self, a):
            print(dir(a))
            print(a.comparators)
            print(a.left)
            print(a.ops)
            return self.p(a.left) + ' ' + self.p(a.ops[0]) + ' ' + self.p(a.comparators[0])

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

#!/usr/bin/python

import ast

class HotPotato:
    class Actions:

        special_names = {
                'False': 'false',
                'None': 'null',
                'True': 'true'
                }

        ######################################################################

        def __init__(self, hp):
            self.hp = hp

        def p(self, php):
            return self.hp._php(php)

        ## Module ############################################################

        def Module(self, a):
            return '\n'.join([self.p(b) for b in a.body])

        ## Statements ########################################################

        def Assign(self, a):
            return self.p(a.targets[0]) + ' = ' + self.p(a.value) + ';'

        def For(self, a):
            return 'foreach ( ' + self.p(a.iter) + ' as ' + self.p(a.target) + ') {\n' + ';\n'.join([self.p(b) for b in a.body]) + '}'

        def If(self, a):
            if a.orelse is None:
                orelse = ''
            elif a.orelse[0].__class__ is ast.If:
                orelse = ' else' + self.p(a.orelse[0])
            else:
                orelse = ' else {\n' + self.p(a.orelse[0]) + '}'

            return 'if ( ' + self.p(a.test) + ' ){\n' + ';\n'.join([self.p(b) for b in a.body]) + '}' + orelse

        ## Expressions #######################################################

        def Expr(self, a):
            return self.p(a.value) + ';\n'

        def Call(self, a):
            return a.func.id + '( ' + ' , '.join([self.p(b) for b in a.args]) + ' )'

        def Name(self, a):
            if a.id in self.special_names:
                return self.special_names[a.id]
            return '$'+a.id

        ## Operators #########################################################

        ## UnaryOp

        def UnaryOp(self, a):
            return self.p(a.op) + ' ' + self.p(a.operand)

        def Not(self, a):
            return '!'

        ## BinOp

        def BinOp(self, a):
            return self.p(a.left) + ' ' + self.p(a.op) + ' ' + self.p(a.right)

        def Add(self, a):
            return '+'

        ## Compare

        def Compare(self, a):
            return self.p(a.left) + ' ' + self.p(a.ops[0]) + ' ' + self.p(a.comparators[0])

        def Eq(self, a):
            return '==='

        ## Builtin types #####################################################

        def List(self, a):
            return 'array( ' + ' , '.join([self.p(e) for e in a.elts]) + ' )'

        def Num(self, a):
            return str(a.n)

        def Str(self, a):
            return "'" + a.s + "'"


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

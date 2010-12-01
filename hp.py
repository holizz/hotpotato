#!/usr/bin/python

import ast

class Macros:
    def __init__(self, hp):
        self.hp = hp

    def p(self, php):
        return self.hp._php(php)

    def _concat(self, *args):
        return ' . '.join([self.p(a) for a in args])

    def _const(self, constant):
        return constant.id


class Actions:
    special_names = {
            'False': 'false',
            'None': 'null',
            'True': 'true'
            }

    ##########################################################################

    def __init__(self, hp):
        self.hp = hp

    def p(self, php):
        return self.hp._php(php)

    ## Module ################################################################

    def Module(self, a):
        return '\n'.join([self.p(b) for b in a.body])

    ## Statements ############################################################

    def statements(self, s):
        return ';\n'.join([self.p(b) for b in s])

    def Assign(self, a):
        return self.p(a.targets[0]) + ' = ' + self.p(a.value) + ';'

    def For(self, a):
        return 'foreach ( ' + \
                self.p(a.iter) +  ' as ' +  self.p(a.target) + \
                ') {\n' + \
                self.statements(a.body) + \
                '}'

    def If(self, a):
        if a.orelse == []:
            orelse = ''
        elif a.orelse[0].__class__ is ast.If:
            orelse = ' else' + self.p(a.orelse[0])
        else:
            orelse = ' else {\n' + self.p(a.orelse[0]) + '}'

        return 'if ( ' + self.p(a.test) + ' ) {\n' + \
                self.statements(a.body) + '}' + orelse

    ## Expressions ###########################################################

    def Expr(self, a):
        return self.p(a.value) + ';\n'

    def Call(self, a):
        m = self.hp.macros(self.hp)
        if a.func.id in dir(m):
            return m.__getattribute__(a.func.id)(*a.args)
        else:
            return a.func.id + '( ' + \
                    ', '.join([self.p(b) for b in a.args]) + ' )'

    def Name(self, a):
        if a.id in self.special_names:
            return self.special_names[a.id]
        return '$'+a.id

    def Subscript(self, a):
        return self.p(a.value) + '[' + self.p(a.slice) + ']'

    def Index(self, a):
        return self.p(a.value)

    ## Operators #############################################################

    ## UnaryOp

    def UnaryOp(self, a):
        return self.p(a.op) + ' ' + self.p(a.operand)

    def Not(self, a):
        return '!'

    ## BinOp

    def BinOp(self, a):
        if type(a.op) == ast.Pow:
            return 'pow(' + self.p(a.left) + ', ' + self.p(a.right) + ')'
        return self.p(a.left) + ' ' + self.p(a.op) + ' ' + self.p(a.right)

    def Add(self, a):
        return '+'

    ## Compare

    def Compare(self, a):
        return self.p(a.left) + \
                ' ' + self.p(a.ops[0]) + ' ' + \
                self.p(a.comparators[0])

    def Eq(self, a):
        return '==='

    def NotEq(self, a):
        return '!=='

    def Lt(self, a):
        return '<'

    def Gt(self, a):
        return '>'

    def LtE(self, a):
        return '<='

    def GtE(self, a):
        return '>='

    ## Builtin types #########################################################

    def Num(self, a):
        return str(a.n)

    def Str(self, a):
        return "'" + a.s.replace('\\','\\\\').replace("'","\\'") + "'"

    def List(self, a):
        return 'array( ' + ', '.join([self.p(e) for e in a.elts]) + ' )'

    def Dict(self, a):
        return 'array(' + \
                ', '.join([self.p(k) + ' => ' + self.p(v)
                    for k,v in zip(a.keys, a.values)]) + \
                            ')'

    def NoneType(self, a):
        return 'null'


class HotPotato:
    def __init__(self, fn, debug=False, macros=Macros):
        self.debug = debug
        self.macros = macros

        self.ast = compile(open(fn).read(),
                fn,
                'exec',
                ast.PyCF_ONLY_AST)

    def php(self):
        return '<?php\n'+self._php(self.ast)

    def _php(self, a):
        c = a.__class__
        actions = Actions(self)
        try:
            return actions.__getattribute__(c.__name__)(a)
        except AttributeError:
            if self.debug:
                return repr(a)
            else:
                raise


class Compiler:
    def __init__(self, macros=Macros):
        self.macros = macros

    def compile(self, files):
        for f in files:
            hp = HotPotato(f, macros=self.macros)
            with open(f.replace('.py', '.php'), 'w+') as out:
                out.write(hp.php())

if __name__ == '__main__':
    import sys
    argv = sys.argv[1:]
    debug = False
    if '-d' in argv:
        argv.remove('-d')
        debug = True

    if len(argv) == 1:
        hp = HotPotato(argv[0], debug)
        print(hp.php())

    else:
        print("Usage: python -m hp FILE.py")
        exit(1)

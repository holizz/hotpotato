import ast

class Macros(object):
    def __init__(self, hp):
        self.hp = hp

    def p(self, php):
        return self.hp._php(php, self)

    def _concat(self, *args):
        return ' . '.join([self.p(a) for a in args])

    def _const(self, constant):
        return constant.id

    def _append(self, target, value):
        return self.p(target) + '[] = ' + self.p(value)


class Actions(object):
    special_names = {
            'False': 'false',
            'None': 'null',
            'True': 'true'
            }

    ##########################################################################

    def __init__(self, hp, parent):
        self.hp = hp
        self.parent = parent
        self.output = []
        self.statement_context = False
        self.var_count = 0

    def p(self, php):
        return self.hp._php(php, self)

    def pyhp_var(self, name):
        var = ast.Name()
        var.id = '__pyhp_' + name + '_' + str(self.var_count) + '__'
        self.var_count += 1
        return var

    def _get_context(self):
        if self.statement_context:
            return self
        return self.parent._get_context()

    ## Module ################################################################

    def Module(self, a):
        self.statement_context = True
        return self.statements(a.body)

    ## Statements ############################################################

    def statements(self, s):
        self.statement_context = True
        for b in s:
            if type(b) == str:
                self.output.append(b)
            else:
                self.output.append(self.p(b))
        return ';\n'.join(self.output + [''])

    def Assign(self, a):
        if type(a.targets[0]) == ast.Tuple:

            # $__pyhp_array__ = $values
            assign = ast.Assign()
            target = self.pyhp_var('assign')
            assign.targets = [target]
            assign.value = a.value

            assignments = [assign]

            targets = a.targets[0].elts

            for t in targets:
                # $target = $value[$n]
                assign = ast.Assign()
                assign.targets = [t]
                v = ast.Call()
                v.func = ast.Name()
                v.func.id = 'array_shift'
                v.args = [target]
                assign.value = v
                assignments.append(assign)

            return self.statements(assignments)

        else:
            return self.p(a.targets[0]) + ' = ' + self.p(a.value)

    def Expr(self, a):
        return self.p(a.value)

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

    def ListComp(self, a):
        g = a.generators[0]

        trees = []

        # $__pyhp_array__ = $values
        assign = ast.Assign()
        target = self.pyhp_var('lstcmp')
        assign.targets = [target]
        assign.value = ast.List()
        assign.value.elts = []
        trees.append(assign)

        # foreach ( $iter as $target ) { $elt }
        for_ = ast.For()
        for_.iter = g.iter
        for_.target = g.target
        for_.body = [ast.Call()]
        for_.body[0].func = ast.Name
        for_.body[0].func.id = '_append'
        for_.body[0].args = [target, a.elt]
        trees.append(for_)

        self._get_context().output.append(self.statements(trees))
        return self.p(target)

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

    def Mult(self, a):
        return '*'

    def Mod(self, a):
        return '%'

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

    def Tuple(self, a):
        return self.List(a)

    def Dict(self, a):
        return 'array(' + \
                ', '.join([self.p(k) + ' => ' + self.p(v)
                    for k,v in zip(a.keys, a.values)]) + \
                            ')'

    def NoneType(self, a):
        return 'null'


class HotPotato(object):
    def __init__(self, debug=False, macros=Macros):
        self.debug = debug
        self.macros = macros

    def load(self, f):
        self.ast = compile(open(f).read(),
                f,
                'exec',
                ast.PyCF_ONLY_AST)

    def php(self):
        return '<?php\n'+self._php(self.ast, None)

    def _php(self, a, parent):
        c = a.__class__
        actions = Actions(self, parent)
        try:
            return actions.__getattribute__(c.__name__)(a)
        except AttributeError:
            if self.debug:
                return repr(a)
            else:
                raise


class CommandLine(object):
    def __init__(self, hotpotato=None):
        self.hotpotato = hotpotato if hotpotato else HotPotato()

    def run(self):
        import sys
        argv = sys.argv[1:]
        debug = False
        if '-d' in argv:
            argv.remove('-d')
            debug = True
        self.hotpotato.debug = debug

        if len(argv) == 1:
            self.hotpotato.load(argv[0])
            print(self.hotpotato.php().strip())

        else:
            print("Usage: pyhp FILE")
            exit(1)
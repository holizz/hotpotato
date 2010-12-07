import ast


class Macros(object):
    def __init__(self, hp):
        self.hp = hp

    def __p(self, php):
        return self.hp._php(php, self)

    def _concat(self, *args):
        return ' . '.join([self.__p(a) for a in args])

    def _const(self, constant):
        return constant.id

    def _append(self, target, value):
        return self.__p(target) + '[] = ' + self.__p(value)


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
        var = ast.Name(id='__pyhp_' + name + '_' + str(self.var_count) + '__')
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
            target = self.pyhp_var('assign')
            assign = ast.Assign(targets=[target],
                                value=a.value)

            assignments = [assign]

            targets = a.targets[0].elts

            for t in targets:
                # $target = $value[$n]
                assign = ast.Assign(targets=[t],
                                    value=ast.Call(func=ast.Name(id='array_shift'),
                                                   args=[target]))
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
        if a.func.id in dir(m) and not a.func.id.startswith('__'):
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
        target = self.pyhp_var('lstcmp')
        assign = ast.Assign(targets=[target],
                            value=ast.List(elts=[]))
        trees.append(assign)

        # foreach ( $iter as $target ) { $elt }
        for_ = ast.For(iter=g.iter,
                       target=g.target,
                       body=[ast.Call(func=ast.Name(id='_append'),
                                      args=[target, a.elt])])
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

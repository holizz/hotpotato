import ast


class Macros:
    def __init__(self, hp):
        self.hp = hp

    def __p(self, php):
        return self.hp._php(php, self)

    ## Callable macros

    def _concat(self, *args):
        """Replace PHP's . operator

        """
        return ' . '.join([self.__p(a) for a in args])

    def _append(self, target, value):
        """Replace PHP's []= idiom

        """
        return self.__p(target) + '[] = ' + self.__p(value) + ';'

    def _new(self, cls):
        """Replace PHP's "new" construct

        """
        return 'new ' + cls.id

    def _raw(self, name):
        """For names that aren't $variables

        """
        return name.id

    def _static(self, target, value):
        """PHP's "static"

        """
        return 'static ' + self.__p(ast.Assign(targets=[target],value=value))

    def _cast(self, target, value):
        """_cast(target, value) == (target) value

        """
        return '(' + target.id + ') ' + self.__p(value)

    def _ref(self, var):
        """_ref(var) == &$var

        """
        return '&' + self.__p(var)

    ## Decorators

    def _abstract(self, s):
        return 'abstract ' + s


class Actions:
    special_names = {
            'False': 'false',
            'None': 'null',
            'True': 'true'
            }

    ##########################################################################

    def __init__(self, hp, parent):
        self.hp = hp
        self.parent = parent

        self.macros = self.hp.macros(self.hp)

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

    def statements(self, s):
        self.output = []
        self.statement_context = True
        for b in s:
            if isinstance(b,str):
                self.output.append(b)
            else:
                self.output.append(self.p(b))
        return '\n'.join(self.output + [''])

    def macro(self, func, *args):
        return getattr(self.macros, func)(*args)

    ## Bits and bobs #########################################################

    def arguments(self, a):
        return ', '.join([self.p(b) for b in a.args])

    def arg(self, a):
        return '$' + a.arg

    ## Module ################################################################

    def Module(self, a):
        self.statement_context = True
        return self.statements(a.body)

    ## Statements ############################################################

    def Assign(self, a):
        if isinstance(a.targets[0], ast.Tuple):

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
            return self.p(a.targets[0]) + ' = ' + self.p(a.value) + ';'

    def Delete(self, a):
        return self.p(ast.Call(func=ast.Name(id='unset'),
                               args=a.targets)) + ';'

    def AugAssign(self, a):
        return self.p(a.target) + ' ' + self.p(a.op) + '= ' + self.p(a.value) + ';'

    def Expr(self, a):
        return self.p(a.value) + ';'

    def For(self, a):
        return 'foreach ( ' + \
                self.p(a.iter) +  ' as ' +  self.p(a.target) + \
                ' ) {\n' + \
                self.statements(a.body) + \
                '}'

    def While(self, a):
        return 'while ( ' + self.p(a.test) + ' ) {\n' + \
                self.statements(a.body) + '}'

    def If(self, a):
        if a.orelse == []:
            orelse = ''
        elif a.orelse[0].__class__ is ast.If:
            orelse = ' else' + self.p(a.orelse[0])
        else:
            orelse = ' else {\n' + self.statements(a.orelse) + '}'

        return 'if ( ' + self.p(a.test) + ' ) {\n' + \
                self.statements(a.body) + '}' + orelse

    def FunctionDef(self, a):
        return 'function ' + a.name + '(' + self.p(a.args) + ') {\n' + \
                self.statements(a.body) + '}'

    def Return(self, a):
        return 'return ' + self.p(a.value) + ';'

    def ClassDef(self, a):
        extends = ''
        if a.bases != []:
            extends = ' extends ' + ', '.join([n.id for n in a.bases])

        r = 'class ' + a.name + extends + ' {\n' + \
            self.statements(a.body) + '}'

        for func in reversed(a.decorator_list):
            r = self.macro(func.id, r)

        return r

    def Pass(self, a):
        return ''

    def Global(self, a):
        return 'global ' + ', '.join(['$' + n for n in a.names]) + ';'

    ## Expressions ###########################################################

    def Call(self, a):
        if isinstance(a.func, ast.Attribute):
            f = self.p(a.func.value) + '->' + a.func.attr
            f = self.p(a.func)

        elif isinstance(a.func, ast.Name):
            if a.func.id in dir(self.macros) \
                    and not a.func.id.startswith('__'):
                return self.macro(a.func.id, *a.args)
            else:
                f = a.func.id

        return f + '( ' +  ', '.join([self.p(b) for b in a.args]) + ' )'

    def Name(self, a):
        if a.id in self.special_names:
            return self.special_names[a.id]
        return '$' + a.id

    def Attribute(self, a):
        return self.p(a.value) + '->' + a.attr

    def Subscript(self, a):
        return self.p(a.value) + '[' + self.p(a.slice) + ']'

    def Index(self, a):
        return self.p(a.value)

    def IfExp(self, a):
        return self.p(a.test) + ' ? ' + self.p(a.body) + ' : ' + self.p(a.orelse)

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
        if isinstance(a.op, ast.Pow):
            return 'pow(' + self.p(a.left) + ', ' + self.p(a.right) + ')'
        return self.p(a.left) + ' ' + self.p(a.op) + ' ' + self.p(a.right)

    # Bitwise

    def BitOr(self, a):
        return '|'

    def BitAnd(self, a):
        return '&'

    # Mathematical

    def Add(self, a):
        return '+'

    def Sub(self, a):
        return '-'

    def Mult(self, a):
        return '*'

    def Div(self, a):
        return '/'

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

import ast

from hotpotato.profile import default


class HotPotato(object):
    def __init__(self, debug=False, actions=default.Actions, macros=default.Macros):
        self.debug = debug
        self.actions = actions
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
        actions = self.actions(self, parent)
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

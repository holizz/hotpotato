import hp

class Macros(hp.Macros):
    def _cc(self, *args):
        return ' ***** '.join([self.p(a) for a in args])

hp.Compiler(Macros).compile(['test.py'])

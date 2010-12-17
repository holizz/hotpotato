#!/usr/bin/env python

import glob
import io
import os
import re
import subprocess
import sys
import tempfile

import hotpotato


class Test:
    def __init__(self, fn):
        self.fn = fn
        self.parse()

        self.tty = os.isatty(sys.stdout.fileno())

        # Setting $_GET and $_POST for certain tests
        self.php_header = '<?php'
        for x in ['post', 'get']:
            self.php_header += """
                $%(x)s = getenv('PHP_%(X)s');
                if($%(x)s)
                    parse_str($%(x)s, &$_%(X)s);
                """ % {'x':x,'X':x.upper()}
        self.php_header += '?>'

    def _colour(self, colour, s):
        if self.tty:
            return '\x1b[%dm%s\x1b[0m' % (colour, s)
        else:
            return s

    def _red(self, s):
        return self._colour(31, s)

    def _green(self, s):
        return self._colour(32, s)

    def parse(self):
        header = {'--TEST--':        'test',
                  '--FILE--':        'file',
                  '--EXPECT--':      'expect',
                  '--EXPECTF--':     'expectf',
                  '--EXPECTREGEX--': 'expectregex',
                  '--SKIPIF--':      'skipif',
                  '--STDIN--':       'stdin',
                  '--POST--':        'post',
                  '--GET--':         'get'}

        data = {'test':        None,
                'file':        None,
                'expect':      None,
                'expectf':     None,
                'expectregex': None,
                'skipif':      None,
                'stdin':       '',
                'post':        '',
                'get':         ''}

        with open(self.fn) as f:
            for line in f.readlines():
                if line.strip() in header:
                    mode = header[line.strip()]
                else:
                    if data[mode] is None:
                        data[mode] = ''
                    data[mode] += line

        new_data = {}
        for k,v in data.items():
            if isinstance(data[k], str):
                new_data[k] = data[k].rstrip('\n')
            else:
                new_data[k] = data[k]

        self.test        = new_data['test']
        self.file        = new_data['file']
        self.expect      = new_data['expect']
        self.expectf     = new_data['expectf']
        self.expectregex = new_data['expectregex']
        self.skipif      = new_data['skipif']
        self.stdin       = new_data['stdin'] + '\n'
        self.post        = new_data['post']
        self.get         = new_data['get']

    def run(self):
        print('Running test: '+self.fn)
        print('              '+self.test)

        # Compile PyHP to PHP with default options
        hp = hotpotato.HotPotato()
        hp.load('file.py', self.file)
        self.pyhp_output = hp.php()

        # Save PHP to a tmp file
        fd,path = tempfile.mkstemp(dir=os.path.dirname(self.fn))
        os.write(fd, bytes(self.php_header, 'utf-8'))
        if self.skipif is not None:
            os.write(fd, bytes(self.skipif, 'utf-8'))
        os.write(fd, bytes(self.pyhp_output, 'utf-8'))

        # Execute PHP
        env = {'PHP_POST': self.post,
               'PHP_GET': self.get}
        php = subprocess.Popen(['php', '--no-php-ini', path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
        self.raw_php_output = php.communicate(input=bytes(self.stdin, 'utf-8'))[0]
        self.php_output = self.raw_php_output.decode('utf-8')

        os.close(fd)
        os.unlink(path)

        self.php_output = self.php_output.rstrip('\n')

        if self.expect is not None:
            assertion = self.php_output == self.expect

        elif self.expectf is not None:
            # Convert self.expectf to re
            e = re.escape(self.expectf)
            e = re.sub(r'\\\n', '\n', e)
            e = re.sub(r'\\%d', r'\d+', e)
            e = re.sub(r'\\%i', r'[+-]?\d+', e)
            e = re.sub(r'\\%f', r'[+-]?\d+(\.\d+)?', e)
            e = re.sub(r'\\%s', r'.+', e)
            e = re.sub(r'\\%x', r'[0-9a-fA-F]+', e)
            e = re.sub(r'\\%c', r'\w', e)
            e = '^'+e+'$'
            regex = re.compile(e)

            assertion = regex.match(self.php_output) is not None

        elif self.expectregex is not None:
            assertion = re.match(self.expectregex, self.php_output, re.DOTALL)

        else:
            raise RuntimeError

        try:
            assert assertion
        except AssertionError:
            print(self._red('Failure!'))
            if self.expect is not None:
                print('Expected\n%s\nto be\n%s' % (repr(self.php_output), repr(self.expect)))
            elif self.expectf is not None:
                print('Expected\n%s\nto match\n%s' % (repr(self.php_output), repr(self.expectf)))
            elif self.expectregex is not None:
                print('Expected\n%s\nto match\n%s' % (repr(self.php_output), repr(self.expectregex)))
            raise
        else:
            print(self._green('Success!'))


if __name__ == '__main__':
    argv = sys.argv[1:]

    tests = None

    if argv:
        tests = argv

    if not tests:
        tests = sorted(glob.glob('tests/*/*.pyhpt'))

    for test in tests:
        Test(test).run()

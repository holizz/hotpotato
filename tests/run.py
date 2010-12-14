#!/usr/bin/env python

import glob
import io
import os
import re
import subprocess
import sys

import hotpotato


class Test:
    def __init__(self, fn):
        self.fn = fn
        self.parse()

    def parse(self):
        header = {'--TEST--':    'test',
                  '--FILE--':    'file',
                  '--EXPECT--':  'expect',
                  '--EXPECTF--': 'expectf'}

        data = {'test':    None,
                'file':    None,
                'expect':  None,
                'expectf': None}

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
            if v is not None and v.endswith('\n'):
                v = v[:-1]
            new_data[k] = v

        self.test    = new_data['test']
        self.file    = new_data['file']
        self.expect  = new_data['expect']
        self.expectf = new_data['expectf']

    def run(self):
        print('Running test: '+self.fn)
        print('              '+self.test)

        #php = subprocess.Popen(['php'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        #print(php.communicate(input=bytes(self.file, 'utf-8'))[0])

        # Compile PyHP to PHP with default options
        hp = hotpotato.HotPotato()
        hp.load('file.py', self.file)
        self.pyhp_output = hp.php()

        # Execute PHP
        php = subprocess.Popen(['php'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        self.raw_php_output = php.communicate(input=bytes(self.pyhp_output, 'utf-8'))[0]
        self.php_output = self.raw_php_output.decode('utf-8')

        if self.expect is not None:
            assertion = self.php_output == self.expect

        elif self.expectf is not None:
            # Convert self.expectf to re
            e = re.escape(self.expectf)
            e = re.sub(r'\\\n', '\n', e)
            e = re.sub(r'\\%d', r'\d+', e)
            e = re.sub(r'\\%i', r'[+-]?\d+', e)
            e = re.sub(r'\\%f', r'[+-]?\d+(\.\d+)?', e)
            e = re.sub(r'\\%s', r'\w+', e)
            e = re.sub(r'\\%x', r'[0-9a-fA-F]+', e)
            e = re.sub(r'\\%c', r'\w', e)
            e = '^'+e+'$'
            regex = re.compile(e)

            assertion = regex.match(self.php_output) is not None

        else:
            raise RuntimeError

        try:
            assert assertion
        except AssertionError:
            print('Failure!')
            if self.expect is not None:
                print('Expected\n%s\nto be\n%s' % (repr(self.php_output), repr(self.expect)))
            elif self.expectf is not None:
                print('Expected\n%s\nto match\n%s' % (repr(self.php_output), repr(self.expectf)))
            raise
        else:
            print('Success!')


if __name__ == '__main__':
    argv = sys.argv[1:]

    tests = None

    if len(argv) > 0:
        tests = argv

    if tests is None:
        tests = sorted(glob.glob('tests/*/*.pyhpt'))

    for test in tests:
        Test(test).run()

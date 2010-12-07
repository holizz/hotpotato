import distutils.core
import os

distutils.core.setup(
        name = 'hotpotato',
        version = open(os.path.join(os.path.dirname(__file__),'VERSION')).read().strip(),
        description = 'Python to PHP compiler',
        author = 'Tom Adams',
        author_email = 'tom@holizz.com',
        url = 'http://github.com/holizz/hotpotato',
        license = 'ISC',

        classifiers = [
            'Intended Audience :: Developers',
            'License :: OSI Approved :: ISC License (ISCL)',
            'Programming Language :: PHP',
            'Programming Language :: Python',
            'Topic :: Software Development :: Compilers',
            ],

        packages = ['hotpotato', 'hotpotato.profile'],
        scripts = ['bin/pyhp']
        )

from setuptools import setup

setup(
    name='herd',
    version='0.0.3.dev1',
    license='MIT',
    description='Small cluster automation',
    author='Ben Picolo',
    author_email='be.picolo@gmail.com',
    url='https://github.com/bpicolo/herd',
    packages=['herd'],
    classifiers=[
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.4',
    ],
    install_requires=[
        'cached-property',
        'paramiko',
        'python-digitalocean',
        'pytoml'
    ],
    scripts=[
        'bin/herd',
    ]
)

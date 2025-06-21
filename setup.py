from setuptools import setup

setup(
    name = 'slabcli',
    version = '0.1.0',
    packages = ['slabcli'],
    entry_points = {
        'console_scripts': [
            'slabcli = slabcli.__main__:main'
        ]
    })

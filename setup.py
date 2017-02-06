from setuptools import setup

from pip.req import parse_requirements

# parse_requirements() returns generator of pip.req.InstallRequirement objects
install_reqs = parse_requirements("requirements.txt", session=False)

reqs = [str(ir.req) for ir in install_reqs]

setup(
    name='silica',
    version='0.1-alpha',
    description='A DSL for expressing FSMs using co-routines that compile to hardware',
    packages=["silica", "test"],
    
    install_requires=reqs
    )

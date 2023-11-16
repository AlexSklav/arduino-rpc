#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import versioneer

from setuptools import setup

properties = dict(
    package_name='arduino_rpc',
    url='https://github.com/sci-bots/arduino-rpc',
    version=versioneer.get_version(),
    short_description='Code generation for memory-efficient '
                      'remote-procedure-calls between a host CPU (Python) and a device (C++) '
                      '(e.g., Arduino).',
    long_description='The main features of this package include: 1) Extract '
                     'method signatures from user-defined C++ class, 2) Assign a unique '
                     '*"command code"* to each method, 3) Generate a `CommandProcessor<T>` '
                     'C++ class, which calls appropriate method on instance of user type '
                     'provided the corresponding serialized command array, and 4) Generate a '
                     '`Proxy` Python class to call methods on remote device by serializing '
                     'Python method call as command request and decoding command response '
                     'from device as Python type(s).',
    category='Communication',
    author='Christian Fobel',
    author_email='christian@fobel.net')

setup(name=properties['package_name'].replace('_', '-'),
      version=versioneer.get_version(),
      cmdclass=versioneer.get_cmdclass(),
      description=properties['short_description'],
      long_description='\n'.join([properties['short_description'],
                                  properties['long_description']]),
      author_email=properties['author_email'],
      author=properties['author'],
      url=properties['url'],
      # Install data listed in `MANIFEST.in`
      include_package_data=True,
      license='MIT',
      packages=[properties['package_name']])

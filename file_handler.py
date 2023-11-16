# coding: utf-8
import argparse
import versioneer

import platformio_helpers as pioh

from typing import Dict
from importlib import import_module

from path_helpers import path
from arduino_rpc.helpers import generate_arduino_library_properties


def get_properties(**kwargs) -> Dict:
    version = versioneer.get_version()

    module_name = kwargs.get('module_name')
    package_name = kwargs.get('package_name')
    url = f'https://github.com/sci-bots/{package_name}'

    properties = dict(package_name=package_name,
                      display_name=package_name,
                      manufacturer='Wheeler Lab',
                      software_version=version,
                      url=url
                      )

    meta = dict(short_description='Code generation for memory-efficient remote-procedure-calls '
                                  'between a host CPU (Python) and a device (C++) (e.g., Arduino).',
                long_description='The main features of this package include: 1) Extract method signatures '
                                 'from user-defined C++ class, 2) Assign a unique *"command code"* to each method, '
                                 '3) Generate a `CommandProcessor<T>` C++ class, which calls appropriate method '
                                 'on instance of user type provided the corresponding serialized command array, and '
                                 '4) Generate a `Proxy` Python class to call methods on remote device by serializing'
                                 'Python method call as command request and decoding command response '
                                 'from device as Python type(s).',
                author='Christian Fobel',
                author_email='christian@fobel.net',
                version=version,
                license='MIT',
                category='Communication',
                architectures='avr',
                )

    lib_properties = {**properties, **meta}

    options = dict(rpc_module=import_module(module_name),
                   PROPERTIES=properties,
                   LIB_PROPERTIES=lib_properties,
                   )
    return {**kwargs, **options}


def transfer(**kwargs) -> None:
    # Copy Arduino library to Conda include directory
    source_dir = kwargs.get('source_dir')
    module_name = kwargs.get('module_name')
    lib_name = kwargs.get('lib_name')
    source_dir = path(source_dir).joinpath(module_name, 'Arduino', 'library', lib_name)
    install_dir = pioh.conda_arduino_include_path().joinpath(lib_name)
    source_dir.copytree(install_dir)
    print(f"Copied tree from '{source_dir}' to '{install_dir}'")


def cli_parser():
    parser = argparse.ArgumentParser(description='Transfer header files to include directory.')
    parser.add_argument('source_dir')
    parser.add_argument('prefix')
    parser.add_argument('package_name')
    parser.add_argument('module_name')
    parser.add_argument('lib_name')

    args = parser.parse_args()
    execute(**vars(args))


def execute(**kwargs):
    options = get_properties(**kwargs)

    top = '>' * 180
    print(top)

    generate_arduino_library_properties(options)
    transfer(**kwargs)

    print('<' * len(top))


if __name__ == '__main__':
    cli_parser()

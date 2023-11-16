# coding: utf-8
import re
import jinja2
import inspect

from typing import Optional, List, Dict

from path_helpers import path
from arduino_helpers import sketchbook_directory
from clang_helpers.data_frame import underscore_to_camelcase

from . import get_library_directory


def verify_library_directory(lib_options: Dict) -> path:
    """
    Must be called from task function accepting `LIB_CMDOPTS` as `cmdopts`.
    """
    calling_function_name = inspect.currentframe().f_back.f_code.co_name

    default_lib_dir = lib_options['rpc_module'].get_lib_directory()
    camelcase_name = lib_options['LIB_PROPERTIES'].get('lib_out_dir', None)

    if hasattr(lib_options, calling_function_name):
        cmd_opts = getattr(lib_options, calling_function_name)
        output_dir = path(getattr(cmd_opts, 'lib_out_dir', default_lib_dir))
    else:
        output_dir = default_lib_dir

    if camelcase_name:
        camel_name = camelcase_name
    else:
        camel_name = underscore_to_camelcase(lib_options['module_name'])

    library_dir = output_dir.joinpath(camel_name)
    library_dir.makedirs(exist_ok=True)
    return library_dir


def recursive_overwrite(src: path, dest: path, ignore: Optional[List] = None) -> None:
    """
    Copy a directory recursively
    """
    for file in src.walkfiles(ignore):
        dest_ = dest.joinpath(file.relpathto(src))
        dest_.parent.makedirs(exist_ok=True)
        file.copy2(dest_)
        print(f'Coping {file} -> {dest_}')


def install_arduino_library(lib_options: Dict, **kwargs):
    """Overrides install to copy an Arduino library to sketch library directory."""
    ignore = lib_options.get('ignore', None) or kwargs.get('ignore', None)

    arduino_lib_source = verify_library_directory(lib_options)
    arduino_lib_destination = sketchbook_directory().joinpath('libraries', arduino_lib_source.name)
    recursive_overwrite(arduino_lib_source, arduino_lib_destination, ignore=ignore)
    print(f'Copied {arduino_lib_source} -> {arduino_lib_destination}')


def generate_arduino_library_properties(lib_options: Dict) -> None:
    template_str = get_library_directory().joinpath('library.properties.t').text()

    template = jinja2.Template(template_str)

    library_dir = verify_library_directory(lib_options)
    library_properties = library_dir.joinpath('library.properties')

    camel_name = underscore_to_camelcase(lib_options['module_name'])

    version = re.sub(r'[^\d\.]+', '', lib_options['LIB_PROPERTIES'].get('version', '0.1.0'))
    version = re.sub(r'^([^\.]+.[^\.]+.[^\.]+)\..*', r'\1', version)

    rendered_template = template.render(camel_name=camel_name, lib_version=version,
                                        **lib_options['LIB_PROPERTIES'])
    library_properties.write_text(rendered_template)

    print(f'Generated {library_properties.name} > {library_properties}')


def copy_existing_headers(lib_options: Dict, **kwargs) -> None:
    ignore = lib_options.get('ignore', None) or kwargs.get('ignore', None)

    project_lib_dir = verify_library_directory(lib_options)

    source_dir = lib_options['rpc_module'].get_lib_directory()

    output_dir = project_lib_dir.parent
    if source_dir == output_dir:
        print('Output library directory is same as source - do not copy.')
    else:
        print('Output library directory differs from source - copy.')
        recursive_overwrite(source_dir, output_dir, ignore=ignore)


def build_arduino_library(lib_options: Dict, **kwargs) -> None:
    copy_existing_headers(lib_options, **kwargs)
    generate_arduino_library_properties(lib_options)

    import zipfile

    library_dir = verify_library_directory(lib_options)
    zf = zipfile.ZipFile(library_dir + '.zip', mode='w')

    for f in library_dir.walkfiles():
        zf.write(f, arcname=library_dir.relpathto(f))
    zf.close()

# coding: utf-8
import nadamq
import nanopb_helpers

from typing import Dict, List
from path_helpers import path
from platformio_helpers import conda_arduino_include_path

from ._version import get_versions

__version__ = get_versions()['version']
del get_versions


def package_path() -> path:
    return path(__file__).parent


def get_library_directory() -> path:
    """
    Return directory containing the Arduino library headers.
    """
    return package_path().joinpath('Arduino', 'library')


def get_lib_directory() -> path:
    """
    Wrapper function to make API compatible with `base-node-rpc` package.
    """
    return get_library_directory()


def get_includes() -> List[path]:
    """
    Return directories containing the Arduino header files.

    Notes
    =====

    For example:

        import arduino_rpc
        ...
        print ' '.join(['-I%s' % i for i in arduino_rpc.get_includes()])
        ...

    """
    includes = (list(get_library_directory().walkdirs('src')) +
                list(conda_arduino_include_path().walkdirs()))
    return includes


def get_sources() -> List[path]:
    """
    Return Arduino source file paths.  This includes any supplementary source
    files that are not contained in Arduino libraries.
    """
    return nadamq.get_sources() + nanopb_helpers.get_sources()


def get_firmwares() -> Dict[str, List[path]]:
    """
    Return compiled Arduino hex file paths.

    This function may be used to locate firmware binaries that are available
    for flashing to [Arduino][1] boards.

    [1]: http://arduino.cc
    """
    return {board_dir.name: [f.abspath() for f in board_dir.walkfiles('*.hex')]
            for board_dir in package_path().joinpath('firmware').dirs()}

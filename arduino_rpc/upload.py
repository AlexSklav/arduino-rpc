# coding: utf-8
from typing import Optional

from arduino_helpers.context import auto_context, Board, Uploader, ArduinoContext
from serial_device import get_serial_ports


def upload_firmware(firmware_path: str, board_name: str, port: str = None,
                    arduino_install_home: str = None, **kwargs) -> None:
    """
    Upload the specified firmware file to the specified board.
    """
    context = auto_context() if arduino_install_home is None else ArduinoContext(arduino_install_home)
    board = Board(context, board_name)
    uploader = Uploader(board)
    available_ports = get_serial_ports()
    if port is None:
        # No serial port was specified.
        if len(available_ports) == 1:
            # There is only one serial port available, so select it automatically.
            port = available_ports[0]
        else:
            raise IOError(f'No serial port was specified. Please select one of the following ports: {available_ports}')
    uploader.upload(firmware_path, port, **kwargs)


def upload(board_name: str, get_firmware: callable, port: str = None,
           arduino_install_home: str = None, **kwargs) -> None:
    """
    Upload the first firmware that matches the specified board type.
    """
    firmware_path = get_firmware(board_name)
    upload_firmware(firmware_path, board_name, port, arduino_install_home, **kwargs)


def get_arg_parser():
    from argparse import ArgumentParser
    from path_helpers import path

    parser = ArgumentParser(description='Upload firmware to Arduino board.')
    parser.add_argument('board_name', type=path, default=None)
    parser.add_argument('-p', '--port', default=None)
    parser.add_argument('-V', '--skip-verify', action='store_true')
    parser.add_argument('--arduino-install-home', type=path, default=None)
    return parser


def parse_args(args=None):
    """Parses arguments, returns (options, args)."""
    import sys

    if args is None:
        args = sys.argv

    parser = get_arg_parser()

    args = parser.parse_args()
    return args

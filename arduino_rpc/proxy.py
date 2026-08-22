# coding: utf-8
import time

import numpy as np
from nadamq.NadaMq import cPacketParser

#: Default time (in seconds) to wait for a complete response packet.
DEFAULT_TIMEOUT_S = 5.
#: Time (in seconds) to sleep between polls when no data is available.
POLL_INTERVAL_S = 1e-3


class ProxyBase:
    def _send_command(self, packet, timeout_s: float = DEFAULT_TIMEOUT_S):
        """
        Write `packet` to the serial device and return the parsed response.

        Parameters
        ----------
        packet
            Packet to send.
        timeout_s : float, optional
            Maximum time (in seconds) to wait for a complete response packet.
            Use `None` (or a non-positive value) to wait indefinitely.

        Raises
        ------
        IOError
            If parsing fails, or if no complete response is received within
            `timeout_s` seconds.

        Notes
        -----
        `parser.message_completed` is set by the `parser.parse()` call that
        consumes the final byte of a packet, so the flag is checked after each
        `parse()` call.  Empty reads sleep briefly rather than spinning at
        100% CPU.
        """
        self._serial.write(packet.tobytes())
        parser = cPacketParser()
        result = None

        start = time.time()

        while True:
            response = self._serial.read(self._serial.in_waiting)
            if not response:
                if timeout_s and timeout_s > 0 and (time.time() - start) > timeout_s:
                    raise IOError(f'Timed out after {timeout_s} seconds waiting for response.')
                # Avoid busy-waiting at 100% CPU while the device responds.
                time.sleep(POLL_INTERVAL_S)
                continue
            result = parser.parse(np.frombuffer(response, dtype='uint8'))
            if parser.message_completed:
                break
            elif parser.error:
                raise IOError('Error parsing.')
            if timeout_s and timeout_s > 0 and (time.time() - start) > timeout_s:
                raise IOError(f'Timed out after {timeout_s} seconds waiting for a complete response packet.')
        return result

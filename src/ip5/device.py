"""Serial communication with the Philips Expression IP5.

The monitor continuously sends ASCII records terminated by CRLF:

    <device name>,<patient id>,<MM/DD/YYYY>,<HH:MM:SS>,<code>,<unit>,<value>,<code>,<unit>,<value>,...

A value of '?' means that the parameter is configured but has no valid value.
"""
import queue
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime

import serial
import serial.tools.list_ports

from .codes import dataName, unitName

BAUDRATE = 9600
# seconds without a complete record before the device is reported as silent
COMMUNICATION_TIMEOUT = 3.0


@dataclass
class Measurement:
    name: str
    unit: str
    value: float | None  # None when the device sends '?'


@dataclass
class Record:
    device_name: str
    patient_id: str
    device_time: datetime
    pc_time: datetime
    measurements: dict[str, Measurement] = field(default_factory=dict)


def parseRecord(line, pc_time=None):
    """Parse one record (without CRLF). Raises ValueError on malformed input."""
    fields = [f.strip() for f in line.split(',')]
    if len(fields) < 4:
        raise ValueError(f'Too few fields in record: {line!r}')
    device_name, patient_id, date_, time_ = fields[:4]
    try:
        device_time = datetime.strptime(date_ + time_, '%m/%d/%Y%H:%M:%S')
    except ValueError:
        raise ValueError(f'Incorrect date/time in record: {line!r}') from None

    data_fields = fields[4:]
    # drop a trailing empty field caused by a terminating comma
    if len(data_fields) % 3 == 1 and data_fields[-1] == '':
        data_fields = data_fields[:-1]
    if len(data_fields) % 3 != 0:
        raise ValueError(f'Data fields are not a multiple of 3 in record: {line!r}')

    record = Record(device_name, patient_id, device_time, pc_time or datetime.now())
    for i in range(0, len(data_fields), 3):
        code, unit_code, value = data_fields[i:i + 3]
        name = dataName(code)
        value = None if value == '?' else float(value)
        record.measurements[name] = Measurement(name, unitName(unit_code), value)
    return record


def listSerialPorts():
    return sorted(p.device for p in serial.tools.list_ports.comports())


class DeviceReader(threading.Thread):
    """Reads records from the serial port in a background thread.

    Everything is reported through `events`, a queue of (kind, payload) tuples:
        ('status', str)   - human readable connection status
        ('connected', None) / ('silent', None)
        ('record', Record)
        ('parse_error', str)
        ('error', str)    - fatal, thread has stopped
        ('stopped', None)
    """

    def __init__(self, port, events: queue.Queue, serial_factory=None):
        super().__init__(daemon=True)
        self.port_name = port
        self.events = events
        self._serial_factory = serial_factory or self._openSerial
        self._stop_event = threading.Event()

    def _openSerial(self, port):
        return serial.Serial(port=port, baudrate=BAUDRATE,
                             bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,
                             stopbits=serial.STOPBITS_ONE, timeout=0.2, exclusive=True)

    def stop(self):
        self._stop_event.set()

    def _emit(self, kind, payload=None):
        self.events.put((kind, payload))

    def run(self):
        port = None
        try:
            self._emit('status', f'Opening {self.port_name}…')
            port = self._serial_factory(self.port_name)
            self._resetPort(port)
            self._emit('status', 'Waiting for IP5…')
            self._readLoop(port)
        except Exception as e:
            self._emit('error', f'{type(e).__name__}: {e}')
        finally:
            if port is not None:
                try:
                    port.close()
                except Exception:
                    pass
            self._emit('stopped')

    def _resetPort(self, port, timeout=5.0):
        # reset_input_buffer does not empty the buffer of some usb to rs232 converters,
        # keep flushing until nothing is waiting
        t0 = time.monotonic()
        port.write(b'\x00')
        while port.in_waiting and not self._stop_event.is_set():
            port.reset_input_buffer()
            port.write(b'\x00')
            time.sleep(0.05)
            if time.monotonic() - t0 > timeout:
                break

    def _readLoop(self, port):
        buffer = b''
        found_start = False  # first line is most likely partial, discard it
        last_record = time.monotonic()
        silent = True
        while not self._stop_event.is_set():
            chunk = port.read(port.in_waiting or 1)
            if chunk:
                buffer += chunk
                *lines, buffer = buffer.split(b'\r\n')
                for line in lines:
                    if not found_start:
                        found_start = True
                        continue
                    last_record = time.monotonic()
                    if silent:
                        silent = False
                        self._emit('connected')
                    self._handleLine(line)
                # protect against garbage without line breaks
                if len(buffer) > 1_000_000:
                    buffer = b''
            if not silent and time.monotonic() - last_record > COMMUNICATION_TIMEOUT:
                silent = True
                self._emit('silent')

    def _handleLine(self, line):
        if not line.strip(b'\x00 \t'):
            return
        try:
            record = parseRecord(line.decode('ascii', errors='replace'))
        except ValueError as e:
            self._emit('parse_error', str(e))
        else:
            self._emit('record', record)

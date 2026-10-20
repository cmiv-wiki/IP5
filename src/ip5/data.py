"""In-memory storage of received data and TSV recording."""
import csv
from collections import deque
from datetime import datetime
from pathlib import Path

from .codes import DATA_CODES, NON_PERIODIC_DATA

# data points kept per parameter for the monitor (~5.5 h at 1 Hz)
BUFFER_SIZE = 20000


class DataSeries:
    def __init__(self, name):
        self.name = name
        self.unit = 'mmHg' if name in NON_PERIODIC_DATA else ''
        self.available = False  # has been sent by the device
        self.value = None  # latest value
        self.last_update = None  # device time of latest value
        self.times = deque(maxlen=BUFFER_SIZE)  # device time
        self.values = deque(maxlen=BUFFER_SIZE)

    def add(self, device_time, unit, value):
        self.available = True
        if unit != self.unit:
            # values with different units can't share a plot
            self.times.clear()
            self.values.clear()
            self.unit = unit
        if value is not None:
            self.value = value
            self.last_update = device_time
            self.times.append(device_time)
            self.values.append(value)


class DataStore:
    def __init__(self):
        self.series = {name: DataSeries(name) for name in DATA_CODES}
        self.device_name = ''
        self.latest_record = None

    def add(self, record):
        self.device_name = record.device_name
        self.latest_record = record
        for m in record.measurements.values():
            if m.name not in self.series:
                self.series[m.name] = DataSeries(m.name)
            self.series[m.name].add(record.device_time, m.unit, m.value)


def formatValue(value):
    return '' if value is None else f'{value:g}'


class Recorder:
    """Writes one TSV row per record received from the device.

    The file is flushed after each row so nothing is lost if the program crashes.
    If the unit of a recorded parameter changes, the current file is closed and
    recording continues in a new file (…_part2.tsv, …) with updated headers.
    """

    def __init__(self, path, data_names, units):
        self.base_path = Path(path)
        self.data_names = list(data_names)
        self.start_device_time = None
        self.start_pc_time = datetime.now()
        self.rows = 0
        self.files = []
        self._file = None
        self._openFile(dict(units))

    @property
    def path(self):
        return self.files[-1]

    def _openFile(self, units):
        part = len(self.files) + 1
        path = self.base_path if part == 1 else \
            self.base_path.with_name(f'{self.base_path.stem}_part{part}{self.base_path.suffix}')
        self.units = units
        self._file = open(path, 'w', newline='', encoding='utf-8')
        self._writer = csv.writer(self._file, delimiter='\t', lineterminator='\n')
        header = ['Time (s)', 'Device time', 'PC time']
        for name in self.data_names:
            unit = units.get(name)
            header.append(f'{name} ({unit})' if unit else name)
        self._writer.writerow(header)
        self._file.flush()
        self.files.append(path)

    def write(self, record):
        """Write a record. Returns a message if a new file had to be started."""
        message = None
        changed = [name for name in self.data_names
                   if name in record.measurements and self.units.get(name)
                   and record.measurements[name].unit != self.units[name]]
        if changed:
            units = dict(self.units)
            for name in changed:
                units[name] = record.measurements[name].unit
            self._file.close()
            self._openFile(units)
            message = f'Unit changed for {", ".join(changed)}. Continuing in {self.path.name}.'
        else:
            # fill in units for parameters that were unknown when recording started
            for name in self.data_names:
                if name in record.measurements and not self.units.get(name):
                    self.units[name] = record.measurements[name].unit

        if self.start_device_time is None:
            self.start_device_time = record.device_time
        elapsed = (record.device_time - self.start_device_time).total_seconds()
        row = [f'{elapsed:g}',
               record.device_time.isoformat(sep=' '),
               record.pc_time.isoformat(sep=' ', timespec='seconds')]
        for name in self.data_names:
            m = record.measurements.get(name)
            row.append(formatValue(m.value) if m else '')
        self._writer.writerow(row)
        self._file.flush()
        self.rows += 1
        return message

    def close(self):
        if self._file and not self._file.closed:
            self._file.close()

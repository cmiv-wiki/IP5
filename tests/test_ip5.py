import queue
import time
from datetime import datetime

import pytest

from ip5.codes import DATA_CODES, UNIT_CODES
from ip5.data import DataStore, Recorder
from ip5.demo import FakeSerial
from ip5.device import DeviceReader, parseRecord


def makeLine(time_='12:00:00', values=(('Heart rate', 'BPM', '72'), ('SPO2', '%', '?'))):
    fields = ['IP5', '123', '10/19/2026', time_]
    for name, unit, value in values:
        fields += [DATA_CODES[name], UNIT_CODES[unit], value]
    return ','.join(fields)


def test_parseRecord():
    record = parseRecord(makeLine())
    assert record.device_name == 'IP5'
    assert record.device_time == datetime(2026, 10, 19, 12, 0, 0)
    assert record.measurements['Heart rate'].value == 72
    assert record.measurements['Heart rate'].unit == 'BPM'
    assert record.measurements['SPO2'].value is None


def test_parseRecord_unknown_code_is_kept():
    record = parseRecord('IP5,,10/19/2026,12:00:00,0002-ffff,0004-ffff,1.5')
    assert record.measurements['Unknown 0002-ffff'].value == 1.5


@pytest.mark.parametrize('line', ['garbage', 'IP5,,13/45/2026,12:00:00',
                                  'IP5,,10/19/2026,12:00:00,0002-4182,0004-0aa0'])
def test_parseRecord_invalid(line):
    with pytest.raises(ValueError):
        parseRecord(line)


def test_recorder(tmp_path):
    store = DataStore()
    store.add(parseRecord(makeLine()))
    names = ['Heart rate', 'SPO2', 'NIBP – Mean']
    recorder = Recorder(tmp_path / 'rec.tsv', names, {n: store.series[n].unit for n in names})
    recorder.write(parseRecord(makeLine('12:00:00')))
    recorder.write(parseRecord(makeLine('12:00:02', values=(('Heart rate', 'BPM', '75'),
                                                             ('NIBP – Mean', 'mmHg', '90')))))
    # unit change -> new file
    message = recorder.write(parseRecord(makeLine('12:00:03', values=(('Heart rate', 'Breaths/min', '1'),))))
    recorder.close()
    assert message and recorder.files[-1].name == 'rec_part2.tsv'

    rows = [line.split('\t') for line in (tmp_path / 'rec.tsv').read_text(encoding='utf-8').splitlines()]
    assert rows[0] == ['Time (s)', 'Device time', 'PC time', 'Heart rate (BPM)', 'SPO2 (%)', 'NIBP – Mean (mmHg)']
    assert rows[1][0] == '0' and rows[1][3:] == ['72', '', '']
    assert rows[2][0] == '2' and rows[2][3:] == ['75', '', '90']
    part2 = (tmp_path / 'rec_part2.tsv').read_text(encoding='utf-8').splitlines()
    assert part2[0].split('\t')[3] == 'Heart rate (Breaths/min)'
    assert part2[1].split('\t')[0] == '3'


class ChunkedSerial(FakeSerial):
    """Delivers a fixed byte stream in small chunks."""

    def __init__(self, data):
        self._data = data
        self._started = False  # report nothing waiting until reading starts, so the port reset passes

    @property
    def in_waiting(self):
        return min(len(self._data), 7) if self._started else 0

    def read(self, size=1):
        self._started = True
        if not self._data:
            time.sleep(0.05)
        chunk, self._data = self._data[:size], self._data[size:]
        return chunk

    def reset_input_buffer(self):
        pass


def collect(reader, events, kind, count, timeout=5):
    found = []
    t0 = time.monotonic()
    while len(found) < count and time.monotonic() - t0 < timeout:
        try:
            k, payload = events.get(timeout=0.1)
        except queue.Empty:
            continue
        if k == kind:
            found.append(payload)
    reader.stop()
    reader.join(2)
    return found


def test_reader_chunked_stream():
    lines = ['partial,line'] + [makeLine(f'12:00:0{i}') for i in range(3)] + ['corrupt']
    data = ('\r\n'.join(lines) + '\r\n').encode('ascii')
    events = queue.Queue()
    reader = DeviceReader('test', events, serial_factory=lambda _: ChunkedSerial(data))
    reader.start()
    records = collect(reader, events, 'record', 3)
    assert [r.device_time.second for r in records] == [0, 1, 2]


def test_reader_demo():
    events = queue.Queue()
    reader = DeviceReader('demo', events, serial_factory=lambda _: FakeSerial(interval=0.1))
    reader.start()
    records = collect(reader, events, 'record', 3)
    assert len(records) == 3
    assert records[0].measurements['Heart rate'].unit == 'BPM'

"""Simulated IP5 serial port, used with `ip5 --demo` to try the program without a device."""
import math
import random
import time
from datetime import datetime

from .codes import DATA_CODES, UNIT_CODES

DEMO_PORT = 'Demo (simulated IP5)'


class FakeSerial:
    def __init__(self, port=None, interval=1.0):
        self.interval = interval
        self._buffer = b''
        self._t0 = time.monotonic()
        self._next = self._t0
        self._n = 0
        self._last_nibp = -60

    def _record(self):
        t = time.monotonic() - self._t0
        values = [
            ('Heart rate', 'BPM', 70 + 5 * math.sin(t / 20) + random.gauss(0, 1)),
            ('SPO2', '%', 97 + random.gauss(0, 0.5)),
            ('Respiration rate', 'Breaths/min', 14 + 2 * math.sin(t / 30)),
            ('Expired CO2', 'kPa', 5.2 + 0.3 * math.sin(t / 15) + random.gauss(0, 0.05)),
            ('Inspired CO2', 'kPa', 0.1),
            ('Inspired O2', '%', 21 + random.gauss(0, 0.2)),
            ('Temperature', '°C', 36.8 + 0.1 * math.sin(t / 60)),
            ('P1 – Systolic', 'mmHg', None),
        ]
        if t - self._last_nibp >= 60:
            self._last_nibp = t
            values += [('NIBP – Systolic', 'mmHg', 120 + random.gauss(0, 3)),
                       ('NIBP – Mean', 'mmHg', 93 + random.gauss(0, 2)),
                       ('NIBP – Diastolic', 'mmHg', 80 + random.gauss(0, 2))]
        now = datetime.now()
        fields = ['IP5-DEMO', '', now.strftime('%m/%d/%Y'), now.strftime('%H:%M:%S')]
        for name, unit, value in values:
            fields += [DATA_CODES[name], UNIT_CODES[unit], '?' if value is None else f'{value:.1f}']
        return (','.join(fields) + '\r\n').encode('ascii')

    def _produce(self):
        while time.monotonic() >= self._next:
            self._buffer += self._record()
            self._next += self.interval

    @property
    def in_waiting(self):
        self._produce()
        return len(self._buffer)

    def read(self, size=1):
        self._produce()
        if not self._buffer:
            time.sleep(0.1)
        data, self._buffer = self._buffer[:size], self._buffer[size:]
        return data

    def write(self, data):
        return len(data)

    def reset_input_buffer(self):
        self._buffer = b''

    def close(self):
        pass

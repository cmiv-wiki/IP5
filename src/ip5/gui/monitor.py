"""Monitor window, plots the selected parameters in real time."""
import math
import tkinter as tk
import tkinter.ttk as ttk

import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402

from ..codes import NON_PERIODIC_DATA  # noqa: E402

TIME_WINDOWS_MIN = (1, 5, 15, 30, 60, 120)
UPDATE_INTERVAL_MS = 1000


class MonitorWindow(tk.Toplevel):
    def __init__(self, parent, store, get_selected, window_min=5, on_window_change=None):
        super().__init__(parent)
        self.title('IP5 Monitor')
        self.geometry('900x700')
        self.store = store
        self.get_selected = get_selected
        self.on_window_change = on_window_change
        self._names = None
        self._axes = {}

        top = ttk.Frame(self, padding=(8, 6))
        top.pack(side=tk.TOP, fill=tk.X)
        ttk.Label(top, text='Time window (min)').pack(side=tk.LEFT)
        self.window_var = tk.StringVar(value=str(window_min))
        window_box = ttk.Combobox(top, textvariable=self.window_var, width=5, state='readonly',
                                  values=[str(w) for w in TIME_WINDOWS_MIN])
        window_box.pack(side=tk.LEFT, padx=5)
        window_box.bind('<<ComboboxSelected>>', self._windowChanged)
        self.info = ttk.Label(top, text='')
        self.info.pack(side=tk.RIGHT)

        self.figure = Figure(layout='constrained')
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self._job = None
        self.refresh()

    @property
    def window_min(self):
        return int(self.window_var.get())

    def _windowChanged(self, event=None):
        if self.on_window_change:
            self.on_window_change(self.window_min)
        self.refresh(reschedule=False)

    def _buildAxes(self, names):
        self.figure.clear()
        self._axes = {}
        self._names = names
        if not names:
            self.figure.text(0.5, 0.5, 'No data selected.\nSelect parameters in the main window.',
                             ha='center', va='center', fontsize=12, color='gray')
            return
        ncols = 1 if len(names) <= 4 else 2
        nrows = math.ceil(len(names) / ncols)
        axes = self.figure.subplots(nrows, ncols, sharex=True, squeeze=False).flatten()
        for ax in axes[len(names):]:
            ax.set_visible(False)
        for ax, name in zip(axes, names):
            style = 'o-' if name in NON_PERIODIC_DATA else '-'
            line, = ax.plot([], [], style, lw=1.5, ms=4)
            # current value, shown at the right of the title row
            value_text = ax.set_title('', loc='right', fontsize=13, fontweight='bold', color=line.get_color())
            ax.grid(True, alpha=0.3)
            self._axes[name] = (ax, line, value_text)
        for ax in axes[(nrows - 1) * ncols:]:
            ax.set_xlabel('Time (min)')

    def refresh(self, reschedule=True):
        names = list(self.get_selected())
        if names != self._names:
            self._buildAxes(names)

        latest = self.store.latest_record
        now = latest.device_time if latest else None
        window_s = self.window_min * 60
        for name, (ax, line, value_text) in self._axes.items():
            series = self.store.series[name]
            ax.set_title(f'{name} ({series.unit})' if series.unit else name, fontsize=10, loc='left')
            xs, ys = [], []
            if now is not None:
                for t, v in zip(reversed(series.times), reversed(series.values)):
                    dt = (t - now).total_seconds()
                    if dt < -window_s:
                        break
                    xs.append(dt / 60)
                    ys.append(v)
            line.set_data(xs, ys)
            value_text.set_text('no value' if series.value is None else f'{series.value:g}')
            ax.set_xlim(-self.window_min, 0)
            if ys:
                lo, hi = min(ys), max(ys)
                pad = (hi - lo) * 0.1 or max(abs(hi) * 0.05, 0.5)
                ax.set_ylim(lo - pad, hi + pad)
        if latest:
            self.info['text'] = f'{latest.device_name}   {latest.device_time:%Y-%m-%d %H:%M:%S}'
        self.canvas.draw_idle()

        if reschedule:
            self._job = self.after(UPDATE_INTERVAL_MS, self.refresh)

    def destroy(self):
        if self._job:
            self.after_cancel(self._job)
            self._job = None
        super().destroy()

"""Main window: serial port, data selection, recording control."""
import queue
import subprocess
import sys
import time
import tkinter as tk
import tkinter.ttk as ttk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox

from .. import __version__
from ..data import DataStore, Recorder, formatValue
from ..demo import DEMO_PORT, FakeSerial
from ..device import DeviceReader, listSerialPorts
from ..settings import loadSettings, saveSettings
from .monitor import MonitorWindow

POLL_INTERVAL_MS = 100
CHECKED, UNCHECKED = '☑', '☐'

STATUS_COLORS = {
    'disconnected': '#9e9e9e',
    'waiting': '#f2b600',
    'connected': '#2e9d3a',
    'error': '#d32f2f',
}


class MainWindow:
    def __init__(self, root, demo=False):
        self.root = root
        self.demo = demo
        self.settings = loadSettings()
        self.store = DataStore()
        self.events = queue.Queue()
        self.reader = None
        self.recorder = None
        self.monitor = None
        self.selected = [name for name in self.settings['selected_data'] if name in self.store.series]
        self.parse_errors = 0

        root.title(f'IP5 Recorder {__version__}')
        root.minsize(620, 560)
        root.protocol('WM_DELETE_WINDOW', self.onClose)

        main = ttk.Frame(root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)
        self._buildConnection(main)
        self._buildDataTable(main)
        self._buildRecording(main)

        self.refreshPorts()
        self.setStatus('disconnected', 'Not connected')
        self.updateTable()
        self.root.after(POLL_INTERVAL_MS, self.poll)

    # layout
    ############################################################################################################
    def _buildConnection(self, parent):
        frame = ttk.LabelFrame(parent, text='Connection', padding=8)
        frame.pack(fill=tk.X)
        ttk.Label(frame, text='Serial port').grid(row=0, column=0, sticky='w')
        self.port_var = tk.StringVar()
        self.port_box = ttk.Combobox(frame, textvariable=self.port_var, width=32, state='readonly')
        self.port_box.grid(row=0, column=1, padx=5, sticky='we')
        self.refresh_button = ttk.Button(frame, text='Refresh', command=self.refreshPorts)
        self.refresh_button.grid(row=0, column=2, padx=2)
        self.connect_button = ttk.Button(frame, text='Connect', command=self.toggleConnection, width=12)
        self.connect_button.grid(row=0, column=3, padx=2)

        self.status_dot = tk.Canvas(frame, width=14, height=14, highlightthickness=0)
        self.status_dot.grid(row=1, column=0, sticky='w', pady=(8, 0))
        self._dot = self.status_dot.create_oval(2, 2, 13, 13, fill='gray', outline='')
        self.status_label = ttk.Label(frame, text='')
        self.status_label.grid(row=1, column=0, columnspan=4, sticky='w', padx=(20, 0), pady=(8, 0))
        frame.columnconfigure(1, weight=1)

    def _buildDataTable(self, parent):
        frame = ttk.LabelFrame(parent, text='Data (checked parameters are monitored and recorded)', padding=8)
        frame.pack(fill=tk.BOTH, expand=True, pady=8)
        columns = ('record', 'name', 'value', 'unit', 'status')
        self.table = ttk.Treeview(frame, columns=columns, show='headings', selectmode='none', height=14)
        for col, text, width, anchor in (('record', 'Record', 60, 'center'),
                                         ('name', 'Parameter', 200, 'w'),
                                         ('value', 'Value', 90, 'e'),
                                         ('unit', 'Unit', 90, 'w'),
                                         ('status', 'Status', 110, 'w')):
            self.table.heading(col, text=text)
            self.table.column(col, width=width, anchor=anchor, stretch=(col == 'name'))
        self.table.tag_configure('unavailable', foreground='#9e9e9e')
        scroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.table.yview)
        self.table.configure(yscrollcommand=scroll.set)
        self.table.grid(row=0, column=0, columnspan=4, sticky='nsew')
        scroll.grid(row=0, column=4, sticky='ns')
        self.table.bind('<Button-1>', self.onTableClick)
        self.table.bind('<space>', self.onTableSpace)

        self.select_all_button = ttk.Button(frame, text='Select all available', command=self.selectAllAvailable)
        self.select_all_button.grid(row=1, column=0, sticky='w', pady=(6, 0))
        self.clear_button = ttk.Button(frame, text='Clear selection', command=self.clearSelection)
        self.clear_button.grid(row=1, column=1, sticky='w', pady=(6, 0), padx=5)
        self.show_all_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text='Show unavailable', variable=self.show_all_var,
                        command=self.updateTable).grid(row=1, column=2, sticky='w', pady=(6, 0))
        ttk.Button(frame, text='Open monitor', command=self.openMonitor).grid(row=1, column=3, sticky='e', pady=(6, 0))
        frame.columnconfigure(2, weight=1)
        frame.rowconfigure(0, weight=1)

    def _buildRecording(self, parent):
        frame = ttk.LabelFrame(parent, text='Recording', padding=8)
        frame.pack(fill=tk.X)
        ttk.Label(frame, text='Folder').grid(row=0, column=0, sticky='w')
        self.folder_var = tk.StringVar(value=self.settings['output_folder'])
        self.folder_entry = ttk.Entry(frame, textvariable=self.folder_var)
        self.folder_entry.grid(row=0, column=1, columnspan=2, sticky='we', padx=5)
        self.browse_button = ttk.Button(frame, text='Browse…', command=self.browseFolder)
        self.browse_button.grid(row=0, column=3)

        ttk.Label(frame, text='File prefix').grid(row=1, column=0, sticky='w', pady=(6, 0))
        self.prefix_var = tk.StringVar(value=self.settings['file_prefix'])
        self.prefix_entry = ttk.Entry(frame, textvariable=self.prefix_var, width=20)
        self.prefix_entry.grid(row=1, column=1, sticky='w', padx=5, pady=(6, 0))
        ttk.Label(frame, text='→ <prefix>_YYYYMMDD_HHMMSS.tsv', foreground='#777').grid(
            row=1, column=2, sticky='w', pady=(6, 0))

        self.record_button = tk.Button(frame, text='● Start recording', command=self.toggleRecording,
                                       width=18, font=('TkDefaultFont', 13, 'bold'))
        self._record_fg = self.record_button.cget('fg')
        self.record_button.grid(row=2, column=0, columnspan=2, sticky='w', pady=(10, 0))
        self.record_info = ttk.Label(frame, text='Not recording')
        self.record_info.grid(row=2, column=2, columnspan=2, sticky='w', pady=(10, 0))
        self.open_folder_button = ttk.Button(frame, text='Show in folder', command=self.showInFolder)
        self.open_folder_button.grid(row=3, column=3, sticky='e', pady=(6, 0))
        self.file_label = ttk.Label(frame, text='', foreground='#555')
        self.file_label.grid(row=3, column=0, columnspan=3, sticky='w', pady=(6, 0))
        frame.columnconfigure(2, weight=1)

    # connection
    ############################################################################################################
    def refreshPorts(self):
        ports = listSerialPorts()
        if self.demo:
            ports.insert(0, DEMO_PORT)
        self.port_box['values'] = ports
        current = self.port_var.get()
        if current not in ports:
            preferred = self.settings['port']
            self.port_var.set(preferred if preferred in ports else (ports[0] if ports else ''))

    def toggleConnection(self):
        if self.reader:
            self.disconnect()
        else:
            self.connect()

    def connect(self):
        port = self.port_var.get()
        if not port:
            messagebox.showwarning('Connection', 'Select a serial port first.', parent=self.root)
            return
        self.settings['port'] = port
        self.parse_errors = 0
        factory = (lambda _: FakeSerial()) if port == DEMO_PORT else None
        # new queue per connection so events from a previous reader are never mixed in
        self.events = queue.Queue()
        self.reader = DeviceReader(port, self.events, serial_factory=factory)
        self.reader.start()
        self.setStatus('waiting', f'Opening {port}…')
        self._updateControls()

    def disconnect(self):
        if self.recorder and not messagebox.askyesno(
                'Disconnect', 'A recording is running. Stop recording and disconnect?', parent=self.root):
            return
        self.stopRecording()
        if self.reader:
            self.reader.stop()
            self.reader = None
        self.setStatus('disconnected', 'Not connected')
        self._updateControls()

    def setStatus(self, state, text):
        self.status_state = state
        self.status_dot.itemconfigure(self._dot, fill=STATUS_COLORS[state])
        self.status_label['text'] = text

    # event handling
    ############################################################################################################
    def poll(self):
        updated = False
        try:
            while True:
                kind, payload = self.events.get_nowait()
                updated |= self.handleEvent(kind, payload)
        except queue.Empty:
            pass
        if updated:
            self.updateTable()
        self._updateRecordingInfo()
        self.root.after(POLL_INTERVAL_MS, self.poll)

    def handleEvent(self, kind, payload):
        if self.reader is None:
            return False
        if kind == 'status':
            self.setStatus('waiting', payload)
        elif kind == 'connected':
            self.setStatus('connected', 'Receiving data')
        elif kind == 'silent':
            self.setStatus('waiting', 'Device not sending data (check cable and IP5 data export)')
        elif kind == 'record':
            self.store.add(payload)
            text = f'Receiving data from {payload.device_name or "IP5"}'
            if self.parse_errors:
                text += f'  ({self.parse_errors} corrupt records ignored)'
            self.setStatus('connected', text)
            if self.recorder:
                self._writeRecord(payload)
            return True
        elif kind == 'parse_error':
            self.parse_errors += 1
        elif kind == 'error':
            self.reader = None
            self.setStatus('error', payload)
            self._updateControls()
            if self.recorder:
                self.stopRecording()
                messagebox.showerror('Connection lost',
                                     f'Recording stopped, the serial port failed:\n{payload}', parent=self.root)
        return False

    # data table
    ############################################################################################################
    def updateTable(self):
        show_all = self.show_all_var.get()
        wanted = [s for s in self.store.series.values()
                  if show_all or s.available or s.name in self.selected]
        wanted_ids = {s.name for s in wanted}
        for iid in self.table.get_children():
            if iid not in wanted_ids:
                self.table.delete(iid)
        for index, s in enumerate(wanted):
            status = 'Available' if s.available else ('Not received' if self.reader else '')
            values = (CHECKED if s.name in self.selected else UNCHECKED, s.name,
                      formatValue(s.value), s.unit, status)
            tags = () if s.available else ('unavailable',)
            if self.table.exists(s.name):
                self.table.item(s.name, values=values, tags=tags)
                self.table.move(s.name, '', index)
            else:
                self.table.insert('', index, iid=s.name, values=values, tags=tags)

    def onTableClick(self, event):
        if self.table.identify_region(event.x, event.y) not in ('cell', 'tree'):
            return
        row = self.table.identify_row(event.y)
        if row:
            self.table.focus(row)
            self.toggleSelected(row)

    def onTableSpace(self, event):
        row = self.table.focus()
        if row:
            self.toggleSelected(row)

    def toggleSelected(self, name):
        if self.recorder:
            messagebox.showinfo('Data selection', 'Stop the recording to change which data is recorded.',
                                parent=self.root)
            return
        if name in self.selected:
            self.selected.remove(name)
        else:
            # keep selection in the order of the table
            order = list(self.store.series)
            self.selected = sorted(self.selected + [name], key=order.index)
        self.updateTable()

    def selectAllAvailable(self):
        self.selected = [s.name for s in self.store.series.values() if s.available]
        self.updateTable()

    def clearSelection(self):
        self.selected = []
        self.updateTable()

    # monitor
    ############################################################################################################
    def openMonitor(self):
        if self.monitor and self.monitor.winfo_exists():
            self.monitor.lift()
            return
        self.monitor = MonitorWindow(self.root, self.store, lambda: self.selected,
                                     window_min=self.settings['monitor_window_min'],
                                     on_window_change=self._monitorWindowChanged)

    def _monitorWindowChanged(self, minutes):
        self.settings['monitor_window_min'] = minutes

    # recording
    ############################################################################################################
    def browseFolder(self):
        folder = filedialog.askdirectory(initialdir=self.folder_var.get() or str(Path.home()), parent=self.root)
        if folder:
            self.folder_var.set(folder)

    def toggleRecording(self):
        if self.recorder:
            self.stopRecording()
        else:
            self.startRecording()

    def startRecording(self):
        if self.status_state != 'connected':
            messagebox.showwarning('Recording', 'No data is being received from the IP5.', parent=self.root)
            return
        if not self.selected:
            messagebox.showwarning('Recording', 'Select at least one parameter to record.', parent=self.root)
            return
        unavailable = [n for n in self.selected if not self.store.series[n].available]
        if unavailable and not messagebox.askyesno(
                'Recording', 'The following parameters have not been received from the device:\n\n'
                + '\n'.join(unavailable) + '\n\nStart recording anyway?', parent=self.root):
            return
        prefix = self.prefix_var.get().strip() or 'IP5'
        folder = Path(self.folder_var.get()).expanduser()
        path = folder / f'{prefix}_{datetime.now():%Y%m%d_%H%M%S}.tsv'
        try:
            folder.mkdir(parents=True, exist_ok=True)
            units = {n: self.store.series[n].unit for n in self.selected}
            self.recorder = Recorder(path, self.selected, units)
        except OSError as e:
            messagebox.showerror('Recording', f'Could not create file:\n{e}', parent=self.root)
            return
        self.recording_t0 = time.monotonic()
        self.settings['output_folder'] = str(folder)
        self.settings['file_prefix'] = prefix
        self._updateControls()

    def _writeRecord(self, record):
        try:
            message = self.recorder.write(record)
        except OSError as e:
            self.stopRecording()
            messagebox.showerror('Recording', f'Recording stopped, could not write to file:\n{e}',
                                 parent=self.root)
            return
        if message:
            messagebox.showwarning('Recording', message, parent=self.root)

    def stopRecording(self):
        if not self.recorder:
            return
        self.recorder.close()
        files = ', '.join(p.name for p in self.recorder.files)
        self.last_files = self.recorder.files
        self.file_label['text'] = f'Saved: {files}  ({self.recorder.rows} rows)'
        self.recorder = None
        self._updateControls()

    def _updateRecordingInfo(self):
        if self.recorder:
            elapsed = int(time.monotonic() - self.recording_t0)
            h, rem = divmod(elapsed, 3600)
            m, s = divmod(rem, 60)
            self.record_info['text'] = f'Recording  {h:02d}:{m:02d}:{s:02d}   {self.recorder.rows} rows'
            self.file_label['text'] = str(self.recorder.path)
        elif self.record_info['text'] != 'Not recording':
            self.record_info['text'] = 'Not recording'

    def showInFolder(self):
        files = getattr(self, 'last_files', None)
        target = (self.recorder.path if self.recorder else files[-1] if files
                  else Path(self.folder_var.get()).expanduser())
        target = Path(target)
        try:
            if sys.platform == 'darwin':
                subprocess.run(['open', '-R', str(target)] if target.is_file() else ['open', str(target)])
            elif sys.platform == 'win32':
                subprocess.run(['explorer', '/select,', str(target)] if target.is_file() else ['explorer', str(target)])
            else:
                subprocess.run(['xdg-open', str(target.parent if target.is_file() else target)])
        except OSError as e:
            messagebox.showerror('Show in folder', str(e), parent=self.root)

    def _updateControls(self):
        connected = self.reader is not None
        recording = self.recorder is not None
        self.connect_button['text'] = 'Disconnect' if connected else 'Connect'
        self.connect_button.state(['!disabled'])
        port_state = ['disabled'] if connected else ['!disabled']
        self.port_box.state(port_state + (['readonly'] if not connected else []))
        self.refresh_button.state(port_state)
        lock = ['disabled'] if recording else ['!disabled']
        for widget in (self.select_all_button, self.clear_button, self.folder_entry,
                       self.browse_button, self.prefix_entry):
            widget.state(lock)
        if recording:
            self.record_button.configure(text='■ Stop recording', fg='#d32f2f')
        else:
            self.record_button.configure(text='● Start recording', fg=self._record_fg)
        self.updateTable()

    # closing
    ############################################################################################################
    def onClose(self):
        if self.recorder and not messagebox.askyesno(
                'Quit', 'A recording is running. Stop recording and quit?', parent=self.root):
            return
        self.stopRecording()
        if self.reader:
            self.reader.stop()
        self.settings['selected_data'] = self.selected
        self.settings['output_folder'] = self.folder_var.get()
        self.settings['file_prefix'] = self.prefix_var.get()
        saveSettings(self.settings)
        self.root.destroy()

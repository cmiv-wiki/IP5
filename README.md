# IP5 Recorder

Program for reading and recording data from a Philips IntelliVue Expression IP5 (MR400) over its serial port.

- Select a serial port and connect
- Choose which parameters to monitor and record (click in the table)
- Monitor window with real-time plots (time window 1–120 min)
- Start/stop recording, data is saved as TSV

## Recording files

Files are saved in the selected folder as `<prefix>_YYYYMMDD_HHMMSS.tsv`. One row is written per record from the IP5
(about 1 Hz), and the file is flushed to disk after every row, so nothing is lost if the program crashes.

| Column | Contents |
|---|---|
| `Time (s)` | Seconds since the first row of the recording (according to the IP5's clock) |
| `Device time` | Timestamp from the IP5 |
| `PC time` | When the computer received the record |
| `<Parameter> (<unit>)` | Value, empty if missing (`?` from the device or not sent, e.g. NIBP between measurements) |

If a recorded parameter changes unit during a recording, the recording continues in a new file (`…_part2.tsv`) with new headers.

## Installation

Requires [Git](https://git-scm.com/downloads) and [Miniconda](https://docs.conda.io/en/latest/miniconda.html) (or Anaconda).

```bash
git clone https://github.com/cmiv-wiki/IP5.git
cd IP5
conda env create -f environment.yml
conda activate ip5
pip install -e .
ip5               # or: ip5 --demo to try it without an IP5
```

### Windows

- Run the commands above in **Anaconda Prompt** (from the Start menu).
- A USB-to-serial adapter usually needs a driver (e.g. FTDI or Prolific). The port then shows up as `COM3` or similar
  in Device Manager and in the program's port list.

### Linux

- The serial port is `/dev/ttyUSB0` (USB-to-serial adapter) or `/dev/ttyS0`.
- Your user needs permission to access the serial port. Add yourself to the `dialout` group (Debian/Ubuntu)
  or `uucp` (Arch), then log out and back in:
  ```bash
  sudo usermod -aG dialout $USER
  ```
- "Show in folder" uses `xdg-open`, which is available on most desktop environments.

## Development

```bash
conda env create -f environment.yml
conda activate ip5
pip install -e .
ip5 --demo        # --demo adds a simulated IP5 to the port list
pytest tests
```

## Building the app

```bash
conda activate ip5
./build_app.sh
```

- macOS: `dist/IP5 Recorder.app`
- Windows: run `pyinstaller --noconfirm --clean ip5.spec` in Anaconda Prompt → `dist\IP5 Recorder\IP5 Recorder.exe`
- Linux: `./build_app.sh` → `dist/IP5 Recorder/IP5 Recorder`

On Windows and Linux the app is a folder; copy the whole `IP5 Recorder` folder, not just the executable.

PyInstaller does not cross-compile; the app must be built on the operating system it will run on.
The app is not signed:
- macOS: the first time, right-click → Open.
- Windows: if SmartScreen warns, click "More info" → "Run anyway".

Settings (last port, folder, selected parameters) are saved in `~/.ip5/settings.json`
(Windows: `C:\Users\<name>\.ip5\settings.json`). Recordings are saved to `~/Documents/IP5 recordings` by default.

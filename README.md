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

Pick one of the options below. All of them install the `ip5` command; run `ip5 --demo` to try it without an IP5.

### Option 1: conda

Requires [Git](https://git-scm.com/downloads) and [Miniconda](https://docs.conda.io/en/latest/miniconda.html)
(or Anaconda). On Windows, run the commands in **Anaconda Prompt** (from the Start menu).

```bash
git clone https://github.com/cmiv-wiki/IP5.git
cd IP5
conda env create -f environment.yml
conda activate ip5
pip install -e .
ip5
```

### Option 2: pip

Requires Python 3.10 or later with tkinter:
- Windows: install from [python.org](https://www.python.org/downloads/windows/) or with
  `winget install -e --id Python.Python.3.13` (tkinter is included).
- macOS: the python.org installer includes tkinter; with Homebrew Python, also run `brew install python-tk`.
- Linux: tkinter is often a separate package, e.g. `sudo apt install python3-tk python3-venv` on Debian/Ubuntu.

macOS/Linux:

```bash
git clone https://github.com/cmiv-wiki/IP5.git
cd IP5
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
ip5
```

Windows (PowerShell):

```powershell
git clone https://github.com/cmiv-wiki/IP5.git
cd IP5
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\ip5.exe
```

Calling the executables in `.venv\Scripts` directly avoids having to activate the environment, which PowerShell's
execution policy often blocks.

Without Git, install straight from GitHub (not editable; rerun with `--upgrade --force-reinstall` to update):

```powershell
py -m venv $HOME\ip5-env
& $HOME\ip5-env\Scripts\python.exe -m pip install https://github.com/cmiv-wiki/IP5/archive/refs/heads/main.zip
& $HOME\ip5-env\Scripts\ip5.exe
```

### Option 3: uv

Requires [uv](https://docs.astral.sh/uv/getting-started/installation/). uv downloads a suitable Python itself.

```bash
git clone https://github.com/cmiv-wiki/IP5.git
cd IP5
uv sync
uv run ip5
```

Or install `ip5` as a global command (into `~/.local/bin`, on Windows `C:\Users\<name>\.local\bin`):

```bash
uv tool install git+https://github.com/cmiv-wiki/IP5.git
uv tool update-shell    # adds ~/.local/bin to PATH; restart the terminal afterwards
ip5
```

### Where does `ip5` end up?

`ip5` (`ip5.exe` on Windows) is a small launcher in the environment's `bin/` (`Scripts\` on Windows) folder, e.g.
`.venv/bin/ip5` or `.venv\Scripts\ip5.exe`. If the command is not found, `python -m ip5` always works inside the
environment. With an editable install (`-e`, `uv sync`), the launcher points to the cloned folder, so code changes
take effect immediately, but the folder must not be moved or deleted.

### Windows notes

- A USB-to-serial adapter usually needs a driver (e.g. FTDI or Prolific). The port then shows up as `COM3` or similar
  in Device Manager and in the program's port list.

### Linux notes

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

With uv: `uv run --with pytest pytest tests`. With pip: `pip install pytest` in the venv first.

## Building the app

```bash
conda activate ip5
./build_app.sh
```

- macOS: `dist/IP5 Recorder.app`
- Windows: run `pyinstaller --noconfirm --clean ip5.spec` in Anaconda Prompt → `dist\IP5 Recorder\IP5 Recorder.exe`
- Linux: `./build_app.sh` → `dist/IP5 Recorder/IP5 Recorder`

Without conda: `pip install pyinstaller` in the venv and run the same commands, or with uv:
`uv run --with pyinstaller pyinstaller --noconfirm --clean ip5.spec`.

On Windows and Linux the app is a folder; copy the whole `IP5 Recorder` folder, not just the executable.

PyInstaller does not cross-compile; the app must be built on the operating system it will run on.
The app is not signed:
- macOS: the first time, right-click → Open.
- Windows: if SmartScreen warns, click "More info" → "Run anyway".

Settings (last port, folder, selected parameters) are saved in `~/.ip5/settings.json`
(Windows: `C:\Users\<name>\.ip5\settings.json`). Recordings are saved to `~/Documents/IP5 recordings` by default.

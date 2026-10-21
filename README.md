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

There are two ways to run the program:

1. **[Run the `ip5` command](#option-1-run-the-ip5-command)**: install the Python package and start the program from
   a terminal with `ip5`. Easiest to keep up to date; requires Python (uv can install it for you).
2. **[Build a standalone app](#option-2-build-a-standalone-app)**: build `IP5 Recorder.app` (macOS) or
   `IP5 Recorder.exe` (Windows) once, then start it like any other program. The finished app does not need Python, so
   it can be copied to a computer without it (with the same operating system).

Both run the same program; settings and recordings are shared (see [Settings and recordings](#settings-and-recordings)).
Use `ip5 --demo` (or `uv run ip5 --demo` in a clone) to try it without an IP5; it adds a simulated IP5 to the port list.

### Option 1: Run the `ip5` command

#### With uv (recommended)

Install [uv](https://docs.astral.sh/uv/getting-started/installation/):

- macOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh` (or `brew install uv`)
- Windows (PowerShell): `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
  (or `winget install -e --id astral-sh.uv`)

uv downloads the right Python version (with tkinter) by itself.

Install `ip5` as a global command (requires [Git](https://git-scm.com/downloads)):

```bash
uv tool install git+https://github.com/cmiv-wiki/IP5.git
uv tool update-shell    # adds ~/.local/bin to PATH; restart the terminal afterwards
ip5
```

Update later with `uv tool upgrade ip5`.

To work on the code, see [Development](#development).

#### With pip

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

#### Where does `ip5` end up?

`ip5` (`ip5.exe` on Windows) is a small launcher in the environment's `bin/` (`Scripts\` on Windows) folder, e.g.
`.venv/bin/ip5` or `.venv\Scripts\ip5.exe`; `uv tool install` puts it in `~/.local/bin`
(`C:\Users\<name>\.local\bin` on Windows). If the command is not found, `python -m ip5` always works inside the
environment. With an editable install (`pip install -e`, `uv sync`), the launcher points to the cloned folder, so code
changes take effect immediately, but the folder must not be moved or deleted.

### Option 2: Build a standalone app

The app is built with [PyInstaller](https://pyinstaller.org/) from a clone of the repository. Install
[uv](#with-uv-recommended) first (or use a pip environment with `pip install -e . pyinstaller`).

macOS/Linux:

```bash
git clone https://github.com/cmiv-wiki/IP5.git
cd IP5
./build_app.sh
```

Windows (PowerShell):

```powershell
git clone https://github.com/cmiv-wiki/IP5.git
cd IP5
uv run pyinstaller --noconfirm --clean ip5.spec    # or ./build_app.sh in Git Bash
```

`build_app.sh` uses `uv run pyinstaller` if uv is installed, otherwise `pyinstaller` from the active environment.
The result ends up in `dist/`:

- macOS: `dist/IP5 Recorder.app` (drag it to Applications if you like)
- Linux: `dist/IP5 Recorder/IP5 Recorder`
- Windows: `dist\IP5 Recorder\IP5 Recorder.exe`

On Windows and Linux the app is a folder; copy the whole `IP5 Recorder` folder, not just the executable.

PyInstaller does not cross-compile; the app must be built on the operating system it will run on.
To update the app, `git pull` and build again.

The app is not signed:
- macOS: the first time, right-click → Open.
- Windows: if SmartScreen warns, click "More info" → "Run anyway".

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

## Settings and recordings

Settings (last port, folder, selected parameters) are saved in `~/.ip5/settings.json`
(Windows: `C:\Users\<name>\.ip5\settings.json`). Recordings are saved to `~/Documents/IP5 recordings` by default.

## Development

The project uses [uv](https://docs.astral.sh/uv/). The Python version is pinned in `.python-version` and exact
package versions in `uv.lock`; commit `uv.lock` when dependencies change.

```bash
git clone https://github.com/cmiv-wiki/IP5.git
cd IP5
uv sync             # creates .venv with Python, the package (editable) and dev tools (pytest, pyinstaller)
uv run ip5 --demo
uv run pytest tests
```

- Add a dependency: `uv add <package>` (or `uv add --dev <package>` for dev tools).
- Update locked versions: `uv lock --upgrade`.
- With pip instead: `pip install -e . pytest pyinstaller` in a venv (see [With pip](#with-pip)).

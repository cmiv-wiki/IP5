"""Entry point for the IP5 Recorder."""
import argparse
import tkinter as tk

from . import __version__
from .gui.main_window import MainWindow


def main(argv=None):
    parser = argparse.ArgumentParser(description='Record data from a Philips Expression IP5.')
    parser.add_argument('--demo', action='store_true', help='add a simulated IP5 to the port list')
    parser.add_argument('--version', action='version', version=__version__)
    # macOS adds -psn_* arguments when an app is started from Finder
    args, _ = parser.parse_known_args(argv)

    root = tk.Tk()
    MainWindow(root, demo=args.demo)
    root.mainloop()


if __name__ == '__main__':
    main()

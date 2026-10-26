#!/usr/bin/env python3
"""Entry point: run with `python AppleSoft.py [program.abas]`."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from applesoft.gui_app import main

if __name__ == "__main__":
    main()

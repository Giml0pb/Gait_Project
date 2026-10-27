"""Convenience entry point for the dataset-free technical demonstration."""

import sys

from gait_project.cli import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:] or ["demo"]))

"""Kanon: context engine for AI-assisted projects."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("kanon-engine")
except PackageNotFoundError:  # running from a source tree without installation
    __version__ = "0+unknown"

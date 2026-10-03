"""Exact-path link metadata for Python rejection tests using regular files."""

from contextlib import contextmanager
import os
import pathlib
from unittest import mock


@contextmanager
def symlink_metadata(path):
    """Expose one existing placeholder as a link; retain other filesystem behavior."""
    selected = os.path.realpath(path)
    original_is_symlink = pathlib.Path.is_symlink
    original_scandir = os.scandir

    def matches(candidate):
        return os.path.realpath(candidate) == selected

    def is_symlink(candidate):
        return matches(candidate) or original_is_symlink(candidate)

    class LinkEntry:
        def __init__(self, entry):
            self.entry = entry

        def __getattr__(self, name):
            return getattr(self.entry, name)

        def is_symlink(self):
            return True

        def is_file(self, *, follow_symlinks=True):
            return follow_symlinks and self.entry.is_file()

        def is_dir(self, *, follow_symlinks=True):
            return follow_symlinks and self.entry.is_dir()

    class Scandir:
        def __init__(self, directory):
            self.entries = original_scandir(directory)

        def __iter__(self):
            return self

        def __next__(self):
            entry = next(self.entries)
            return LinkEntry(entry) if matches(entry.path) else entry

        def __enter__(self):
            return self

        def __exit__(self, *exception):
            self.close()

        def close(self):
            self.entries.close()

    with mock.patch.object(pathlib.Path, "is_symlink", is_symlink), \
         mock.patch.object(os, "scandir", Scandir):
        yield

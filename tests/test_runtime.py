"""Tests for runtime environment guards."""

import pytest

from pipeline.runtime import ensure_supported_python


class TestEnsureSupportedPython:
    def test_accepts_supported_version(self):
        ensure_supported_python((3, 11, 0))

    def test_rejects_older_version(self):
        with pytest.raises(RuntimeError):
            ensure_supported_python((3, 10, 12))

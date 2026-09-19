"""Shared test configuration.

The API requires a session for every endpoint. These tests exercise pipeline
and API behaviour rather than access control, so they run with authentication
disabled rather than threading a login through every request - which would
test the login helper repeatedly and the thing under test not at all.

Set here (before the app is imported anywhere) rather than in individual test
modules, so a new test file cannot accidentally run without it and appear to
fail for reasons unrelated to what it checks. Authentication itself is covered
by backend/tests/test_auth.py, which turns this off deliberately.
"""
from __future__ import annotations

import os

os.environ.setdefault("BORDERWATCH_DISABLE_AUTH", "1")
# Demo cameras open video files and start capture threads; a test run should
# not be doing that in the background.
os.environ.setdefault("BORDERWATCH_NO_DEMO_CAMERAS", "1")

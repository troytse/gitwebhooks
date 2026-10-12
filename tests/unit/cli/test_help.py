"""Unit tests for CLI help and version behavior

Verifies that ``-h``/``--help`` and ``-v``/``--version`` follow standard Unix
conventions (handled by argparse, printed to stdout, exit code 0) at every
command level, and that the ``help`` subcommand shows the same text.

These tests are written with ``unittest`` on purpose: the project's test
runner (``python3 -m tests``) does not require pytest.
"""

import io
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

# Make the package importable when this file is run directly
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from gitwebhooks.main import main


class TestHelpFlag(unittest.TestCase):
    """-h/--help must be accepted at every level and exit with code 0."""

    def _run_expecting_exit(self, argv):
        """Run main(argv), expect SystemExit, return (code, stdout, stderr)."""
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            with self.assertRaises(SystemExit) as ctx:
                main(argv)
        return ctx.exception.code, out.getvalue(), err.getvalue()

    def test_main_help_short_flag(self):
        """-h prints usage and exits 0."""
        code, out, _ = self._run_expecting_exit(['-h'])
        self.assertEqual(code, 0)
        self.assertIn('usage', out.lower())

    def test_main_help_long_flag(self):
        """--help prints usage and exits 0."""
        code, out, _ = self._run_expecting_exit(['--help'])
        self.assertEqual(code, 0)
        self.assertIn('usage', out.lower())
        self.assertIn('serve', out)

    def test_help_writes_to_stdout(self):
        """Help output goes to stdout, not stderr."""
        _, out, err = self._run_expecting_exit(['--help'])
        self.assertTrue(out.strip())
        self.assertEqual(err, '')

    def test_help_no_longer_rejected(self):
        """Regression: the old '-h/--help are not supported' error is gone."""
        _, out, err = self._run_expecting_exit(['--help'])
        self.assertNotIn('not supported', (out + err).lower())

    def test_subcommand_help(self):
        """Each top-level subcommand accepts --help."""
        for cmd in ('serve', 'config'):
            with self.subTest(cmd=cmd):
                code, out, _ = self._run_expecting_exit([cmd, '--help'])
                self.assertEqual(code, 0)
                self.assertIn(cmd, out)

    def test_nested_action_help(self):
        """Nested actions accept --help and list their own options."""
        code, out, _ = self._run_expecting_exit(['serve', 'install', '--help'])
        self.assertEqual(code, 0)
        self.assertIn('--force', out)

    def test_version_flags(self):
        """-v and --version print the version and exit 0."""
        for flag in ('-v', '--version'):
            with self.subTest(flag=flag):
                code, out, _ = self._run_expecting_exit([flag])
                self.assertEqual(code, 0)
                self.assertIn('gitwebhooks-cli', out)


class TestHelpSubcommand(unittest.TestCase):
    """The `help` subcommand stays available and mirrors <cmd> --help."""

    def _capture_return(self, argv):
        """Run main(argv) expecting an integer return, return (rc, stdout)."""
        out = io.StringIO()
        with redirect_stdout(out):
            rc = main(argv)
        return rc, out.getvalue()

    def test_help_subcommand_no_topic(self):
        """`help` without a topic prints main help and succeeds."""
        rc, out = self._capture_return(['help'])
        self.assertEqual(rc, 0)
        self.assertIn('usage', out.lower())

    def test_help_subcommand_matches_flag_output(self):
        """`help <cmd>` and `<cmd> --help` produce identical text."""
        for cmd in ('serve', 'config'):
            with self.subTest(cmd=cmd):
                _, via_subcommand = self._capture_return(['help', cmd])

                out = io.StringIO()
                with redirect_stdout(out):
                    with self.assertRaises(SystemExit):
                        main([cmd, '--help'])

                self.assertEqual(via_subcommand, out.getvalue())

    def test_unknown_topic_exits_nonzero(self):
        """`help <unknown>` reports an error and returns 1."""
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = main(['help', 'bogus'])

        self.assertEqual(rc, 1)
        self.assertIn('Unknown command', err.getvalue())


if __name__ == '__main__':
    unittest.main()

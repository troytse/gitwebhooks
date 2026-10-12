"""Unit tests for the deployment command executor

Covers the pipe-buffer regression: a deployment command whose output exceeds
the OS pipe buffer MUST NOT block, and the child process MUST be reaped.

These tests are written with ``unittest`` on purpose: the project's test
runner (``python3 -m tests``) does not require pytest.
"""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# Make the package importable when this file is run directly
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from gitwebhooks.utils.executor import execute_deployment

# Comfortably larger than any OS pipe buffer (Linux 64 KiB, macOS 16-64 KiB).
FLOOD_BYTES = 400000

CHILD_SCRIPT = '''\
import sys

mode = sys.argv[1]
if mode == 'flood':
    sys.stdout.write('x' * %d)
    sys.stdout.flush()
    open(sys.argv[2], 'w').write('done')
elif mode == 'flood_stderr':
    sys.stderr.write('y' * %d)
    sys.stderr.flush()
    open(sys.argv[2], 'w').write('done')
elif mode == 'fail':
    print('BOOM-LINE-1')
    print('BOOM-LINE-2')
    sys.exit(3)
elif mode == 'ok':
    print('OK-LINE')
''' % (FLOOD_BYTES, FLOOD_BYTES)


class TestExecuteDeployment(unittest.TestCase):
    """Behavior of execute_deployment()"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmpdir = self._tmp.name
        self.script = Path(self.tmpdir) / 'gw-exec-emit.py'
        self.script.write_text(CHILD_SCRIPT, encoding='utf-8')

    def tearDown(self):
        self._tmp.cleanup()

    def _cmd(self, *args):
        return ' '.join([sys.executable, str(self.script)] + [str(a) for a in args])

    def _leaked_for_our_script(self):
        """Return live Popen entries still held for this test's child script."""
        active = getattr(subprocess, '_active', None) or []
        return [p for p in active if 'gw-exec-emit' in str(p.args)]

    def test_large_stdout_does_not_block(self):
        """A command flooding stdout past the pipe buffer must still finish."""
        sentinel = Path(self.tmpdir) / 'flood_done'

        worker = execute_deployment(
            'demo/repo', self.tmpdir, self._cmd('flood', sentinel)
        )
        self.assertIsNotNone(worker)
        worker.join(timeout=30)

        self.assertFalse(worker.is_alive(), 'executor thread blocked on a full pipe')
        self.assertTrue(
            sentinel.exists(),
            'deployment command never completed: it blocked writing to an unread pipe'
        )

    def test_large_stderr_does_not_block(self):
        """stderr must be drained as well (it is merged into stdout)."""
        sentinel = Path(self.tmpdir) / 'stderr_done'

        worker = execute_deployment(
            'demo/repo', self.tmpdir, self._cmd('flood_stderr', sentinel)
        )
        worker.join(timeout=30)

        self.assertFalse(worker.is_alive(), 'executor thread blocked on a full pipe')
        self.assertTrue(sentinel.exists(), 'command blocked writing to stderr pipe')

    def test_child_is_reaped(self):
        """The child must be waited on, not left in subprocess._active."""
        sentinel = Path(self.tmpdir) / 'reap_done'

        worker = execute_deployment(
            'demo/repo', self.tmpdir, self._cmd('flood', sentinel)
        )
        worker.join(timeout=30)

        self.assertEqual(
            [], self._leaked_for_our_script(),
            'child process was never reaped (subprocess._active leak)'
        )

    def test_success_exit_code_logged(self):
        """A successful deployment records exit 0."""
        with self.assertLogs(level='INFO') as cm:
            worker = execute_deployment('demo/repo', self.tmpdir, self._cmd('ok'))
            worker.join(timeout=30)

        self.assertIn('Deployment finished (exit 0)', '\n'.join(cm.output))

    def test_failure_reports_exit_code_and_tail(self):
        """A failing deployment surfaces its exit code and output tail."""
        with self.assertLogs(level='WARNING') as cm:
            worker = execute_deployment('demo/repo', self.tmpdir, self._cmd('fail'))
            worker.join(timeout=30)

        output = '\n'.join(cm.output)
        self.assertIn('Deployment failed (exit 3)', output)
        self.assertIn('BOOM-LINE-1', output)
        self.assertIn('BOOM-LINE-2', output)

    def test_unstartable_command_returns_none(self):
        """A bad working directory is reported instead of raising."""
        missing = os.path.join(self.tmpdir, 'no-such-directory')

        with self.assertLogs(level='WARNING') as cm:
            result = execute_deployment('demo/repo', missing, 'true')

        self.assertIsNone(result)
        self.assertIn('Execution failed', '\n'.join(cm.output))


if __name__ == '__main__':
    unittest.main()

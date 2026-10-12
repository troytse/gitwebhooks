"""Command executor

Asynchronously executes deployment commands.
"""

import collections
import logging
import subprocess
import threading
from typing import Optional

# Number of trailing output lines reported when a deployment fails.
FAILURE_TAIL_LINES = 50


def _consume_output(proc: subprocess.Popen, repo_name: str) -> None:
    """Drain a deployment process output, then reap it.

    Reads the merged stdout/stderr stream until EOF so the command can never
    block on a full pipe, logs every line, and finally waits for the process
    so it does not linger in ``subprocess._active``.

    Args:
        proc: The running deployment process
        repo_name: Repository name (for logging)
    """
    tail = collections.deque(maxlen=FAILURE_TAIL_LINES)

    try:
        if proc.stdout is not None:
            for line in proc.stdout:
                line = line.rstrip('\n')
                tail.append(line)
                logging.debug('[%s] %s', repo_name, line)
    except (OSError, ValueError) as e:
        logging.warning('[%s] Failed to read command output: %s', repo_name, e)
    finally:
        if proc.stdout is not None:
            try:
                proc.stdout.close()
            except (OSError, ValueError):
                pass

    # Reap the child, otherwise it stays in subprocess._active forever and its
    # pipe read end is never released.
    returncode = proc.wait()

    if returncode == 0:
        logging.info('[%s] Deployment finished (exit 0)', repo_name)
    else:
        # Re-emit the tail at WARNING so failures stay visible even when
        # debug-level output is filtered out.
        logging.warning(
            '[%s] Deployment failed (exit %s); last %d line(s) of output:',
            repo_name, returncode, len(tail)
        )
        for line in tail:
            logging.warning('[%s]   %s', repo_name, line)


def execute_deployment(repo_name: str, cwd: str, cmd: str) -> Optional[threading.Thread]:
    """Execute deployment command

    Args:
        repo_name: Repository name (for logging)
        cwd: Working directory
        cmd: Command to execute

    Returns:
        The daemon worker thread draining the command output, or None if the
        command could not be started. Callers may ignore it; it is returned so
        the execution can be joined (used by tests).

    Note:
        Command executes asynchronously without blocking the server.
        stdout and stderr are merged into a pipe that is drained by a daemon
        thread: a command producing more output than the OS pipe buffer can
        never block, because the pipe is always read and the child is always
        reaped. stdin is set to DEVNULL to prevent file descriptor leaks.
    """
    logging.info('[%s] Executing: %s', repo_name, cmd)

    try:
        proc = subprocess.Popen(
            cmd,
            cwd=cwd,
            shell=True,
            stdin=subprocess.DEVNULL,   # Prevent inheriting stdin, avoid fd leaks
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,   # Merge, so a single reader drains both
            text=True,
            bufsize=1,                  # Line buffered
            errors='replace'            # Never raise on undecodable output
        )
    except (OSError, subprocess.SubprocessError) as e:
        logging.warning('[%s] Execution failed: %s', repo_name, e)
        return None

    worker = threading.Thread(
        target=_consume_output,
        args=(proc, repo_name),
        name='gitwebhooks-deploy-%s' % repo_name.replace('/', '-'),
        daemon=True
    )
    worker.start()
    return worker

"""Command executor

Asynchronously executes deployment commands.
"""

import logging
import subprocess


def execute_deployment(repo_name: str, cwd: str, cmd: str) -> None:
    """Execute deployment command

    Args:
        repo_name: Repository name (for logging)
        cwd: Working directory
        cmd: Command to execute

    Note:
        Command executes asynchronously without blocking the server.
        stdin is set to DEVNULL to prevent file descriptor leaks.
    """
    logging.info('[%s] Executing: %s', repo_name, cmd)

    try:
        subprocess.Popen(
            cmd,
            cwd=cwd,
            shell=True,
            stdin=subprocess.DEVNULL,  # Prevent inheriting stdin, avoid fd leaks
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    except (OSError, subprocess.SubprocessError) as e:
        logging.warning('[%s] Execution failed: %s', repo_name, e)

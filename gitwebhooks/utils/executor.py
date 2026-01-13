"""命令执行器

异步执行部署命令。
"""

import logging
import subprocess


def execute_deployment(repo_name: str, cwd: str, cmd: str) -> None:
    """执行部署命令

    Args:
        repo_name: 仓库名称（用于日志）
        cwd: 工作目录
        cmd: 要执行的命令

    Note:
        命令异步执行，不阻塞服务器。
        stdin 设置为 DEVNULL 避免文件描述符泄漏。
    """
    logging.info('[%s] Executing: %s', repo_name, cmd)

    try:
        subprocess.Popen(
            cmd,
            cwd=cwd,
            shell=True,
            stdin=subprocess.DEVNULL,  # 防止继承 stdin，避免 fd 泄漏
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    except (OSError, subprocess.SubprocessError) as e:
        logging.warning('[%s] Execution failed: %s', repo_name, e)

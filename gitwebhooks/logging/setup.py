"""日志配置

配置应用程序日志系统。
"""

import logging
import sys
from pathlib import Path


def setup_logging(log_file: str = None):
    """配置日志系统

    Args:
        log_file: 日志文件路径（空字符串表示不记录到文件）

    根据配置设置日志记录：
    - 如果 log_file 为空，只输出到 stdout
    - 如果 log_file 非空，同时输出到文件和 stdout
    - 如果日志目录不存在，只输出到 stdout（记录警告）

    Note:
        Python 3.8+ 使用 force 参数确保重新配置，
        早期版本手动清除现有 handlers。
    """
    handlers = []

    # 文件处理器
    if log_file:
        try:
            log_path = Path(log_file)
            # 确保日志目录存在
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            ))
            handlers.append(file_handler)
        except (OSError, IOError) as e:
            # 如果无法创建日志文件，回退到仅控制台输出
            import warnings
            warnings.warn(f'无法创建日志文件 {log_file}: {e}，将仅输出到控制台')

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    handlers.append(console_handler)

    # 配置根日志记录器
    # Python 3.8+ 支持 force 参数
    basic_config_kwargs = {
        'level': logging.DEBUG,
        'handlers': handlers,
    }
    if sys.version_info >= (3, 8):
        basic_config_kwargs['force'] = True
    else:
        # 早期版本：手动清除现有 handlers
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

    logging.basicConfig(**basic_config_kwargs)

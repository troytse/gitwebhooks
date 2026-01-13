"""服务器配置

定义服务器相关的配置数据类。
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from gitwebhooks.utils.exceptions import ConfigurationError


@dataclass
class ServerConfig:
    """服务器配置

    Attributes:
        address: 监听地址
        port: 监听端口
        log_file: 日志文件路径（空字符串表示不记录到文件）
        ssl_enabled: 是否启用 SSL
        ssl_key_file: SSL 密钥文件路径
        ssl_cert_file: SSL 证书文件路径
    """
    address: str
    port: int
    log_file: str
    ssl_enabled: bool = False
    ssl_key_file: Optional[str] = None
    ssl_cert_file: Optional[str] = None

    @classmethod
    def from_loader(cls, loader: 'ConfigLoader') -> 'ServerConfig':
        """从 ConfigLoader 创建服务器配置

        Args:
            loader: 配置加载器实例

        Returns:
            ServerConfig 实例
        """
        server_cfg = loader.get_server_config()
        ssl_cfg = loader.get_ssl_config()

        return cls(
            address=server_cfg['address'],
            port=server_cfg['port'],
            log_file=server_cfg['log_file'],
            ssl_enabled=ssl_cfg is not None,
            ssl_key_file=ssl_cfg['key_file'] if ssl_cfg else None,
            ssl_cert_file=ssl_cfg['cert_file'] if ssl_cfg else None,
        )

    def validate(self) -> None:
        """验证服务器配置

        Raises:
            ConfigurationError: 配置无效
        """
        if self.ssl_enabled:
            if not self.ssl_key_file:
                raise ConfigurationError('SSL enabled but key_file not specified')
            if not self.ssl_cert_file:
                raise ConfigurationError('SSL enabled but cert_file not specified')

            # 验证文件存在
            key_path = Path(self.ssl_key_file)
            cert_path = Path(self.ssl_cert_file)

            if not key_path.exists():
                raise ConfigurationError(f'SSL key file not found: {self.ssl_key_file}')
            if not cert_path.exists():
                raise ConfigurationError(f'SSL cert file not found: {self.ssl_cert_file}')

        # 验证端口范围
        if not (1 <= self.port <= 65535):
            raise ConfigurationError(f'Invalid port number: {self.port}')

        # 验证日志文件可写（如果指定）
        if self.log_file:
            log_path = Path(self.log_file)
            parent_dir = log_path.parent
            if parent_dir.exists() and not os.access(parent_dir, os.W_OK):
                raise ConfigurationError(f'Log directory not writable: {parent_dir}')

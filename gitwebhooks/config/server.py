"""Server configuration

Defines server-related configuration dataclasses.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from gitwebhooks.utils.exceptions import ConfigurationError


@dataclass
class ServerConfig:
    """Server configuration

    Attributes:
        address: Listen address
        port: Listen port
        log_file: Log file path (empty string means no file logging)
        ssl_enabled: Whether SSL is enabled
        ssl_key_file: SSL key file path
        ssl_cert_file: SSL certificate file path
    """
    address: str
    port: int
    log_file: str
    ssl_enabled: bool = False
    ssl_key_file: Optional[str] = None
    ssl_cert_file: Optional[str] = None

    @classmethod
    def from_loader(cls, loader: 'ConfigLoader') -> 'ServerConfig':
        """Create server configuration from ConfigLoader

        Args:
            loader: Configuration loader instance

        Returns:
            ServerConfig instance
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
        """Validate server configuration

        Raises:
            ConfigurationError: Configuration is invalid
        """
        if self.ssl_enabled:
            if not self.ssl_key_file:
                raise ConfigurationError('SSL enabled but key_file not specified')
            if not self.ssl_cert_file:
                raise ConfigurationError('SSL enabled but cert_file not specified')

            # Verify files exist
            key_path = Path(self.ssl_key_file)
            cert_path = Path(self.ssl_cert_file)

            if not key_path.exists():
                raise ConfigurationError(f'SSL key file not found: {self.ssl_key_file}')
            if not cert_path.exists():
                raise ConfigurationError(f'SSL cert file not found: {self.ssl_cert_file}')

        # Validate port range
        if not (1 <= self.port <= 65535):
            raise ConfigurationError(f'Invalid port number: {self.port}')

        # Validate log file writable (if specified)
        if self.log_file:
            log_path = Path(self.log_file)
            parent_dir = log_path.parent
            if parent_dir.exists() and not os.access(parent_dir, os.W_OK):
                raise ConfigurationError(f'Log directory not writable: {parent_dir}')

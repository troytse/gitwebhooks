"""HTTP and response constants definition

Defines all constants used in the project.
"""

from enum import Enum
from pathlib import Path

# HTTP Status Codes
HTTP_OK = 200
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_NOT_ACCEPTABLE = 406
HTTP_PRECONDITION_FAILED = 412
HTTP_INTERNAL_SERVER_ERROR = 500

# HTTP Content Types
CONTENT_TYPE_JSON = 'application/json'
CONTENT_TYPE_FORM_URLENCODED = 'application/x-www-form-urlencoded'

# HTTP Headers
HEADER_CONTENT_TYPE = 'Content-Type'
HEADER_CONTENT_LENGTH = 'Content-Length'
HEADER_GITHUB_EVENT = 'X-GitHub-Event'
HEADER_GITHUB_SIGNATURE = 'X-Hub-Signature'
HEADER_GITEE_EVENT = 'X-Gitee-Event'
HEADER_GITEE_TOKEN = 'X-Gitee-Token'
HEADER_GITEE_TIMESTAMP = 'X-Gitee-Timestamp'
HEADER_GITLAB_EVENT = 'X-Gitlab-Event'
HEADER_GITLAB_TOKEN = 'X-Gitlab-Token'

# Response Messages
MESSAGE_OK = b'OK'
MESSAGE_FORBIDDEN = 'Forbidden'
MESSAGE_BAD_REQUEST = 'Bad Request'
MESSAGE_UNAUTHORIZED = 'Unauthorized'
MESSAGE_NOT_FOUND = 'Not Found'
MESSAGE_NOT_ACCEPTABLE = 'Not Acceptable'
MESSAGE_PRECONDITION_FAILED = 'Precondition Failed'
MESSAGE_INTERNAL_SERVER_ERROR = 'Internal Server Error'

# Reserved configuration sections
RESERVED_SECTIONS = {'server', 'ssl', 'github', 'gitee', 'gitlab', 'custom'}

# Configuration file paths (in priority order)
CONFIG_PATH_USER = "~/.gitwebhooks.ini"
CONFIG_PATH_LOCAL = "/usr/local/etc/gitwebhooks.ini"
CONFIG_PATH_SYSTEM = "/etc/gitwebhooks.ini"
CONFIG_SEARCH_PATHS = [CONFIG_PATH_USER, CONFIG_PATH_LOCAL, CONFIG_PATH_SYSTEM]

# Sensitive field keywords
SENSITIVE_KEYWORDS = {"secret", "password", "token", "key", "passphrase"}

# ANSI color codes for sensitive field highlighting
COLOR_SENSITIVE = "\033[33m"  # Yellow
COLOR_RESET = "\033[0m"


class ConfigLevel(Enum):
    """Configuration file level for service installation

    Represents the three configuration file levels supported by gitwebhooks,
    ordered by priority (highest to lowest).
    """

    USER = "user"          # ~/.gitwebhooks.ini (highest priority)
    LOCAL = "local"        # /usr/local/etc/gitwebhooks.ini
    SYSTEM = "system"      # /etc/gitwebhooks.ini (lowest priority)

    def get_config_path(self) -> Path:
        """Get the configuration file path for this level

        Returns:
            Path object pointing to the configuration file
        """
        paths = {
            ConfigLevel.USER: Path(CONFIG_PATH_USER).expanduser(),
            ConfigLevel.LOCAL: Path(CONFIG_PATH_LOCAL),
            ConfigLevel.SYSTEM: Path(CONFIG_PATH_SYSTEM),
        }
        return paths[self]

    @classmethod
    def from_string(cls, value: str) -> 'ConfigLevel':
        """Create ConfigLevel from string value

        Args:
            value: String value ('user', 'local', or 'system')

        Returns:
            ConfigLevel enum value

        Raises:
            ValueError: If value is not a valid config level
        """
        try:
            return cls(value.lower())
        except ValueError:
            valid_values = ', '.join([e.value for e in cls])
            raise ValueError(
                f"Invalid config level '{value}'. Valid values are: {valid_values}"
            )

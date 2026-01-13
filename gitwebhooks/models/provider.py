"""Git platform provider enumeration

Defines supported Git hosting platform types.
"""

from enum import Enum, unique


@unique
class Provider(Enum):
    """Git platform provider type

    Supported Git hosting platforms:
    - GITHUB: GitHub platform
    - GITEE: Gitee platform (China)
    - GITLAB: GitLab platform
    - CUSTOM: Custom webhook platform
    """
    GITHUB = 'github'
    GITEE = 'gitee'
    GITLAB = 'gitlab'
    CUSTOM = 'custom'

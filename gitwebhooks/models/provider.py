"""Git 平台提供者枚举

定义支持的 Git 托管平台类型。
"""

from enum import Enum, unique


@unique
class Provider(Enum):
    """Git 平台提供者类型

    支持的 Git 托管平台：
    - GITHUB: Github 平台
    - GITEE: Gitee 平台（中国）
    - GITLAB: Gitlab 平台
    - CUSTOM: 自定义 webhook 平台
    """
    GITHUB = 'github'
    GITEE = 'gitee'
    GITLAB = 'gitlab'
    CUSTOM = 'custom'

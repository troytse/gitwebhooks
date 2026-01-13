"""签名验证结果数据类

表示签名验证的结果状态。
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SignatureVerificationResult:
    """签名验证结果

    Attributes:
        is_valid: 验证是否通过
        error_message: 验证失败时的错误描述
    """
    is_valid: bool
    error_message: Optional[str] = None

    @classmethod
    def success(cls) -> 'SignatureVerificationResult':
        """创建成功的验证结果

        Returns:
            is_valid=True 的结果对象
        """
        return cls(is_valid=True)

    @classmethod
    def failure(cls, message: str) -> 'SignatureVerificationResult':
        """创建失败的验证结果

        Args:
            message: 错误描述

        Returns:
            is_valid=False 且包含错误消息的结果对象
        """
        return cls(is_valid=False, error_message=message)

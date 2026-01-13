"""签名验证器基类

定义签名验证的抽象接口。
"""

from abc import ABC, abstractmethod

from gitwebhooks.models.result import SignatureVerificationResult


class SignatureVerifier(ABC):
    """签名验证器基类

    所有平台特定的验证器必须继承此类并实现验证方法。
    """

    @abstractmethod
    def verify(self, payload: bytes, signature: str, secret: str,
               **kwargs) -> SignatureVerificationResult:
        """验证签名

        Args:
            payload: 原始请求体字节
            signature: 请求中的签名字符串
            secret: 配置的密钥
            **kwargs: 平台特定的额外参数（如 timestamp）

        Returns:
            SignatureVerificationResult 实例

        Raises:
            SignatureValidationError: 验证失败时（可选）
        """
        pass

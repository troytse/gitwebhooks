"""验证器工厂类

根据提供者类型创建对应的验证器实例。
"""

from gitwebhooks.models.provider import Provider
from gitwebhooks.auth.verifier import SignatureVerifier
from gitwebhooks.auth.github import GithubSignatureVerifier
from gitwebhooks.auth.gitee import GiteeSignatureVerifier
from gitwebhooks.auth.gitlab import GitlabTokenVerifier
from gitwebhooks.auth.custom import CustomTokenVerifier
from gitwebhooks.utils.exceptions import UnsupportedProviderError


class VerifierFactory:
    """验证器工厂类

    根据提供者类型创建对应的验证器实例
    """

    _verifiers = {
        Provider.GITHUB: GithubSignatureVerifier(),
        Provider.GITEE: GiteeSignatureVerifier(),
        Provider.GITLAB: GitlabTokenVerifier(),
        Provider.CUSTOM: None,  # Custom verifier created dynamically
    }

    @classmethod
    def get_verifier(cls, provider: Provider,
                    verify_enabled: bool = True) -> SignatureVerifier:
        """获取提供者对应的验证器

        Args:
            provider: 提供者类型
            verify_enabled: 是否启用验证（仅对 CUSTOM 有效）

        Returns:
            SignatureVerifier 实例

        Raises:
            UnsupportedProviderError: 不支持的提供者
        """
        if provider == Provider.CUSTOM:
            return CustomTokenVerifier(verify_enabled=verify_enabled)

        verifier = cls._verifiers.get(provider)
        if verifier is None:
            raise UnsupportedProviderError(f'No verifier for provider: {provider}')
        return verifier

    @classmethod
    def create_github_verifier(cls) -> GithubSignatureVerifier:
        """创建 Github 验证器（便利方法）"""
        return GithubSignatureVerifier()

    @classmethod
    def create_gitee_verifier(cls) -> GiteeSignatureVerifier:
        """创建 Gitee 验证器（便利方法）"""
        return GiteeSignatureVerifier()

    @classmethod
    def create_gitlab_verifier(cls) -> GitlabTokenVerifier:
        """创建 Gitlab 验证器（便利方法）"""
        return GitlabTokenVerifier()

    @classmethod
    def create_custom_verifier(cls, verify_enabled: bool = True) -> CustomTokenVerifier:
        """创建自定义验证器（便利方法）

        Args:
            verify_enabled: 是否启用验证
        """
        return CustomTokenVerifier(verify_enabled=verify_enabled)

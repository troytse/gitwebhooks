"""Verifier factory class

Creates corresponding verifier instances based on provider type.
"""

from gitwebhooks.models.provider import Provider
from gitwebhooks.auth.verifier import SignatureVerifier
from gitwebhooks.auth.github import GithubSignatureVerifier
from gitwebhooks.auth.gitee import GiteeSignatureVerifier
from gitwebhooks.auth.gitlab import GitlabTokenVerifier
from gitwebhooks.auth.custom import CustomTokenVerifier
from gitwebhooks.utils.exceptions import UnsupportedProviderError


class VerifierFactory:
    """Verifier factory class

    Creates corresponding verifier instances based on provider type
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
        """Get verifier for the specified provider

        Args:
            provider: Provider type
            verify_enabled: Whether verification is enabled (CUSTOM only)

        Returns:
            SignatureVerifier instance

        Raises:
            UnsupportedProviderError: Unsupported provider
        """
        if provider == Provider.CUSTOM:
            return CustomTokenVerifier(verify_enabled=verify_enabled)

        verifier = cls._verifiers.get(provider)
        if verifier is None:
            raise UnsupportedProviderError(f'No verifier for provider: {provider}')
        return verifier

    @classmethod
    def create_github_verifier(cls) -> GithubSignatureVerifier:
        """Create GitHub verifier (convenience method)"""
        return GithubSignatureVerifier()

    @classmethod
    def create_gitee_verifier(cls) -> GiteeSignatureVerifier:
        """Create Gitee verifier (convenience method)"""
        return GiteeSignatureVerifier()

    @classmethod
    def create_gitlab_verifier(cls) -> GitlabTokenVerifier:
        """Create GitLab verifier (convenience method)"""
        return GitlabTokenVerifier()

    @classmethod
    def create_custom_verifier(cls, verify_enabled: bool = True) -> CustomTokenVerifier:
        """Create custom verifier (convenience method)

        Args:
            verify_enabled: Whether verification is enabled
        """
        return CustomTokenVerifier(verify_enabled=verify_enabled)

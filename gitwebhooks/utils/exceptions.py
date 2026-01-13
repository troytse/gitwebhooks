"""自定义异常类

定义项目中使用的所有异常类型。
"""


class WebhookError(Exception):
    """Webhook 处理错误基类"""
    pass


class SignatureValidationError(WebhookError):
    """签名验证失败"""
    pass


class UnsupportedEventError(WebhookError):
    """不支持的事件类型"""
    pass


class UnsupportedProviderError(WebhookError):
    """无法识别的平台提供者"""
    pass


class ConfigurationError(WebhookError):
    """配置错误或缺失"""
    pass


class RequestParseError(WebhookError):
    """请求解析失败"""
    pass

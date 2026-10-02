"""AI 凭据的认证加密边界，主密钥自动保存在系统用户私有目录，不进入公开响应。"""
from cryptography.fernet import Fernet, InvalidToken
from fastapi import status
from pydantic import SecretStr

from web408.core.exceptions import BusinessException
from web408.integrations.ai_local_secrets import AiLocalSecretError, get_master_key


KEY_VERSION = "1"


def _get_cipher(*, create: bool) -> Fernet:
    """只在明确写入新 Go Key 时允许补建，解密绝不替换缺失或损坏的主密钥。"""
    try:
        configured_key = get_master_key(create=create)
        return Fernet(configured_key.get_secret_value().encode("ascii"))
    except AiLocalSecretError as error:
        raise BusinessException(status.HTTP_503_SERVICE_UNAVAILABLE, str(error)) from None
    except (ValueError, TypeError):
        raise BusinessException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "AI 加密主密钥格式无效，请恢复原文件；不会自动覆盖",
        ) from None


def encrypt_api_key(api_key: SecretStr) -> tuple[str, str]:
    """返回加密载荷及主密钥版本，明文不交给数据库。"""
    ciphertext = _get_cipher(create=True).encrypt(api_key.get_secret_value().encode("utf-8"))
    return ciphertext.decode("ascii"), KEY_VERSION


def decrypt_api_key(ciphertext: str, key_version: str) -> SecretStr:
    """仅供后续服务端调用使用，不把密文或解密异常原文带出边界。"""
    if key_version != KEY_VERSION:
        raise BusinessException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "AI 凭据主密钥版本不匹配，请恢复原主密钥或重新填写 API Key",
        )
    cipher = _get_cipher(create=False)
    try:
        plaintext = cipher.decrypt(ciphertext.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError, TypeError):
        raise BusinessException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "AI 凭据无法解密，请检查主密钥或重新填写 API Key",
        ) from None
    return SecretStr(plaintext)

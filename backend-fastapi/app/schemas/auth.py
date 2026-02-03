"""
认证模块请求与响应模型
"""
from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class RegisterRequest(BaseModel):
    """用户注册请求"""
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="用户名",
        examples=["testuser"]
    )
    password: str = Field(
        ...,
        min_length=6,
        max_length=20,
        description="密码",
        examples=["123456"]
    )
    email: Optional[EmailStr] = Field(
        default=None,
        description="邮箱地址",
        examples=["test@example.com"]
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "username": "testuser",
                    "password": "123456",
                    "email": "test@example.com"
                }
            ]
        }
    }


class LoginRequest(BaseModel):
    """用户登录请求"""
    username: str = Field(
        ...,
        description="用户名",
        examples=["admin"]
    )
    password: str = Field(
        ...,
        description="密码",
        examples=["123456"]
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "username": "admin",
                    "password": "123456"
                }
            ]
        }
    }


class AuthResponse(BaseModel):
    """认证成功响应"""
    token: str = Field(
        ...,
        description="JWT Token",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]
    )
    username: str = Field(
        ...,
        description="用户名",
        examples=["admin"]
    )
    role: str = Field(
        ...,
        description="用户角色",
        examples=["ADMIN"]
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "username": "admin",
                    "role": "ADMIN"
                }
            ]
        }
    }

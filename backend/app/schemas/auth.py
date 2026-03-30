from pydantic import BaseModel, EmailStr, Field
from typing import Literal


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    recaptcha_token: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    has_completed_onboarding: bool = True


class UserInToken(BaseModel):
    id: str
    role: Literal["student", "tutor", "coordinator"]


class MessageResponse(BaseModel):
    message: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class CreateUserRequest(BaseModel):
    """Schema para crear un nuevo usuario (solo coordinadores)"""
    email: EmailStr = Field(..., description="Email del usuario")
    password: str = Field(..., min_length=8, description="Contraseña (mínimo 8 caracteres)")
    full_name: str = Field(..., min_length=3, description="Nombre completo del usuario")
    role: Literal["student", "tutor"] = Field(..., description="Rol del usuario (student o tutor)")


class UserCreatedResponse(BaseModel):
    """Response cuando se crea un usuario exitosamente"""
    id: str
    email: str
    full_name: str
    role: str
    message: str

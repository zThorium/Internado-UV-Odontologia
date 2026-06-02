from pydantic import BaseModel, EmailStr, Field, model_validator
from typing import Literal


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


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
    profession: str | None = Field(default=None, description="Profesión del tutor clínico")
    available_hours_per_week: int | None = Field(default=None, ge=1, le=80)
    tutor_training_status: Literal["yes", "no", "in_progress"] | None = Field(default=None)

    @model_validator(mode="after")
    def validate_tutor_fields(self):
        if self.role != "tutor":
            return self

        if not self.profession:
            raise ValueError("La profesión es obligatoria para tutores")
        if self.available_hours_per_week is None:
            raise ValueError("Las horas disponibles por semana son obligatorias para tutores")
        if self.tutor_training_status is None:
            raise ValueError("La capacitación de tutor clínico es obligatoria para tutores")
        return self


class UserCreatedResponse(BaseModel):
    """Response cuando se crea un usuario exitosamente"""
    id: str
    email: str
    full_name: str
    role: str
    profession: str | None = None
    available_hours_per_week: int | None = None
    tutor_training_status: str | None = None
    message: str

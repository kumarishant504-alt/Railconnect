from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session
from app.database.engine import get_session
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.user import (UserRegister, UserResponse, TokenResponse,
                               ForgotPasswordRequest, ResetPasswordRequest, ChangePasswordRequest)
from app.schemas.common import MessageResponse
from app.services import auth_service

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=201)
def register(data: UserRegister, session: Session = Depends(get_session)):
    return auth_service.register_user(data, session)


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(),
          session: Session = Depends(get_session)):
    user = auth_service.authenticate_user(form_data.username, form_data.password, session)
    token = auth_service.create_token_for_user(user)
    return TokenResponse(access_token=token, token_type="bearer",
                         user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(data: ForgotPasswordRequest, session: Session = Depends(get_session)):
    return MessageResponse(message=auth_service.initiate_password_reset(data.email, session))


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(data: ResetPasswordRequest, session: Session = Depends(get_session)):
    return MessageResponse(message=auth_service.reset_password(data.token, data.new_password, session))


@router.post("/change-password", response_model=MessageResponse)
def change_password(data: ChangePasswordRequest,
                    current_user: User = Depends(get_current_user),
                    session: Session = Depends(get_session)):
    return MessageResponse(message=auth_service.change_password(
        current_user, data.current_password, data.new_password, session))

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from secrets import token_urlsafe
import jwt
from jwt import PyJWTError
from passlib.context import CryptContext
from supabase import Client, create_client
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")  # Asegúrate de cambiar esto en producción
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Inicializar Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configurar el router
router = APIRouter()

# Configurar el contexto de encriptación de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configurar OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Modelos
class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: str
    is_active: bool = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class PasswordResetRequest(BaseModel):
    email: str

class PasswordReset(BaseModel):
    token: str
    new_password: str

# Funciones de utilidad
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Verificar si el token está en la lista negra
        response = supabase.table("invalidated_tokens").select("*").eq("token", token).execute()
        if response.data:
            raise credentials_exception

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except PyJWTError:
        raise credentials_exception

    user = get_user_by_email(token_data.email)
    if user is None:
        raise credentials_exception
    return user

def get_user_by_email(email: str):
    try:
        response = supabase.table("users").select("*").eq("email", email).execute()
        if response.data:
            return User(**response.data[0])
        return None
    except Exception as e:
        print(f"Error getting user: {e}")
        return None

# Endpoints
@router.post("/signup", response_model=Token)
async def signup(user: UserCreate):
    # Verificar si el usuario ya existe
    if get_user_by_email(user.email):
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Crear nuevo usuario
    hashed_password = get_password_hash(user.password)
    try:
        new_user = {
            "email": user.email,
            "hashed_password": hashed_password,
            "is_active": True
        }
        response = supabase.table("users").insert(new_user).execute()
        
        # Crear token de acceso
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating user: {str(e)}"
        )

@router.post("/login", response_model=Token)
async def login(user_data: UserCreate):
    # Buscar usuario por email
    response = supabase.table("users").select("*").eq("email", user_data.email).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Obtener el hash de la contraseña
    hashed_password = response.data[0]["hashed_password"]
    if not verify_password(user_data.password, hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_data.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user), token: str = Depends(oauth2_scheme)):
    try:
        # Decodificar el token para obtener su tiempo de expiración
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        expires_at = datetime.fromtimestamp(payload.get("exp"))
        
        # Agregar el token a la lista negra
        invalidated_token = {
            "token": token,
            "expires_at": expires_at.isoformat()
        }
        supabase.table("invalidated_tokens").insert(invalidated_token).execute()
        
        return {"message": "Successfully logged out"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error during logout: {str(e)}"
        )

@router.post("/forgot-password")
async def forgot_password(request: PasswordResetRequest):
    user = get_user_by_email(request.email)
    if not user:
        # Por seguridad, no revelamos si el email existe o no
        return {"message": "If the email exists, a reset link will be sent"}
    
    # Generar token único
    reset_token = token_urlsafe(32)
    expires = datetime.utcnow() + timedelta(hours=24)
    
    try:
        # Actualizar usuario con el token
        supabase.table("users").update({
            "reset_token": reset_token,
            "reset_token_expires": expires.isoformat()
        }).eq("email", request.email).execute()
        
        # TODO: Enviar email con el link de reset
        # Por ahora, solo retornamos el token (en producción, esto se enviaría por email)
        return {"reset_token": reset_token}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing password reset: {str(e)}"
        )

@router.post("/reset-password")
async def reset_password(reset: PasswordReset):
    try:
        # Buscar usuario con el token válido
        response = supabase.table("users").select("*").eq("reset_token", reset.token).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=400,
                detail="Invalid or expired reset token"
            )
            
        user_data = response.data[0]
        
        # Verificar si el token ha expirado
        expires = datetime.fromisoformat(user_data["reset_token_expires"])
        if datetime.utcnow() > expires:
            raise HTTPException(
                status_code=400,
                detail="Reset token has expired"
            )
        
        # Actualizar contraseña y limpiar token
        hashed_password = get_password_hash(reset.new_password)
        supabase.table("users").update({
            "hashed_password": hashed_password,
            "reset_token": None,
            "reset_token_expires": None
        }).eq("id", user_data["id"]).execute()
        
        return {"message": "Password has been reset successfully"}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500,
            detail=f"Error resetting password: {str(e)}"
        )

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

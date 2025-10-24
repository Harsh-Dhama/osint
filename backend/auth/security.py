from passlib.context import CryptContext
import importlib
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import os
from dotenv import load_dotenv

load_dotenv()

# Password hashing
# Detect whether the native 'bcrypt' module is functional. Some environments
# ship an incompatible 'bcrypt' wheel which causes passlib to fail when using
# the bcrypt handler. If bcrypt appears broken, prefer pbkdf2_sha256.
_bcrypt_ok = False
try:
    _bcrypt = importlib.import_module("bcrypt")
    # basic sanity checks - the module should expose either a version/about
    # attribute or the low-level API
    if hasattr(_bcrypt, "__about__") or hasattr(_bcrypt, "hashpw"):
        # Now attempt to actually perform a tiny hash to ensure the backend
        # is functional (some broken wheels expose functions but are unusable).
        try:
            test_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
            _ = test_ctx.hash("test")
            _bcrypt_ok = True
        except Exception:
            _bcrypt_ok = False
except Exception:
    _bcrypt_ok = False

if _bcrypt_ok:
    pwd_schemes = ["bcrypt", "pbkdf2_sha256"]
else:
    pwd_schemes = ["pbkdf2_sha256"]

pwd_context = CryptContext(schemes=pwd_schemes, deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

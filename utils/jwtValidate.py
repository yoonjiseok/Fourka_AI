import jwt
from fastapi import HTTPException, status
from jwt import PyJWTError
from config import settings

SECRET_KEY = settings.JWT_SECRET  # 환경변수에서 불러옴
ALGORITHM = "HS512"

def verify_jwt_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

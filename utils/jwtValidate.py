import jwt
import base64
import logging # 로깅 라이브러리 추가
from fastapi import HTTPException, status
from jwt.exceptions import ExpiredSignatureError, InvalidSignatureError, PyJWTError
from config import settings

# 로거 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

secret_b64 = settings.JWT_SECRET
secret = base64.b64decode(secret_b64)
ALGORITHM = "HS512"

def verify_jwt_token(token: str):
    try:
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
        return payload
    except ExpiredSignatureError:
        logger.warning("Token has expired.") # 서버 로그에 만료 사실 기록
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired", # 클라이언트에게 조금 더 친절한 메시지
        )
    except InvalidSignatureError:
        logger.error("Invalid token signature.") # 서명 오류는 심각한 문제일 수 있으므로 error 레벨로 기록
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    except PyJWTError as e:
        logger.error(f"An unexpected JWT error occurred: {e}") # 그 외 JWT 오류 기록
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
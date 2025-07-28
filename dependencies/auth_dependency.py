from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from utils.jwtValidate import verify_jwt_token

"""
JWT 토큰 인증 관련 의존성 함수들
Spring API Gateway에서 토큰 만료 시간과 사용자 존재 여부를 체크하므로,
Python에서는 토큰 서명 검증과 payload 추출만 수행
"""

# HTTPBearer 보안 설정 (auto_error=False로 개발시 선택사항으로 만듦)
security = HTTPBearer(auto_error=True)

def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """
    개발용 더미 사용자 정보 반환 (JWT 검증 비활성화)
    
    Args:
        credentials: HTTPAuthorizationCredentials 객체 (Bearer 토큰 포함)
    
    Returns:
        dict: 더미 사용자 정보
    """
    # 개발용 더미 데이터 반환 (토큰이 있든 없든 상관없이)
    return {
        "sub": "dev@example.com",
        "user_id": 123,
        "role": "admin"
    }
    
    """
    실제 JWT 검증 코드 (개발 중 주석 처리)
    
    if not credentials:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    token = credentials.credentials  # Bearer 토큰에서 실제 토큰 부분 추출
    payload = verify_jwt_token(token)
    return payload 
    """
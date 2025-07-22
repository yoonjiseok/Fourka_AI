from fastapi import Header, HTTPException
from utils.jwtValidate import verify_jwt_token

"""
토큰이 위조/만료되지 않았는지만 자동으로 확인
payload에 담긴 정보의 진짜 유효성(ex. user_id가 실제 존재하는지, 권한이 맞는지 등은 확인 안 함)
"""
def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")
    token = authorization.split(" ")[1]
    payload = verify_jwt_token(token)
    return payload  # {'sub': 이메일, 'user_id': userId, 'role': role, ...}

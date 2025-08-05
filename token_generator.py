# main.py
import jwt
from datetime import datetime, timedelta, timezone


def get_test_token():
    """서버의 SECRET_KEY로 직접 서명한 테스트 토큰을 발급합니다."""
    JWT_SECRET = "fourkachipfourkachipfourkachipfourkachipfourkachipfourkachipfourkachipfourkachipfourkachipfourkachipfourkachipfourkachipfourkachipfourkachipfourkachipfourkachipfourkachipfourkachipfourkachipfourkachipfourkachipfourkachipfourkach"

    # HS512 알고리즘을 사용합니다.
    algorithm = "HS512"
    
    # 토큰에 담을 정보 (payload)
    payload = {
        "sub": "test@example.com",
        "user_id": 999,
        "role": "TESTER",
        "company_id": 1,
        "iat": datetime.now(timezone.utc), # 생성 시간
        "exp": datetime.now(timezone.utc) + timedelta(minutes=120) # 만료 시간 (120분)
    }
    
    # 서버가 가진 시크릿 키로 토큰을 생성합니다.
    print(f"{JWT_SECRET}")
    test_token = jwt.encode(payload, JWT_SECRET, algorithm=algorithm)
    
    return {test_token}

if __name__ == "__main__":
    print(get_test_token())
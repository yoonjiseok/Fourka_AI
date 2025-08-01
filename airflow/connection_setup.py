#!/usr/bin/env python3
"""
FourKa DB Connection 자동 설정 스크립트
Airflow Connection을 프로그래밍적으로 생성합니다.
"""

import os
from airflow.models import Connection
from airflow.utils.session import provide_session

@provide_session
def create_fourka_db_connection(session=None):
    """FourKa DB Connection 생성"""
    
    # 기존 Connection 삭제 (있다면)
    existing_conn = session.query(Connection).filter(
        Connection.conn_id == 'fourka_db'
    ).first()
    
    if existing_conn:
        session.delete(existing_conn)
        print("기존 fourka_db Connection 삭제됨")
    
    # 새 Connection 생성
    new_conn = Connection(
        conn_id='fourka_db',
        conn_type='postgres',
        host=os.getenv('FOURKA_DB_HOST', 'host.docker.internal'),  # Docker 내부에서 호스트 접근
        port=int(os.getenv('FOURKA_DB_PORT', '5432')),
        schema=os.getenv('FOURKA_DB_NAME', 'fourka_db'),
        login=os.getenv('FOURKA_DB_USER', 'postgres'),
        password=os.getenv('FOURKA_DB_PASSWORD', 'password')
    )
    
    session.add(new_conn)
    session.commit()
    
    print(f"✅ FourKa DB Connection 생성 완료!")
    print(f"   Host: {new_conn.host}")
    print(f"   Port: {new_conn.port}")  
    print(f"   Schema: {new_conn.schema}")
    print(f"   User: {new_conn.login}")

if __name__ == "__main__":
    create_fourka_db_connection() 
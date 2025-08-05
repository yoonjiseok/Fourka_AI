import boto3
import uuid
from datetime import datetime
from fastapi import UploadFile
from config import settings
from botocore.exceptions import ClientError, NoCredentialsError


class S3Service:
    """카카오 클라우드 Object Storage 서비스 클래스"""
    def __init__(self):
        try:
            # 카카오 클라우드 Object Storage 클라이언트 초기화
            client_config = {
                'region_name': settings.S3_REGION,
                'aws_access_key_id': settings.S3_ACCESS_KEY_ID,
                'aws_secret_access_key': settings.S3_SECRET_ACCESS_KEY
            }
            
            # 카카오 클라우드 엔드포인트 설정
            client_config['endpoint_url'] = settings.S3_ENDPOINT_URL
                
            self.s3_client = boto3.client('s3', **client_config)
            self.bucket_name = settings.S3_BUCKET_NAME
            self.region = settings.S3_REGION
            
        except NoCredentialsError:
            raise Exception("카카오 클라우드 인증 정보가 설정되지 않았습니다.")
        except Exception as e:
            raise Exception(f"카카오 클라우드 클라이언트 초기화 실패: {e}")

    async def upload_file(self, file: UploadFile, folder_name: str = "documents") -> str:
        """
        파일을 카카오 클라우드에 업로드하고 URL을 반환합니다.
        
        Args:
            file: 업로드할 파일 (FastAPI UploadFile)
            folder_name: 카카오 클라우드 내 폴더명 (기본값: "documents")
            
        Returns:
            str: 카카오 클라우드 파일 URL
        """
        try:
            # 고유한 파일명 생성
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            file_extension = file.filename.split('.')[-1] if '.' in file.filename else ''
            s3_key = f"{folder_name}/{timestamp}_{unique_id}.{file_extension}"
            
            # 파일 내용 읽기
            file_content = await file.read()
            await file.seek(0)  # 포인터를 다시 처음으로 이동
            
            # 카카오 클라우드에 업로드
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=file.content_type or 'application/octet-stream'
            )
            
            # 카카오 클라우드 URL 생성
            base_url = settings.S3_ENDPOINT_URL.rstrip('/')
            s3_url = f"{base_url}/{self.bucket_name}/{s3_key}"
            
            return s3_url
            
        except ClientError as e:
            raise Exception(f"카카오 클라우드 업로드 실패: {e}")
        except Exception as e:
            raise Exception(f"파일 업로드 중 오류 발생: {e}")

    def delete_file(self, s3_url: str) -> bool:
        """
        카카오 클라우드에서 파일을 삭제합니다.
        
        Args:
            s3_url: 삭제할 파일의 카카오 클라우드 URL
            
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            # URL에서 S3 키 추출 (카카오 클라우드)
            s3_key = s3_url.split(f"/{self.bucket_name}/")[1]
            
            # 카카오 클라우드에서 파일 삭제
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            return True
            
        except ClientError as e:
            print(f"카카오 클라우드 파일 삭제 실패: {e}")
            return False
        except Exception as e:
            print(f"파일 삭제 중 오류 발생: {e}")
            return False    
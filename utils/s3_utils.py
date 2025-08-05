import difflib

import boto3
import fitz
import io
from urllib.parse import urlparse
from botocore.exceptions import NoCredentialsError, ClientError

from config import settings

# boto3 S3 클라이언트 초기화
s3_client = boto3.client(
    's3',
    aws_access_key_id=settings.S3_ACCESS_KEY_ID,
    aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
    region_name=settings.S3_REGION_NAME,
    endpoint_url=settings.S3_ENDPOINT_URL,
    # 카카오클라우드 S3 호환성을 위한 설정
    use_ssl=True,
    verify=True
)


def get_key_from_url(url: str) -> str:
    """전체 S3 URL에서 객체 키(파일 경로)를 추출합니다."""
    print(f"URL 파싱 시작: {url}")
    
    try:
        # 카카오클라우드 S3 URL 형식: https://endpoint/v1/project_id/bucket_name/key
        if "/v1/" in url and settings.S3_PROJECT_ID in url and settings.S3_BUCKET_NAME in url:
            parts = url.split(f"/v1/{settings.S3_PROJECT_ID}/{settings.S3_BUCKET_NAME}/")
            if len(parts) > 1:
                key = parts[1]
                print(f"카카오클라우드 형식으로 파싱된 키: {key}")
                return key
        
        # AWS S3 형식: https://bucket.s3.region.amazonaws.com/key
        if ".s3." in url and ".amazonaws.com" in url:
            parsed_url = urlparse(url)
            # 버킷명을 제거한 경로 반환
            path_parts = parsed_url.path.lstrip('/').split('/', 1)
            if len(path_parts) > 1:
                key = path_parts[1]
                print(f"AWS S3 형식으로 파싱된 키: {key}")
                return key
            else:
                key = path_parts[0] if path_parts else ""
                print(f"AWS S3 형식으로 파싱된 키: {key}")
                return key
        
        # 기존 방식으로 fallback
        parsed_url = urlparse(url)
        key = parsed_url.path.lstrip('/')
        print(f"기본 방식으로 파싱된 키: {key}")
        return key
        
    except Exception as e:
        print(f"URL 파싱 중 오류 발생: {e}")
        # 기존 방식으로 fallback
        parsed_url = urlparse(url)
        return parsed_url.path.lstrip('/')


def download_file_from_s3(url: str) -> io.BytesIO | None:
    """
    S3 URL에서 파일을 다운로드하여 메모리 내 바이트 스트림으로 반환합니다.
    :param url: S3 파일의 전체 URL
    :return: 파일 내용이 담긴 BytesIO 객체 또는 실패 시 None
    """
    bucket_name = settings.S3_BUCKET_NAME
    object_key = get_key_from_url(url)

    print(f"S3에서 파일 다운로드를 시작합니다: bucket='{bucket_name}', key='{object_key}'")
    print(f"S3 클라이언트 설정: endpoint_url={settings.S3_ENDPOINT_URL}, region={settings.S3_REGION_NAME}")

    try:
        file_obj = io.BytesIO()
        s3_client.download_fileobj(bucket_name, object_key, file_obj)
        file_obj.seek(0)  # 스트림의 포인터를 맨 앞으로 이동
        print("다운로드 성공.")
        return file_obj
    except NoCredentialsError:
        print("S3 인증 정보를 찾을 수 없습니다.")
        return None
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            print(f"파일을 찾을 수 없습니다: {object_key}")
        else:
            print(f"S3 클라이언트 오류 발생: {e}")
        return None
    except Exception as e:
        print(f"파일 다운로드 중 알 수 없는 오류 발생: {e}")
        return None

def compare_text(text1: str, text2: str) -> str:
    """두 텍스트의 차이를 비교하는 헬퍼 함수"""
    differ = difflib.Differ()
    diff = differ.compare(text1.splitlines(), text2.splitlines())
    changed_lines = [line for line in diff if line.startswith('+ ') or line.startswith('- ')]
    return '\n'.join(changed_lines)

def extract_text_from_pdf(pdf_stream: io.BytesIO) -> str:
    """PDF 메모리 스트림에서 텍스트를 추출합니다."""
    full_text = ""
    try:
        with fitz.open(stream=pdf_stream, filetype="pdf") as doc:
            for page in doc:
                full_text += page.get_text()
        print("텍스트 추출 성공.")
        return full_text
    except Exception as e:
        print(f"PDF 처리 중 오류 발생: {e}")
        return ""
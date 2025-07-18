import difflib
import fitz  # PyMuPDF
import io
import requests


def compare_text(text1, text2) -> str:
    """
    Args:
        text1: 원본 텍스트 내용
        text2: 변경 후의 텍스트 내용

    Returns: text1과 text2의 차이를 +,-로 return함

    ['가나다라', '마바사', '아자차', '까따빠']
    ['가나다라', '마바사', '마바사다', '아자차']
    + 마바사다
    - 까따빠
    """
    differ = difflib.Differ()
    diff = differ.compare(text1.splitlines(), text2.splitlines())
    changed_lines = [line for line in diff if line.startswith('+ ') or line.startswith('- ')]
    return '\n'.join(changed_lines)

def download_file_to_memory(url: str) -> io.BytesIO | None:
    """
    :param url: S3 URL
    :return: 바이트 스트림으로 메모리 반환
    """
    print(f"'{url}'에서 파일 다운로드를 시작합니다...")
    try:
        response = requests.get(url)
        response.raise_for_status()
        print("다운로드 성공.")
        return io.BytesIO(response.content)
    except requests.exceptions.RequestException as e:
        print(f"URL 요청 중 오류 발생: {e}")
        return None

def extract_text_from_pdf(pdf_stream: io.BytesIO) -> str:
    """
    :param pdf_stream: pdf 메모리 스트림을 입력받음
    :return: 읽은 pdf의 텍스트 반환
    """
    print("PDF에서 텍스트 추출을 시작합니다...")
    full_text = ""
    try:
        # 스트림으로부터 PDF 문서를 엽니다.
        with fitz.open(stream=pdf_stream, filetype="pdf") as doc:
            for page in doc:
                full_text += page.get_text()
        print("텍스트 추출 성공.")
    except Exception as e:
        print(f"PDF 처리 중 오류 발생: {e}")
    return full_text

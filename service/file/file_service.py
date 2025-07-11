from fastapi import File
import fitz

def read_file(file: File):
    content = fitz.open(file)
    # 임베딩 시작


async def update_file(file_name, doc_id):

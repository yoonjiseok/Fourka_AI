from fastapi import File
import fitz

def read_file(file: File):
    content = fitz.open(file)
    # 임베딩 시작


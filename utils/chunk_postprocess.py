import re

def clean_text(text):
    if not text:
        return ""
    
    # 1. null 문자 제거
    text = text.replace('\x00', ' ')
    
    # 2. 특수 유니코드 문자 제거 (개선)
    # zero-width space 등 특수 공백 문자 제거
    text = re.sub(r'[\u200b\u200c\u200d\u200e\u200f]', '', text)
    # 특수 박스 문자 제거
    text = re.sub(r'[󰠆󰠏󰠐󰠌󰠏]', '', text)
    # 특수 사각형 문자 제거
    text = re.sub(r'[□■▢▣▤▥▦▧▨▩]', '', text)
    
    # 3. 탭을 공백으로 변환
    text = text.replace('\t', ' ')
                  
    # 4. 연속된 공백을 하나로 통일
    text = re.sub(r'[ \t]+', ' ', text)
    
    # 5. 줄바꿈 처리
    # - 연속된 줄바꿈을 하나로 통일
    text = re.sub(r'\n+', '\n', text)
    # - 줄 끝의 공백 제거
    text = re.sub(r' +\n', '\n', text)
    # - 줄 시작의 공백 제거
    text = re.sub(r'\n +', '\n', text)
    
    # 6. 중간에 끊어진 텍스트 연결 (개선)
    # - 줄바꿈으로 분리된 한글 단어들을 연결
    text = re.sub(r'([가-힣])\s*\n\s*([가-힣])', r'\1\2', text)
    # - 줄바꿈으로 분리된 영문 단어들을 연결
    text = re.sub(r'([a-zA-Z])\s*\n\s*([a-zA-Z])', r'\1\2', text)
    # - 줄바꿈으로 분리된 숫자들을 연결
    text = re.sub(r'(\d)\s*\n\s*(\d)', r'\1\2', text)
    # - 줄바꿈으로 분리된 조사들을 연결
    text = re.sub(r'([은는이가을를의에로와과])\s*\n\s*([가-힣])', r'\1\2', text)
    
    # 7. 불필요한 구두점 정리
    # - 연속된 점들을 하나로 통일
    text = re.sub(r'[․·]+', '․', text)
    # - 점 뒤의 불필요한 공백 제거
    text = re.sub(r'[․·]\s+', '․', text)
    
    # 8. 특수 문자 정리
    # - 연속된 쉼표 정리
    text = re.sub(r',+', ',', text)
    # - 쉼표 뒤 공백 정리
    text = re.sub(r',\s+', ', ', text)
    
    # 9. 한글 띄어쓰기 개선 (더 정교하게)
    # - 조사 앞의 불필요한 공백 제거
    text = re.sub(r'\s+([은는이가을를의에로와과])\s+', r'\1 ', text)
    # - 조사 뒤의 불필요한 공백 제거
    text = re.sub(r'\s+([은는이가을를의에로와과])\s+', r' \1 ', text)
    
    # 10. 한글 단어 사이 띄어쓰기 개선
    # - "회사와직원은이" 같은 문제 해결
    text = re.sub(r'([가-힣])([가-힣])([가-힣])([가-힣])([가-힣])([가-힣])([가-힣])([가-힣])', r'\1\2\3\4\5\6\7 \8', text)
    text = re.sub(r'([가-힣])([가-힣])([가-힣])([가-힣])([가-힣])([가-힣])([가-힣])', r'\1\2\3\4\5\6 \7', text)
    text = re.sub(r'([가-힣])([가-힣])([가-힣])([가-힣])([가-힣])([가-힣])', r'\1\2\3\4\5 \6', text)
    
    # 11. 조사 앞에 공백 추가
    text = re.sub(r'([가-힣])([은는이가을를의에로와과])([가-힣])', r'\1\2 \3', text)
    
    # 12. 남은 연속 공백을 하나로 통일
    text = re.sub(r' +', ' ', text)
    
    # 13. 앞뒤 공백 제거
    text = text.strip()
    
    return text

def merge_incomplete_chunks(chunks):
    """
    불완전한 청크들을 병합하는 후처리 함수 (개선된 버전)
    """
    if not chunks:
        return chunks
    
    merged_chunks = []
    current_chunk = chunks[0]
    
    for i in range(1, len(chunks)):
        next_chunk = chunks[i]
        
        # 현재 청크가 불완전한지 확인
        current_text = current_chunk.text.strip()
        next_text = next_chunk.text.strip()
        
        # 병합 조건들
        should_merge = False
        
        # 1. 현재 청크가 짧고 불완전한 문장으로 끝나는 경우
        if len(current_text) < 300 and (
            current_text.endswith('다.') or 
            current_text.endswith('것') or
            current_text.endswith('함') or
            current_text.endswith('음') or
            current_text.endswith('고') or
            current_text.endswith('며') or
            current_text.endswith('서')
        ):
            should_merge = True
        
        # 2. 번호가 연속되는 경우 (예: 1), 2), 3))
        if re.search(r'\d+\)$', current_text) and re.search(r'^\d+\)', next_text):
            should_merge = True
        
        # 3. 문장이 중간에 끊어진 경우
        if not current_text.endswith(('.', '다.', '음', '함', '것', '고', '며', '서')) and len(current_text) < 400:
            should_merge = True
        
        # 4. 제목 다음에 짧은 내용이 있는 경우
        if re.search(r'^제\s*\d+\s*조', current_text) and len(next_text) < 200:
            should_merge = True
        
        if should_merge:
            # 청크 병합
            merged_text = current_chunk.text + '\n' + next_chunk.text
            # 새로운 청크 객체 생성 (간단한 방식)
            from unstructured.documents.elements import Text
            merged_chunk = Text(merged_text)
            merged_chunk.metadata = current_chunk.metadata
            current_chunk = merged_chunk
        else:
            merged_chunks.append(current_chunk)
            current_chunk = next_chunk
    
    merged_chunks.append(current_chunk)
    return merged_chunks

def validate_chunk_quality(chunks):
    """
    청크 품질을 검증하고 개선하는 함수
    """
    improved_chunks = []
    
    for chunk in chunks:
        text = chunk.text.strip()
        
        # 너무 짧은 청크 제거 (50자 미만)
        if len(text) < 50:
            continue
            
        # 너무 긴 청크 분할 (8000자 초과)
        if len(text) > 8000:
            # 문장 단위로 분할
            sentences = re.split(r'[.!?。]', text)
            current_part = ""
            
            for sentence in sentences:
                if len(current_part + sentence) > 4000:
                    if current_part:
                        from unstructured.documents.elements import Text
                        new_chunk = Text(current_part.strip())
                        new_chunk.metadata = chunk.metadata
                        improved_chunks.append(new_chunk)
                    current_part = sentence
                else:
                    current_part += sentence + "."
            
            if current_part.strip():
                from unstructured.documents.elements import Text
                new_chunk = Text(current_part.strip())
                new_chunk.metadata = chunk.metadata
                improved_chunks.append(new_chunk)
        else:
            improved_chunks.append(chunk)
    
    return improved_chunks

def add_overlap_to_chunks(chunks, overlap_chars=200):
    """
    청크들에 overlapping을 추가하는 후처리 함수
    """
    if not chunks or len(chunks) <= 1:
        return chunks
    
    overlapped_chunks = []
    
    for i in range(len(chunks)):
        current_chunk = chunks[i]
        current_text = current_chunk.text
        
        # 이전 청크의 끝 부분을 현재 청크 앞에 추가
        if i > 0:
            prev_chunk = chunks[i-1]
            prev_text = prev_chunk.text
            # 이전 청크의 마지막 overlap_chars만큼 가져오기
            overlap_text = prev_text[-overlap_chars:] if len(prev_text) > overlap_chars else prev_text
            current_text = overlap_text + "\n" + current_text
        
        # 다음 청크의 시작 부분을 현재 청크 뒤에 추가
        if i < len(chunks) - 1:
            next_chunk = chunks[i+1]
            next_text = next_chunk.text
            # 다음 청크의 처음 overlap_chars만큼 가져오기
            overlap_text = next_text[:overlap_chars] if len(next_text) > overlap_chars else next_text
            current_text = current_text + "\n" + overlap_text
        
        # 새로운 청크 객체 생성
        from unstructured.documents.elements import Text
        overlapped_chunk = Text(current_text)
        overlapped_chunk.metadata = current_chunk.metadata
        overlapped_chunks.append(overlapped_chunk)
    
    return overlapped_chunks
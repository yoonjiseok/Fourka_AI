from typing import List, Any, Dict

from api.routes.chat import chatDTO


def similar_chunks(chunks, threshold):
    """
    HIL 서비스에서 유사한 청크의 임계도를 확인합니다.
    하나라도 임계값 이상의 청크가 있다면 HIL서비스는 실행되지 않습니다.
    """
    for chunk in chunks:
        if chunk.distance >= threshold:
            return False
    return True


def HIL(metadata: List[Dict[str, Any]]):  # 1. 파라미터 타입을 딕셔너리 리스트로 수정
    """
    HIL 서비스는 검색된 유사한 문서에 대해서 반환합니다.
    """
    ans_list = []

    for data in metadata:
        data_dict = {
            "문서 제목": data['title'],
            "문서 페이지": data['page_number'],
            }
        ans_list.append(data_dict)
    return chatDTO.HILResponse(
        answer="검색결과가 없습니다. 유사한 문서는 아래의 부분입니다. 만약 해당 부분에서도 원하시는 정보가 없을 시 FAQ에 문의해주세요.",
        metadata=ans_list)








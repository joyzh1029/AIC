"""
LLM 응답 포맷 처리를 위한 유틸리티
"""
import logging
from typing import Union, Dict, Any

def format_llm_response(response: Any) -> str:
    """
    LLM 응답을 문자열 형식으로 변환
    
    Args:
        response: LLM에서 반환된 응답 (dict, str 등 다양한 형식 가능)
        
    Returns:
        str: 포맷팅된 문자열 응답
    """
    try:
        # 디버그 로깅
        logging.debug(f"Formatting response of type: {type(response)}")
        
        # 이미 문자열인 경우
        if isinstance(response, str):
            return response
            
        # langchain 응답 객체인 경우
        if hasattr(response, 'content'):
            content = response.content
            logging.debug(f"Found content attribute: {content}")
            return format_llm_response(content)
            
        # dict 형식인 경우
        if isinstance(response, dict):
            logging.debug(f"Processing dict response with keys: {response.keys()}")
            # 우선순위에 따라 필드 확인
            for field in ['response', 'content', 'text', 'message']:
                if field in response:
                    return str(response[field])
            
            # thought 필드가 있는 경우 특별 처리
            if 'thought' in response:
                logging.debug("Found thought field, extracting main content")
                # thought 필드를 제외한 다른 필드들의 값을 결합
                other_fields = {k: v for k, v in response.items() if k != 'thought'}
                if other_fields:
                    return ' '.join(str(v) for v in other_fields.values())
                return "응답을 생성하는 중입니다..."
            
            # 모든 값을 연결
            return ' '.join(str(v) for v in response.values())
            
        # 기타 객체인 경우
        if hasattr(response, '__str__'):
            return str(response)
            
        return "응답을 처리할 수 없습니다."
        
    except Exception as e:
        logging.error(f"Response formatting error: {str(e)}")
        logging.error(f"Problematic response: {response}")
        return "죄송합니다. 응답을 처리하는 중에 오류가 발생했습니다." 
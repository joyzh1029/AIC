from openai import OpenAI
from backend.config import config
from backend.tools import SearchTool
import json

class SimpleAgent:
    def __init__(self):
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.search_tool = SearchTool()
    
    def _get_tools(self):
        """사용 가능한 도구"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_web",
                    "description": "웹에서 정보를 검색합니다",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "검색할 키워드"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_news",
                    "description": "최신 뉴스를 검색합니다",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "검색할 뉴스 키워드"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_answer",
                    "description": "질문에 대한 직접적인 답변을 생성합니다",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "답변을 원하는 질문"
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]
    
    def query(self, user_input: str) -> str:
        """사용자 질문 처리"""
        messages = [
            {
                "role": "system",
                "content": """당신은 검색 도우미입니다. 
사용자가 정보를 요청하면 적절한 도구를 사용해서 정보를 찾아주세요.
- 웹 검색: search_web
- 뉴스 검색: search_news  
- 직접 답변: get_answer

검색 결과를 바탕으로 친절하고 정확한 답변을 제공하세요."""
            },
            {"role": "user", "content": user_input}
        ]
        
        # LLM 호출
        response = self.client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=messages,
            tools=self._get_tools(),
            tool_choice="auto"
        )
        
        message = response.choices[0].message
        
        # Tool 사용이 필요한 경우
        if message.tool_calls:
            messages.append(message)
            
            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
                query = arguments.get('query', '')
                print(f"🔧 도구 사용: {function_name} - {query}")
                
                # 도구 실행
                if function_name == "search_web":
                    results = self.search_tool.search_web(query)
                elif function_name == "search_news":
                    results = self.search_tool.search_news(query)
                elif function_name == "get_answer":
                    results = self.search_tool.get_answer(query)
                else:
                    results = []
                
                # 결과를 메시지에 추가
                tool_message = {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": json.dumps(results, ensure_ascii=False) if isinstance(results, list) else str(results)
                }
                messages.append(tool_message)
            
            # 최종 응답 생성
            final_response = self.client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=messages
            )
            
            return final_response.choices[0].message.content
        
        return message.content
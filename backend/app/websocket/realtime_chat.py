from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
import asyncio
import websockets
import json
import logging
import time
from typing import Dict
from ..config import settings

# 로그 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# 활성 WebSocket 연결 저장
active_connections: Dict[str, WebSocket] = {}
# 각 연결에 대한 MiniMax WebSocket 저장
minimax_connections: Dict[str, websockets.WebSocketServerProtocol] = {}

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.minimax_connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.heartbeat_tasks: Dict[str, asyncio.Task] = {}
        # 음성 데이터 누적을 위한 버퍼
        self.audio_buffers: Dict[str, str] = {}
        self.welcome_in_progress: Dict[str, bool] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        # 심박수 작업 시작
        self.heartbeat_tasks[client_id] = asyncio.create_task(self._heartbeat_loop(client_id))
        logger.info(f"클라이언트 {client_id} 연결됨")

    async def _heartbeat_loop(self, client_id: str):
        """심박수 루프 - 연결 유지를 위해 정기적으로 ping 전송"""
        try:
            while client_id in self.active_connections:
                await asyncio.sleep(15)  # 15초마다 ping
                if client_id in self.active_connections:
                    # 연결 상태를 먼저 확인
                    websocket = self.active_connections.get(client_id)
                    if websocket and self._is_websocket_connected(websocket):
                        try:
                            await self.send_personal_message({
                                "type": "ping",
                                "timestamp": int(time.time())
                            }, client_id)
                        except Exception as e:
                            logger.error(f"{client_id} 심박수 전송 실패: {e}")
                            break
                    else:
                        logger.warning(f"{client_id}의 WebSocket이 이미 닫혀있음, 심박수 루프 종료")
                        break
        except asyncio.CancelledError:
            logger.info(f"{client_id} 심박수 작업이 취소됨")
        except Exception as e:
            logger.error(f"{client_id} 심박수 루프 오류: {e}")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        # 심박수 작업 정리
        if client_id in self.heartbeat_tasks:
            self.heartbeat_tasks[client_id].cancel()
            del self.heartbeat_tasks[client_id]
        if client_id in self.minimax_connections:
            asyncio.create_task(self.close_minimax_connection(client_id))
        # 음성 버퍼 및 환영 메시지 상태 정리
        if client_id in self.audio_buffers:
            del self.audio_buffers[client_id]
        if client_id in self.welcome_in_progress:
            del self.welcome_in_progress[client_id]
        logger.info(f"클라이언트 {client_id} 연결 해제됨")

    async def close_minimax_connection(self, client_id: str):
        if client_id in self.minimax_connections:
            try:
                minimax_ws = self.minimax_connections[client_id]
                # 연결 상태 확인 후 연결 종료
                try:
                    if minimax_ws.state.name == 'OPEN':
                        await minimax_ws.close()
                except AttributeError:
                    # 연결 상태 확인 방법 2
                    try:
                        await minimax_ws.close()
                    except:
                        pass
                del self.minimax_connections[client_id]
                logger.info(f"{client_id}의 MiniMax 연결 종료됨")
            except Exception as e:
                logger.error(f"{client_id}의 MiniMax 연결 종료 중 오류: {e}")

    def _is_websocket_connected(self, websocket: WebSocket) -> bool:
        """WebSocket 연결 상태를 안전하게 확인"""
        try:
            # FastAPI WebSocket 상태 확인
            if hasattr(websocket, 'client_state') and websocket.client_state == WebSocketState.CONNECTED:
                return True
            elif hasattr(websocket, 'application_state') and websocket.application_state == WebSocketState.CONNECTED:
                return True
            else:
                return False
        except Exception:
            return False
    
    def _clean_base64_data(self, data: str) -> str:
        """Base64 데이터를 정리하고 유효성을 검증"""
        if not data:
            return ""
        
        # 공백, 줄바꿈 등 제거
        cleaned = ''.join(data.split())
        
        # Base64 문자만 유지 (A-Z, a-z, 0-9, +, /, =)
        import re
        cleaned = re.sub(r'[^A-Za-z0-9+/=]', '', cleaned)
        
        # Base64 패딩 확인 및 수정
        if cleaned:
            padding = len(cleaned) % 4
            if padding > 0:
                cleaned += '=' * (4 - padding)
        
        return cleaned
    
    async def _send_large_audio(self, client_id: str, audio_data: str):
        """대용량 음성 파일 분할 전송 - Base64 무결성 보장"""
        MAX_CHUNK_SIZE = 800000  # 800KB per chunk (留出其他JSON数据的空间)
        
        if len(audio_data) <= MAX_CHUNK_SIZE:
            # 음성 데이터가 작으면 직접 전송
            await self.send_personal_message({
                "type": "welcome_audio_complete",
                "audio": audio_data,
                "message": "환영 메시지 음성이 준비되었습니다"
            }, client_id)
        else:
            # 음성 데이터가 크면 Base64 무결성을 보장하여 분할 전송
            # Base64는 4문자 단위로 작동하므로, 4의 배수로 분할해야 함
            safe_chunk_size = (MAX_CHUNK_SIZE // 4) * 4  # 4의 배수로 맞춤
            
            chunks = []
            for i in range(0, len(audio_data), safe_chunk_size):
                chunk = audio_data[i:i + safe_chunk_size]
                chunks.append(chunk)
            
            total_chunks = len(chunks)
            logger.info(f"{client_id}: 대용량 음성 파일 분할 전송, 총 길이: {len(audio_data)}, 분할 수: {total_chunks}, 안전한 청크 크기: {safe_chunk_size}")
            
            # 각 청크가 유효한 base64인지 검증
            for i, chunk in enumerate(chunks):
                try:
                    import base64
                    base64.b64decode(chunk)
                    logger.info(f"{client_id}: 청크 {i+1} Base64 검증 성공 (길이: {len(chunk)})")
                except Exception as e:
                    logger.error(f"{client_id}: 청크 {i+1} Base64 검증 실패: {e}")
                    # 검증 실패 시 전체 전송 중단
                    await self.send_personal_message({
                        "type": "error",
                        "message": "음성 데이터 처리 중 오류가 발생했습니다."
                    }, client_id)
                    return
            
            # 검증된 청크들을 순차적으로 전송
            for i, chunk in enumerate(chunks):
                message = {
                    "type": "welcome_audio_chunk",
                    "chunk_index": i,
                    "total_chunks": total_chunks,
                    "audio": chunk,
                    "message": f"음성 청크 {i+1}/{total_chunks}"
                }
                
                success = await self.send_personal_message(message, client_id)
                if not success:
                    logger.error(f"{client_id}: 음성 청크 {i+1} 전송 실패")
                    return
                
                logger.info(f"{client_id}: 음성 청크 {i+1}/{total_chunks} 전송 완료 (길이: {len(chunk)})")
                
                # 짧은 지연으로 네트워크 부하 방지
                await asyncio.sleep(0.1)
            
            # 모든 청크 전송 완료 알림
            await self.send_personal_message({
                "type": "welcome_audio_complete",
                "message": "환영 메시지 음성이 준비되었습니다"
            }, client_id)
    
    def _validate_and_clean_final_audio(self, audio_data: str) -> str:
        """최종 음성 데이터 검증 및 정리"""
        if not audio_data:
            return ""
        
        # 원본 데이터 샘플 로깅
        sample_start = audio_data[:100] if len(audio_data) > 100 else audio_data
        sample_end = audio_data[-100:] if len(audio_data) > 100 else ""
        logger.info(f"원본 음성 데이터 샘플 - 시작: {sample_start}")
        logger.info(f"원본 음성 데이터 샘플 - 끝: {sample_end}")
        
        # 기본 정리
        cleaned = self._clean_base64_data(audio_data)
        
        # Base64 디코딩 테스트
        try:
            import base64
            decoded = base64.b64decode(cleaned)
            logger.info(f"음성 데이터 검증 성공: {len(cleaned)}자 -> {len(decoded)}바이트")
            return cleaned
        except Exception as e:
            logger.error(f"음성 데이터 검증 실패: {e}")
            logger.error(f"실패한 데이터 샘플: {cleaned[:200]}...")
            
            # 추가 정리 시도
            try:
                # 더 엄격한 정리: 연속된 '=' 제거 후 재패딩
                import re
                cleaned = re.sub(r'=+$', '', cleaned)
                padding = len(cleaned) % 4
                if padding > 0:
                    cleaned += '=' * (4 - padding)
                
                decoded = base64.b64decode(cleaned)
                logger.info(f"음성 데이터 복구 성공: {len(cleaned)}자")
                return cleaned
            except Exception as e2:
                logger.error(f"음성 데이터 복구 실패: {e2}")
                # 최후의 시도: 비 ASCII 문자 제거
                try:
                    ascii_only = ''.join(char for char in audio_data if ord(char) < 128)
                    final_cleaned = self._clean_base64_data(ascii_only)
                    if final_cleaned:
                        decoded = base64.b64decode(final_cleaned)
                        logger.info(f"ASCII 정리 후 복구 성공: {len(final_cleaned)}자")
                        return final_cleaned
                except Exception as e3:
                    logger.error(f"최종 복구 시도 실패: {e3}")
                    return ""

    async def send_personal_message(self, message: dict, client_id: str):
        """안전하게 개인 메시지를 전송하는 메서드"""
        if client_id not in self.active_connections:
            logger.debug(f"{client_id} 클라이언트가 연결되어 있지 않음")
            return False
            
        websocket = self.active_connections[client_id]
        
        # 연결 상태 확인
        if not self._is_websocket_connected(websocket):
            logger.warning(f"{client_id}의 WebSocket이 연결되지 않음")
            self.disconnect(client_id)
            return False
            
        try:
            await websocket.send_text(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"{client_id}에게 메시지 전송 실패: {e}")
            # 연결이 끊어진 경우 정리
            self.disconnect(client_id)
            return False

    def is_minimax_connected(self, client_id: str) -> bool:
        """MiniMax 연결 상태 확인"""
        if client_id not in self.minimax_connections:
            return False
        minimax_ws = self.minimax_connections[client_id]
        # websockets.connect() 반환값은 ClientConnection 객체이며 state 속성 확인
        try:
            return minimax_ws.state.name == 'OPEN'
        except AttributeError:
            # state 속성이 없으면 다른 방법으로 확인
            return hasattr(minimax_ws, 'open') and minimax_ws.open
    
    async def send_welcome_message(self, client_id: str):
        """환영 메시지를 자동으로 생성하여 전송"""
        try:
            logger.info(f"{client_id}: 환영 메시지 생성 시작")
            
            # 환영 메시지 생성 중 표시
            self.welcome_in_progress[client_id] = True
            self.audio_buffers[client_id] = ""  # 음성 버퍼 초기화
            
            # 클라이언트에게 환영 메시지 생성 중임을 알림
            await self.send_personal_message({
                "type": "welcome_generating",
                "message": "환영 메시지를 생성하고 있습니다..."
            }, client_id)
            
            # 환영 메시지를 MiniMax에 전송
            welcome_message = {
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "user",
                    "status": "completed",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "안녕하세요! 처음 만나는 사용자에게 친근하고 자연스러운 환영 인사를 해주세요."
                        }
                    ]
                }
            }
            
            success = await self.send_to_minimax(client_id, welcome_message)
            if success:
                # 음성 응답 생성 요청
                response_message = {
                    "event_id": f"welcome_event_{client_id}_{int(time.time())}",
                    "type": "response.create",
                    "response": {
                        "modalities": ["text", "audio"],
                        "instructions": "Please respond in Korean with a warm, friendly welcome message. Keep it natural and conversational.",
                        "voice": "male-qn-qingse",
                        "output_audio_format": "pcm16",
                        "temperature": 0.7,
                        "max_response_output_tokens": "1000",
                        "status": "incomplete"
                    }
                }
                await self.send_to_minimax(client_id, response_message)
                logger.info(f"{client_id}: 환영 메시지 요청 전송 완료")
            else:
                logger.error(f"{client_id}: 환영 메시지 전송 실패")
                self.welcome_in_progress[client_id] = False
                
        except Exception as e:
            logger.error(f"{client_id}: 환영 메시지 생성 중 오류: {e}")
            self.welcome_in_progress[client_id] = False

    async def connect_to_minimax(self, client_id: str, model: str = None):
        """MiniMax와의 WebSocket 연결 생성 및 초기화 메시지 전송"""
        if model is None:
            model = settings.minimax_ws_default_model
        
        url = f"{settings.minimax_ws_realtime_base_url}?model={model}"
        headers = [
            ("Authorization", f"Bearer {settings.minimax_api_key}")
        ]
        
        try:
            logger.info(f"{client_id}: MiniMax 연결 시도 - URL: {url}")
            logger.info(f"{client_id}: API 키 설정됨: {'예' if settings.minimax_api_key and settings.minimax_api_key != 'default_api_key' else '아니오'}")
            
            # asyncio.wait_for를 사용하여 연결 시간 제한 적용
            minimax_ws = await asyncio.wait_for(
                websockets.connect(
                    url,
                    additional_headers=headers,
                    ping_interval=20,
                    ping_timeout=10
                ),
                timeout=30  # 연결 시간 제한 30초
            )
            self.minimax_connections[client_id] = minimax_ws
            logger.info(f"{client_id}에 대해 MiniMax에 연결됨")

            # 연결 성공 후 session.created 이벤트 대기, 즉시 초기화 메시지 전송 필요 없음
            logger.info(f"{client_id}에 대해 MiniMax WebSocket 연결 완료, 세션 생성 대기 중")

            # MiniMax 응답을 수신하는 작업 시작
            asyncio.create_task(self.listen_minimax_responses(client_id))
            
            return True
        except asyncio.TimeoutError:
            logger.error(f"{client_id}의 MiniMax 연결 시간 초과 (30초)")
            # WebSocket이 연결되어 있는 경우에만 오류 메시지 전송
            if client_id in self.active_connections:
                await self.send_personal_message({
                    "type": "error",
                    "message": "MiniMax 연결 시간 초과. 네트워크 연결을 확인하세요."
                }, client_id)
            return False
        except Exception as e:
            logger.error(f"{client_id}의 MiniMax 연결 실패: {e}")
            # WebSocket이 연결되어 있는 경우에만 오류 메시지 전송
            if client_id in self.active_connections:
                await self.send_personal_message({
                    "type": "error",
                    "message": f"MiniMax 연결 실패: {str(e)}"
                }, client_id)
            return False

    async def listen_minimax_responses(self, client_id: str):
        """MiniMax의 응답을 수신하여 클라이언트에 전달"""
        try:
            while client_id in self.minimax_connections:
                minimax_ws = self.minimax_connections[client_id]
                
                # 연결 상태 확인
                try:
                    if minimax_ws.state.name != 'OPEN':
                        logger.info(f"{client_id}의 MiniMax 연결이 종료됨")
                        break
                except AttributeError:
                    # 연결 상태 확인 방법 2
                    if hasattr(minimax_ws, 'open') and not minimax_ws.open:
                        logger.info(f"{client_id}의 MiniMax 연결이 종료됨")
                        break
                
                try:
                    # 타임아웃 설정으로 무한 대기 방지
                    message = await asyncio.wait_for(minimax_ws.recv(), timeout=30)
                    
                    try:
                        response_data = json.loads(message)
                        logger.info(f"{client_id}의 MiniMax 이벤트 수신: {response_data.get('type', 'unknown')}")
                        
                        # API 문서에 따라 다른 유형의 이벤트 처리
                        event_type = response_data.get('type')
                        
                        if event_type == 'session.created':
                            logger.info(f"{client_id}: MiniMax 세션이 생성되었습니다")
                            await self.send_personal_message({
                                "type": "minimax_response",
                                "data": response_data
                            }, client_id)
                            
                            # 세션 생성 후 자동으로 환영 메시지 생성
                            await self.send_welcome_message(client_id)
                            
                        elif event_type == 'response.text.delta':
                            # 텍스트 증분 업데이트 처리
                            delta_text = response_data.get('delta', '')
                            await self.send_personal_message({
                                "type": "minimax_response",
                                "data": {
                                    "type": "text_delta",
                                    "text": delta_text
                                }
                            }, client_id)
                            
                        elif event_type == 'response.text.done':
                            # 텍스트 완료 처리
                            final_text = response_data.get('text', '')
                            await self.send_personal_message({
                                "type": "minimax_response",
                                "data": {
                                    "type": "text_complete",
                                    "text": final_text
                                }
                            }, client_id)
                            
                        elif event_type == 'response.audio.delta':
                            # 음성 증분 업데이트 처리 - 후端에서 누적
                            audio_delta = response_data.get('delta', '')
                            if audio_delta and client_id in self.audio_buffers:
                                # 원본 데이터 샘플 로깅
                                delta_sample = audio_delta[:50] + "..." + audio_delta[-50:] if len(audio_delta) > 100 else audio_delta
                                logger.info(f"{client_id}: 원본 델타 샘플: {delta_sample}")
                                
                                # Base64 데이터 정리 후 누적
                                cleaned_delta = self._clean_base64_data(audio_delta)
                                if cleaned_delta:
                                    self.audio_buffers[client_id] += cleaned_delta
                                    logger.info(f"{client_id}: 음성 델타 누적, 원본 길이: {len(audio_delta)}, 정리된 길이: {len(cleaned_delta)}, 총 길이: {len(self.audio_buffers[client_id])}")
                                    
                                    # 누적 후 샘플 로깅
                                    buffer_sample = self.audio_buffers[client_id][:50] + "..." + self.audio_buffers[client_id][-50:] if len(self.audio_buffers[client_id]) > 100 else self.audio_buffers[client_id]
                                    logger.info(f"{client_id}: 누적 버퍼 샘플: {buffer_sample}")
                            
                            # 환영 메시지가 아닌 경우에만 실시간 전송
                            if not self.welcome_in_progress.get(client_id, False):
                                await self.send_personal_message({
                                    "type": "minimax_response",
                                    "data": {
                                        "type": "audio_delta",
                                        "audio": audio_delta  # Base64 인코딩된 음성 데이터
                                    }
                                }, client_id)
                            
                        elif event_type == 'response.audio.done':
                            # 음성 완료 처리 - 환영 메시지인 경우 누적된 데이터 전송
                            if self.welcome_in_progress.get(client_id, False):
                                # 환영 메시지: 누적된 음성 데이터 전송
                                accumulated_audio = self.audio_buffers.get(client_id, '')
                                
                                # 최종 Base64 검증 및 정리
                                final_audio = self._validate_and_clean_final_audio(accumulated_audio)
                                
                                logger.info(f"{client_id}: 환영 메시지 음성 완료, 원본 길이: {len(accumulated_audio)}, 최종 길이: {len(final_audio)}")
                                
                                if final_audio:
                                    # 음성 데이터가 너무 큰 경우 분할 전송
                                    await self._send_large_audio(client_id, final_audio)
                                else:
                                    logger.error(f"{client_id}: 환영 메시지 음성 데이터가 유효하지 않음")
                                    await self.send_personal_message({
                                        "type": "error",
                                        "message": "음성 데이터 생성에 실패했습니다"
                                    }, client_id)
                                
                                # 환영 메시지 생성 완료
                                self.welcome_in_progress[client_id] = False
                                self.audio_buffers[client_id] = ""
                            else:
                                # 일반 메시지: 기존 방식 유지
                                final_audio = response_data.get('audio', '')
                                await self.send_personal_message({
                                    "type": "minimax_response",
                                    "data": {
                                        "type": "audio_complete",
                                        "audio": final_audio  # Base64 인코딩된 음성 데이터
                                    }
                                }, client_id)
                            
                        elif event_type == 'response.done':
                            # 응답 완료 처리
                            logger.info(f"{client_id}: MiniMax 응답이 완료되었습니다")
                            response_obj = response_data.get('response', {})
                            output = response_obj.get('output', [])
                            
                            # 완전한 응답 텍스트 추출
                            if output:
                                for item in output:
                                    if item.get('type') == 'message' and item.get('role') == 'assistant':
                                        content = item.get('content', [])
                                        for c in content:
                                            if c.get('type') == 'text':
                                                await self.send_personal_message({
                                                    "type": "minimax_response",
                                                    "data": {
                                                        "type": "response_complete",
                                                        "text": c.get('text', '')
                                                    }
                                                }, client_id)
                                                
                        elif event_type == 'error':
                            # 오류 처리
                            error_info = response_data.get('error', {})
                            error_message = error_info.get('message', 'Unknown error')
                            logger.error(f"{client_id}: MiniMax 오류: {error_message}")
                            await self.send_personal_message({
                                "type": "error",
                                "message": f"MiniMax 오류: {error_message}"
                            }, client_id)
                            
                        elif event_type == 'response.audio_transcript.done':
                            # 음성 전사 완료 처리
                            transcript = response_data.get('transcript', '')
                            
                            if self.welcome_in_progress.get(client_id, False):
                                # 환영 메시지의 전사 텍스트
                                logger.info(f"{client_id}: 환영 메시지 전사 완료: {transcript}")
                                await self.send_personal_message({
                                    "type": "welcome_text_complete", 
                                    "text": transcript,
                                    "message": "환영 메시지 텍스트가 준비되었습니다"
                                }, client_id)
                            else:
                                # 일반 메시지의 전사 텍스트
                                await self.send_personal_message({
                                    "type": "minimax_response",
                                    "data": {
                                        "type": "response.audio_transcript.done",
                                        "transcript": transcript
                                    }
                                }, client_id)
                                
                        elif event_type == 'response.output_item.done':
                            # 응답 항목 완료 처리
                            logger.debug(f"{client_id}: 응답 항목 완료")
                            if not self.welcome_in_progress.get(client_id, False):
                                await self.send_personal_message({
                                    "type": "minimax_response",
                                    "data": response_data
                                }, client_id)
                        
                        else:
                            # 다른 이벤트 유형 처리
                            if not self.welcome_in_progress.get(client_id, False):
                                await self.send_personal_message({
                                    "type": "minimax_response",
                                    "data": response_data
                                }, client_id)
                            
                    except json.JSONDecodeError as e:
                        logger.error(f"{client_id}의 MiniMax 응답 파싱 실패: {e}")
                        
                except asyncio.TimeoutError:
                    # 타임아웃은 정상적인 상황일 수 있음
                    continue
                except websockets.exceptions.ConnectionClosed:
                    logger.info(f"{client_id}의 MiniMax 연결이 정상 종료됨")
                    break
                except Exception as e:
                    logger.error(f"{client_id}의 MiniMax 메시지 수신 중 오류: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"{client_id}의 MiniMax 응답 수신 중 예외: {e}")
        finally:
            # 정리 작업
            if client_id in self.minimax_connections:
                await self.close_minimax_connection(client_id)
            # WebSocket이 여전히 연결되어 있는 경우에만 상태 메시지 전송
            if client_id in self.active_connections:
                await self.send_personal_message({
                    "type": "connection_status",
                    "connected": False,
                    "message": "MiniMax 연결이 종료되었습니다"
                }, client_id)

    async def send_to_minimax(self, client_id: str, message: dict):
        """MiniMax로 메시지 전송"""
        # 연결 상태 확인
        if not self.is_minimax_connected(client_id):
            logger.warning(f"{client_id}의 MiniMax 연결이 없음 - 재연결 시도")
            if not await self.connect_to_minimax(client_id):
                return False

        minimax_ws = self.minimax_connections.get(client_id)
        if not minimax_ws:
            return False

        try:
            # 연결 상태 재확인
            try:
                if minimax_ws.state.name != 'OPEN':
                    logger.warning(f"{client_id}의 MiniMax 연결이 닫혀있음")
                    del self.minimax_connections[client_id]
                    return False
            except AttributeError:
                # 연결 상태 확인 방법 2
                if hasattr(minimax_ws, 'open') and not minimax_ws.open:
                    logger.warning(f"{client_id}의 MiniMax 연결이 닫혀있음")
                    del self.minimax_connections[client_id]
                    return False
                
            message_str = json.dumps(message)
            await minimax_ws.send(message_str)
            logger.info(f"{client_id}에 대해 MiniMax로 메시지 전송: {message.get('type', 'unknown')}")
            logger.debug(f"{client_id} MiniMax 전송 내용: {message_str}")
            return True
        except websockets.exceptions.ConnectionClosed:
            logger.warning(f"{client_id}의 MiniMax 연결이 닫혀있음")
            if client_id in self.minimax_connections:
                del self.minimax_connections[client_id]
            # WebSocket이 연결되어 있는 경우에만 상태 메시지 전송
            if client_id in self.active_connections:
                await self.send_personal_message({
                    "type": "connection_status",
                    "connected": False,
                    "message": "MiniMax 연결이 끊어졌습니다"
                }, client_id)
            return False
        except Exception as e:
            logger.error(f"{client_id}의 MiniMax 메시지 전송 실패: {e}")
            # WebSocket이 연결되어 있는 경우에만 오류 메시지 전송
            if client_id in self.active_connections:
                await self.send_personal_message({
                    "type": "error",
                    "message": f"MiniMax로 메시지 전송 실패: {str(e)}"
                }, client_id)
            return False

manager = ConnectionManager()

@router.websocket("/realtime-chat")
async def websocket_endpoint(websocket: WebSocket, client_id: str = "default"):
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # 클라이언트 메시지 수신
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "connect_minimax":
                    # MiniMax 연결 생성
                    model = message.get("model", settings.minimax_ws_default_model)
                    success = await manager.connect_to_minimax(client_id, model)
                    await manager.send_personal_message({
                        "type": "connection_status",
                        "connected": success,
                        "model": model
                    }, client_id)
                
                elif message_type == "user_message":
                    # 사용자 텍스트 메시지를 MiniMax로 전달
                    user_text = message.get("text", "")
                    logger.info(f"{client_id}: 사용자 메시지 수신: {user_text}")
                    
                    if user_text:
                        # MiniMax API 형식에 맞게 메시지 구성 (status 필드 추가)
                        minimax_message = {
                            "type": "conversation.item.create",
                            "item": {
                                "type": "message",
                                "role": "user",
                                "status": "completed",
                                "content": [
                                    {
                                        "type": "input_text",
                                        "text": user_text
                                    }
                                ]
                            }
                        }
                        logger.info(f"{client_id}: MiniMax로 사용자 메시지 전송 시도")
                        success = await manager.send_to_minimax(client_id, minimax_message)
                        
                        if success:
                            logger.info(f"{client_id}: 사용자 메시지 전송 성공")
                            # MiniMax API 규격에 따른 완전한 response.create 요청 (실시간 음성 채팅용 - 텍스트와 음성 모두 포함)
                            response_message = {
                                "event_id": f"event_{client_id}_{int(time.time())}",
                                "type": "response.create",
                                "response": {
                                    "modalities": ["text", "audio"],  # 실시간 음성 채팅을 위해 음성도 포함
                                    "instructions": "Please respond in Korean. Be helpful and conversational. This is a real-time voice chat, so provide natural, friendly responses.",
                                    "voice": "male-qn-qingse",
                                    "output_audio_format": "pcm16",
                                    "temperature": 0.7,
                                    "max_response_output_tokens": "4000",
                                    "status": "incomplete"
                                }
                            }
                            await manager.send_to_minimax(client_id, response_message)
                            logger.info(f"{client_id}: 완전한 응답 생성 요청 전송 완료")
                        else:
                            logger.error(f"{client_id}: 사용자 메시지 전송 실패")
                            await manager.send_personal_message({
                                "type": "error",
                                "message": "메시지 전송에 실패했습니다. 다시 시도해주세요."
                            }, client_id)
                    else:
                        logger.warning(f"{client_id}: 빈 메시지 수신")
                        await manager.send_personal_message({
                            "type": "error",
                            "message": "빈 메시지는 전송할 수 없습니다"
                        }, client_id)
                        
                elif message_type == "audio_message":
                    # 사용자 음성 메시지를 MiniMax로 전달 (PCM16 형식)
                    audio_data = message.get("audio_data", "")
                    audio_format = message.get("format", "pcm16")
                    sample_rate = message.get("sample_rate", 24000)
                    channels = message.get("channels", 1)
                    
                    logger.info(f"{client_id}: 사용자 음성 메시지 수신 - 형식: {audio_format}, 샘플레이트: {sample_rate}Hz, 채널: {channels}")
                    
                    if audio_data:
                        # MiniMax API 형식에 맞게 음성 메시지 구성 (PCM16, 24kHz, 모노)
                        minimax_message = {
                            "type": "conversation.item.create",
                            "item": {
                                "type": "message",
                                "role": "user",
                                "status": "completed",
                                "content": [
                                    {
                                        "type": "input_audio",
                                        "audio": audio_data  # Base64 인코딩된 PCM16 음성 데이터
                                    }
                                ]
                            }
                        }
                        logger.info(f"{client_id}: MiniMax로 PCM16 음성 메시지 전송 시도")
                        success = await manager.send_to_minimax(client_id, minimax_message)
                        
                        if success:
                            logger.info(f"{client_id}: 사용자 음성 메시지 전송 성공")
                            # MiniMax API 규격에 따른 음성 응답 생성 요청 (음성 + 텍스트)
                            response_message = {
                                "event_id": f"audio_event_{client_id}_{int(time.time())}",
                                "type": "response.create",
                                "response": {
                                    "modalities": ["text", "audio"],
                                    "instructions": "Please respond in Korean. Be helpful and conversational.",
                                    "voice": "male-qn-qingse",
                                    "output_audio_format": "pcm16",
                                    "temperature": 0.7,
                                    "max_response_output_tokens": "4000",
                                    "status": "incomplete"
                                }
                            }
                            await manager.send_to_minimax(client_id, response_message)
                            logger.info(f"{client_id}: 완전한 음성 응답 생성 요청 전송 완료")
                        else:
                            logger.error(f"{client_id}: 사용자 음성 메시지 전송 실패")
                            await manager.send_personal_message({
                                "type": "error",
                                "message": "음성 메시지 전송에 실패했습니다. 다시 시도해주세요."
                            }, client_id)
                    else:
                        logger.warning(f"{client_id}: 빈 음성 데이터 수신")
                        await manager.send_personal_message({
                            "type": "error",
                            "message": "음성 데이터가 비어있습니다"
                        }, client_id)
                
                elif message_type == "send_to_minimax":
                    # 직접 MiniMax로 메시지 전달 (디버깅/고급 사용)
                    minimax_message = message.get("message", {})
                    await manager.send_to_minimax(client_id, minimax_message)
                
                elif message_type == "disconnect_minimax":
                    # MiniMax 연결 해제
                    await manager.close_minimax_connection(client_id)
                    await manager.send_personal_message({
                        "type": "connection_status",
                        "connected": False
                    }, client_id)
                
                else:
                    # 알 수 없는 메시지 타입
                    await manager.send_personal_message({
                        "type": "error",
                        "message": f"알 수 없는 메시지 타입: {message_type}"
                    }, client_id)
                    
            except json.JSONDecodeError:
                await manager.send_personal_message({
                    "type": "error",
                    "message": "잘못된 JSON 형식입니다"
                }, client_id)
            except Exception as e:
                logger.error(f"{client_id}의 메시지 처리 중 오류: {e}")
                await manager.send_personal_message({
                    "type": "error",
                    "message": f"메시지 처리 중 오류: {str(e)}"
                }, client_id)

    except WebSocketDisconnect:
        logger.info(f"{client_id}의 WebSocket 정상 연결 해제")
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"{client_id}의 WebSocket 오류: {e}")
        # 연결 오류 시 정리
        try:
            manager.disconnect(client_id)
        except Exception as cleanup_error:
            logger.error(f"{client_id} 정리 중 오류: {cleanup_error}")

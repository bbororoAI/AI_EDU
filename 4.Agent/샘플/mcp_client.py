import asyncio
import json
import subprocess
import sys
from typing import Dict, List, Any, Optional
import aiohttp
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPClient:
    """MCP (Model Context Protocol) 클라이언트"""
    
    def __init__(self, config_path: str = "mcp_config.json"):
        self.config_path = config_path
        self.servers = {}
        self.processes = {}
        self.load_config()
    
    def load_config(self):
        """MCP 서버 설정 로드"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.servers = config.get('mcpServers', {})
                logger.info(f"MCP 설정 로드 완료: {len(self.servers)}개 서버")
        except Exception as e:
            logger.error(f"설정 파일 로드 실패: {e}")
            self.servers = {}
    
    async def start_server(self, server_name: str) -> bool:
        """MCP 서버 시작"""
        if server_name not in self.servers:
            logger.error(f"서버 '{server_name}' 설정을 찾을 수 없습니다")
            return False
        
        try:
            server_config = self.servers[server_name]
            command = server_config['command']
            args = server_config['args']
            
            # Windows 환경에서 올바른 명령어 구성
            if command == "cmd":
                # cmd /c npx ... 형태로 실행
                full_command = [command] + args
            else:
                # npx ... 형태로 직접 실행
                full_command = [command] + args
            
            logger.info(f"서버 '{server_name}' 실행 명령어: {' '.join(full_command)}")
            
            # 서버 프로세스 시작
            process = await asyncio.create_subprocess_exec(
                *full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE,
                text=True
            )
            
            # 서버가 정상적으로 시작되었는지 확인
            await asyncio.sleep(2)  # 서버 초기화 대기
            
            if process.returncode is not None:
                # 프로세스가 즉시 종료된 경우
                stderr_output = await process.stderr.read()
                logger.error(f"서버 '{server_name}' 즉시 종료됨. 오류: {stderr_output}")
                return False
            
            self.processes[server_name] = process
            logger.info(f"MCP 서버 '{server_name}' 시작됨 (PID: {process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"서버 '{server_name}' 시작 실패: {e}")
            return False
    
    async def stop_server(self, server_name: str):
        """MCP 서버 중지"""
        if server_name in self.processes:
            process = self.processes[server_name]
            process.terminate()
            await process.wait()
            del self.processes[server_name]
            logger.info(f"MCP 서버 '{server_name}' 중지됨")
    
    async def send_request(self, server_name: str, method: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """MCP 서버에 요청 전송"""
        if server_name not in self.processes:
            logger.error(f"서버 '{server_name}'가 실행되지 않았습니다")
            return None
        
        try:
            process = self.processes[server_name]
            
            # MCP 초기화 요청
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "roots": {
                            "listChanged": True
                        },
                        "sampling": {}
                    },
                    "clientInfo": {
                        "name": "streamlit-search-agent",
                        "version": "1.0.0"
                    }
                }
            }
            
            # 초기화 요청 전송
            init_json = json.dumps(init_request) + "\n"
            process.stdin.write(init_json.encode())
            await process.stdin.drain()
            
            # 초기화 응답 읽기
            init_response = await process.stdout.readline()
            if init_response:
                init_result = json.loads(init_response.decode().strip())
                logger.info(f"서버 '{server_name}' 초기화 완료")
            
            # 실제 요청 전송
            request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": method,
                "params": params or {}
            }
            
            request_json = json.dumps(request) + "\n"
            process.stdin.write(request_json.encode())
            await process.stdin.drain()
            
            # 응답 읽기
            response_line = await process.stdout.readline()
            if response_line:
                response = json.loads(response_line.decode().strip())
                return response
            
        except Exception as e:
            logger.error(f"서버 '{server_name}' 요청 실패: {e}")
            return None
        
        return None
    
    async def search_web(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """DuckDuckGo를 통한 웹 검색"""
        try:
            response = await self.send_request(
                "ddg_search",
                "search",
                {"query": query, "max_results": max_results}
            )
            
            if response and "result" in response:
                return response["result"]
            else:
                logger.warning("웹 검색 결과가 없습니다")
                return []
                
        except Exception as e:
            logger.error(f"웹 검색 실패: {e}")
            return []
    
    async def search_docs(self, query: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """Context7를 통한 기술 문서 검색"""
        try:
            response = await self.send_request(
                "context7-mcp",
                "search",
                {"query": query, "max_results": max_results}
            )
            
            if response and "result" in response:
                return response["result"]
            else:
                logger.warning("문서 검색 결과가 없습니다")
                return []
                
        except Exception as e:
            logger.error(f"문서 검색 실패: {e}")
            return []
    
    async def cleanup(self):
        """모든 서버 정리"""
        for server_name in list(self.processes.keys()):
            await self.stop_server(server_name)

# 전역 MCP 클라이언트 인스턴스
mcp_client = MCPClient()

import asyncio
import json
import subprocess
import sys
from typing import Dict, List, Any, Optional
import logging
import aiohttp

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleMCPClient:
    """간소화된 MCP 클라이언트 - 실제 HTTP API 사용"""
    
    def __init__(self):
        self.web_search_url = "https://api.duckduckgo.com/"
        self.context7_url = "https://context7.upstash.io/"
        self.api_key = "본인 key 입력"
    
    async def search_web_direct(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """DuckDuckGo 직접 API 호출"""
        try:
            # DuckDuckGo Instant Answer API 사용
            params = {
                'q': query,
                'format': 'json',
                'no_html': '1',
                'skip_disambig': '1'
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(self.web_search_url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        results = []
                        
                        # Abstract (요약) 정보
                        if data.get('Abstract'):
                            results.append({
                                'title': data.get('Heading', 'DuckDuckGo 요약'),
                                'url': data.get('AbstractURL', ''),
                                'snippet': data.get('Abstract', ''),
                                'source': 'DuckDuckGo 요약',
                                'rank': 1
                            })
                        
                        # Related Topics (관련 주제)
                        for i, topic in enumerate(data.get('RelatedTopics', [])[:max_results-1], 2):
                            if isinstance(topic, dict) and 'Text' in topic:
                                results.append({
                                    'title': topic.get('Text', '').split(' - ')[0],
                                    'url': topic.get('FirstURL', ''),
                                    'snippet': topic.get('Text', ''),
                                    'source': 'DuckDuckGo 관련 주제',
                                    'rank': i
                                })
                        
                        # Results (검색 결과)
                        for i, result in enumerate(data.get('Results', [])[:max_results-len(results)], len(results)+1):
                            results.append({
                                'title': result.get('Text', '').split(' - ')[0],
                                'url': result.get('FirstURL', ''),
                                'snippet': result.get('Text', ''),
                                'source': 'DuckDuckGo 검색 결과',
                                'rank': i
                            })
                        
                        logger.info(f"웹 검색 완료: {len(results)}개 결과")
                        return results
                    else:
                        logger.error(f"DuckDuckGo API 오류: {response.status}")
                        # API 오류 시 모의 데이터 반환
                        return self._get_mock_web_results(query, max_results)
                        
        except Exception as e:
            logger.error(f"웹 검색 실패: {e}")
            # 예외 발생 시 모의 데이터 반환
            return self._get_mock_web_results(query, max_results)
    
    def _get_mock_web_results(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """모의 웹 검색 결과 생성"""
        mock_results = [
            {
                'title': f'{query}에 대한 최신 정보',
                'url': f'https://example.com/{query.lower().replace(" ", "-")}',
                'snippet': f'{query}에 대한 상세한 정보와 최신 뉴스를 제공합니다.',
                'source': '웹 검색 (모의 데이터)',
                'rank': 1
            },
            {
                'title': f'{query} 가이드 및 튜토리얼',
                'url': f'https://tutorial.com/{query.lower().replace(" ", "-")}',
                'snippet': f'{query}를 배우고 싶다면 이 가이드를 확인해보세요.',
                'source': '웹 검색 (모의 데이터)',
                'rank': 2
            },
            {
                'title': f'{query} 관련 뉴스 및 업데이트',
                'url': f'https://news.com/{query.lower().replace(" ", "-")}',
                'snippet': f'{query}와 관련된 최신 뉴스와 업데이트를 확인할 수 있습니다.',
                'source': '웹 검색 (모의 데이터)',
                'rank': 3
            }
        ]
        
        return mock_results[:max_results]
    
    async def search_docs_mock(self, query: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """Context7 대신 모의 기술 문서 검색"""
        try:
            # 실제로는 Context7 API를 호출해야 하지만, 
            # 여기서는 모의 데이터를 반환
            mock_docs = [
                {
                    'title': f'Python {query} 가이드',
                    'url': 'https://docs.python.org/3/',
                    'snippet': f'Python에서 {query}를 사용하는 방법에 대한 공식 문서입니다.',
                    'source': 'Python 공식 문서',
                    'rank': 1,
                    'code_snippet': f'# {query} 예제\nimport {query.lower()}\n\n# 사용법\nresult = {query.lower()}.example()',
                    'library': 'Python',
                    'language': 'python'
                },
                {
                    'title': f'JavaScript {query} 튜토리얼',
                    'url': 'https://developer.mozilla.org/',
                    'snippet': f'JavaScript {query}에 대한 MDN 문서입니다.',
                    'source': 'MDN Web Docs',
                    'rank': 2,
                    'code_snippet': f'// {query} 예제\nconst {query.lower()} = () => {{\n  // 구현\n}};',
                    'library': 'JavaScript',
                    'language': 'javascript'
                },
                {
                    'title': f'React {query} Hook',
                    'url': 'https://react.dev/',
                    'snippet': f'React에서 {query}를 사용하는 Hook에 대한 가이드입니다.',
                    'source': 'React 공식 문서',
                    'rank': 3,
                    'code_snippet': f'import {{ {query} }} from \'react\';\n\nfunction Component() {{\n  const {query.lower()} = {query}();\n  return <div>{query}</div>;\n}}',
                    'library': 'React',
                    'language': 'javascript'
                }
            ]
            
            # 쿼리와 관련된 결과만 필터링
            filtered_docs = []
            query_lower = query.lower()
            
            for doc in mock_docs:
                if any(term in doc['title'].lower() or term in doc['snippet'].lower() 
                      for term in query_lower.split()):
                    filtered_docs.append(doc)
            
            # 결과가 없으면 기본 결과 반환
            if not filtered_docs:
                filtered_docs = mock_docs[:max_results]
            
            logger.info(f"기술 문서 검색 완료: {len(filtered_docs)}개 결과")
            return filtered_docs[:max_results]
            
        except Exception as e:
            logger.error(f"기술 문서 검색 실패: {e}")
            return []
    
    async def search_web_with_requests(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """requests 라이브러리를 사용한 웹 검색 (대안)"""
        try:
            import requests
            
            # DuckDuckGo Instant Answer API
            params = {
                'q': query,
                'format': 'json',
                'no_html': '1',
                'skip_disambig': '1'
            }
            
            response = requests.get(self.web_search_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                results = []
                
                # Abstract
                if data.get('Abstract'):
                    results.append({
                        'title': data.get('Heading', 'DuckDuckGo 요약'),
                        'url': data.get('AbstractURL', ''),
                        'snippet': data.get('Abstract', ''),
                        'source': 'DuckDuckGo 요약',
                        'rank': 1
                    })
                
                # Related Topics
                for i, topic in enumerate(data.get('RelatedTopics', [])[:max_results-1], 2):
                    if isinstance(topic, dict) and 'Text' in topic:
                        results.append({
                            'title': topic.get('Text', '').split(' - ')[0],
                            'url': topic.get('FirstURL', ''),
                            'snippet': topic.get('Text', ''),
                            'source': 'DuckDuckGo 관련 주제',
                            'rank': i
                        })
                
                logger.info(f"웹 검색 완료: {len(results)}개 결과")
                return results
            else:
                logger.error(f"DuckDuckGo API 오류: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"웹 검색 실패: {e}")
            return []

# 전역 클라이언트 인스턴스
simple_mcp_client = SimpleMCPClient()

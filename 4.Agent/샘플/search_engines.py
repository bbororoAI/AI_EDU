import asyncio
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from mcp_client_simple import simple_mcp_client

logger = logging.getLogger(__name__)

class WebSearchEngine:
    """DuckDuckGo 웹 검색 엔진"""
    
    def __init__(self):
        self.name = "DuckDuckGo"
        self.max_results = 10
    
    async def search(self, query: str, max_results: int = None) -> List[Dict[str, Any]]:
        """웹 검색 수행"""
        try:
            results = await simple_mcp_client.search_web_direct(
                query, 
                max_results or self.max_results
            )
            
            # 결과 포맷팅
            formatted_results = []
            for i, result in enumerate(results, 1):
                formatted_result = {
                    'rank': i,
                    'title': result.get('title', '제목 없음'),
                    'url': result.get('url', ''),
                    'snippet': result.get('snippet', '요약 없음'),
                    'source': '웹 검색',
                    'timestamp': datetime.now().isoformat(),
                    'relevance_score': self._calculate_relevance(query, result)
                }
                formatted_results.append(formatted_result)
            
            logger.info(f"웹 검색 완료: {len(formatted_results)}개 결과")
            return formatted_results
            
        except Exception as e:
            logger.error(f"웹 검색 실패: {e}")
            return []
    
    def _calculate_relevance(self, query: str, result: Dict[str, Any]) -> float:
        """관련도 점수 계산"""
        title = result.get('title', '').lower()
        snippet = result.get('snippet', '').lower()
        query_terms = query.lower().split()
        
        score = 0.0
        for term in query_terms:
            if term in title:
                score += 0.5
            if term in snippet:
                score += 0.3
        
        return min(score, 1.0)

class TechDocSearchEngine:
    """Context7 기술 문서 검색 엔진"""
    
    def __init__(self):
        self.name = "Context7"
        self.max_results = 100
    
    async def search(self, query: str, max_results: int = None) -> List[Dict[str, Any]]:
        """기술 문서 검색 수행"""
        try:
            results = await simple_mcp_client.search_docs_mock(
                query, 
                max_results or self.max_results
            )
            
            # 결과 포맷팅
            formatted_results = []
            for i, result in enumerate(results, 1):
                formatted_result = {
                    'rank': i,
                    'title': result.get('title', '제목 없음'),
                    'url': result.get('url', ''),
                    'snippet': result.get('content', '내용 없음'),
                    'source': '기술 문서',
                    'timestamp': datetime.now().isoformat(),
                    'relevance_score': self._calculate_relevance(query, result),
                    'code_snippet': result.get('code', ''),
                    'library': result.get('library', ''),
                    'language': result.get('language', '')
                }
                formatted_results.append(formatted_result)
            
            logger.info(f"기술 문서 검색 완료: {len(formatted_results)}개 결과")
            return formatted_results
            
        except Exception as e:
            logger.error(f"기술 문서 검색 실패: {e}")
            return []
    
    def _calculate_relevance(self, query: str, result: Dict[str, Any]) -> float:
        """관련도 점수 계산"""
        title = result.get('title', '').lower()
        content = result.get('content', '').lower()
        code = result.get('code', '').lower()
        query_terms = query.lower().split()
        
        score = 0.0
        for term in query_terms:
            if term in title:
                score += 0.4
            if term in content:
                score += 0.3
            if term in code:
                score += 0.3
        
        return min(score, 1.0)

class SearchAggregator:
    """통합 검색 시스템"""
    
    def __init__(self):
        self.web_engine = WebSearchEngine()
        self.doc_engine = TechDocSearchEngine()
    
    async def search_all(self, query: str, web_results: int = 10, doc_results: int = 50) -> Dict[str, List[Dict[str, Any]]]:
        """모든 검색 엔진에서 동시 검색"""
        try:
            # 병렬 검색 실행
            web_task = self.web_engine.search(query, web_results)
            doc_task = self.doc_engine.search(query, doc_results)
            
            web_results, doc_results = await asyncio.gather(
                web_task, doc_task, return_exceptions=True
            )
            
            # 예외 처리
            if isinstance(web_results, Exception):
                logger.error(f"웹 검색 오류: {web_results}")
                web_results = []
            
            if isinstance(doc_results, Exception):
                logger.error(f"문서 검색 오류: {doc_results}")
                doc_results = []
            
            return {
                'web_results': web_results,
                'doc_results': doc_results,
                'total_results': len(web_results) + len(doc_results)
            }
            
        except Exception as e:
            logger.error(f"통합 검색 실패: {e}")
            return {
                'web_results': [],
                'doc_results': [],
                'total_results': 0
            }
    
    async def search_web_only(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """웹 검색만 수행"""
        return await self.web_engine.search(query, max_results)
    
    async def search_docs_only(self, query: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """문서 검색만 수행"""
        return await self.doc_engine.search(query, max_results)

# 전역 검색 어그리게이터 인스턴스
search_aggregator = SearchAggregator()

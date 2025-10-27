import streamlit as st
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any
import logging

# 로컬 모듈 임포트
from mcp_client import mcp_client
from search_engines import search_aggregator

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 페이지 설정
st.set_page_config(
    page_title="종합 정보 검색 AI Agent",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .search-section {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .result-card {
        background-color: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        border-left: 4px solid #1f77b4;
    }
    .web-result {
        border-left-color: #ff7f0e;
    }
    .doc-result {
        border-left-color: #2ca02c;
    }
    .source-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .web-badge {
        background-color: #ff7f0e;
        color: white;
    }
    .doc-badge {
        background-color: #2ca02c;
        color: white;
    }
    .relevance-score {
        font-size: 0.9rem;
        color: #666;
        margin-top: 0.5rem;
    }
    .code-block {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 4px;
        padding: 1rem;
        margin-top: 0.5rem;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

def display_search_results(results: Dict[str, List[Dict[str, Any]]]):
    """검색 결과 표시"""
    
    # 전체 통계
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("총 결과", results['total_results'])
    with col2:
        st.metric("웹 검색", len(results['web_results']))
    with col3:
        st.metric("기술 문서", len(results['doc_results']))
    with col4:
        st.metric("검색 시간", datetime.now().strftime("%H:%M:%S"))
    
    # 탭으로 결과 분리
    tab1, tab2, tab3 = st.tabs(["🌐 웹 검색 결과", "📚 기술 문서", "📊 통합 결과"])
    
    with tab1:
        display_web_results(results['web_results'])
    
    with tab2:
        display_doc_results(results['doc_results'])
    
    with tab3:
        display_combined_results(results)

def display_web_results(web_results: List[Dict[str, Any]]):
    """웹 검색 결과 표시"""
    if not web_results:
        st.info("웹 검색 결과가 없습니다.")
        return
    
    for result in web_results:
        with st.container():
            st.markdown(f"""
            <div class="result-card web-result">
                <div class="source-badge web-badge">웹 검색 #{result['rank']}</div>
                <h4>{result['title']}</h4>
                <p>{result['snippet']}</p>
                <a href="{result['url']}" target="_blank">🔗 링크 열기</a>
                <div class="relevance-score">관련도: {result['relevance_score']:.2f}</div>
            </div>
            """, unsafe_allow_html=True)

def display_doc_results(doc_results: List[Dict[str, Any]]):
    """기술 문서 결과 표시"""
    if not doc_results:
        st.info("기술 문서 검색 결과가 없습니다.")
        return
    
    for result in doc_results:
        with st.container():
            # 라이브러리 정보
            library_info = ""
            if result.get('library'):
                library_info = f"<strong>라이브러리:</strong> {result['library']} | "
            if result.get('language'):
                library_info += f"<strong>언어:</strong> {result['language']}"
            
            # 코드 스니펫
            code_snippet = ""
            if result.get('code_snippet'):
                code_snippet = f"""
                <div class="code-block">
                    <strong>코드 예제:</strong><br>
                    <pre>{result['code_snippet']}</pre>
                </div>
                """
            
            st.markdown(f"""
            <div class="result-card doc-result">
                <div class="source-badge doc-badge">기술 문서 #{result['rank']}</div>
                <h4>{result['title']}</h4>
                <p>{result['snippet']}</p>
                {library_info}
                {code_snippet}
                <a href="{result['url']}" target="_blank">🔗 문서 보기</a>
                <div class="relevance-score">관련도: {result['relevance_score']:.2f}</div>
            </div>
            """, unsafe_allow_html=True)

def display_combined_results(results: Dict[str, List[Dict[str, Any]]]):
    """통합 결과 표시 (관련도 순으로 정렬)"""
    all_results = []
    
    # 웹 결과 추가
    for result in results['web_results']:
        result['type'] = 'web'
        all_results.append(result)
    
    # 문서 결과 추가
    for result in results['doc_results']:
        result['type'] = 'doc'
        all_results.append(result)
    
    # 관련도 순으로 정렬
    all_results.sort(key=lambda x: x['relevance_score'], reverse=True)
    
    if not all_results:
        st.info("검색 결과가 없습니다.")
        return
    
    st.subheader(f"관련도 순 정렬 ({len(all_results)}개 결과)")
    
    for i, result in enumerate(all_results, 1):
        result_type = "웹 검색" if result['type'] == 'web' else "기술 문서"
        badge_class = "web-badge" if result['type'] == 'web' else "doc-badge"
        
        with st.container():
            st.markdown(f"""
            <div class="result-card">
                <div class="source-badge {badge_class}">{result_type} #{i}</div>
                <h4>{result['title']}</h4>
                <p>{result['snippet']}</p>
                <a href="{result['url']}" target="_blank">🔗 링크 열기</a>
                <div class="relevance-score">관련도: {result['relevance_score']:.2f}</div>
            </div>
            """, unsafe_allow_html=True)

async def perform_search(query: str, search_type: str, max_web: int, max_docs: int):
    """검색 수행"""
    try:
        if search_type == "전체 검색":
            return await search_aggregator.search_all(query, max_web, max_docs)
        elif search_type == "웹 검색만":
            web_results = await search_aggregator.search_web_only(query, max_web)
            return {
                'web_results': web_results,
                'doc_results': [],
                'total_results': len(web_results)
            }
        elif search_type == "기술 문서만":
            doc_results = await search_aggregator.search_docs_only(query, max_docs)
            return {
                'web_results': [],
                'doc_results': doc_results,
                'total_results': len(doc_results)
            }
    except Exception as e:
        st.error(f"검색 중 오류가 발생했습니다: {e}")
        return {
            'web_results': [],
            'doc_results': [],
            'total_results': 0
        }

def main():
    """메인 애플리케이션"""
    
    # 헤더
    st.markdown('<h1 class="main-header">🔍 종합 정보 검색 AI Agent</h1>', unsafe_allow_html=True)
    st.markdown("**DuckDuckGo + Context7 + MCP를 활용한 지능형 검색 시스템**")
    
    # 사이드바 설정
    with st.sidebar:
        st.header("⚙️ 검색 설정")
        
        search_type = st.selectbox(
            "검색 유형",
            ["전체 검색", "웹 검색만", "기술 문서만"],
            help="검색할 소스를 선택하세요"
        )
        
        max_web = st.slider(
            "웹 검색 결과 수",
            min_value=1,
            max_value=20,
            value=10,
            help="DuckDuckGo에서 가져올 최대 결과 수"
        )
        
        max_docs = st.slider(
            "기술 문서 결과 수",
            min_value=1,
            max_value=100,
            value=50,
            help="Context7에서 가져올 최대 결과 수"
        )
        
        st.markdown("---")
        st.markdown("### 📊 시스템 상태")
        
        # 검색 엔진 상태 확인
        st.success("✅ 검색 엔진 준비 완료")
        st.info("🌐 DuckDuckGo 웹 검색")
        st.info("📚 기술 문서 검색")
    
    # 메인 검색 인터페이스
    with st.container():
        st.markdown('<div class="search-section">', unsafe_allow_html=True)
        
        # 검색 입력
        query = st.text_input(
            "🔍 검색어를 입력하세요",
            placeholder="예: Python 비동기 프로그래밍, React hooks, 머신러닝 알고리즘...",
            help="웹 검색과 기술 문서를 동시에 검색합니다"
        )
        
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            search_button = st.button("🔍 검색", type="primary", use_container_width=True)
        with col2:
            clear_button = st.button("🗑️ 초기화", use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 검색 실행
    if search_button and query:
        with st.spinner("검색 중... 잠시만 기다려주세요."):
            # 비동기 검색 실행
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                results = loop.run_until_complete(
                    perform_search(query, search_type, max_web, max_docs)
                )
                
                # 결과 표시
                st.markdown("---")
                st.subheader(f"📋 '{query}' 검색 결과")
                display_search_results(results)
                
            except Exception as e:
                st.error(f"검색 중 오류가 발생했습니다: {e}")
            finally:
                loop.close()
    
    elif clear_button:
        st.rerun()
    
    # 푸터
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        <p>🔍 종합 정보 검색 AI Agent | DuckDuckGo + Context7 + MCP</p>
        <p>실시간 웹 검색과 기술 문서 검색을 통한 종합적인 정보 제공</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    # 애플리케이션 실행
    main()

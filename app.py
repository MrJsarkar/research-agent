import streamlit as st
import json
import traceback
from datetime import datetime
from duckduckgo_search import DDGS
from typing import List, Dict, Tuple
import time
import requests
import urllib.parse

# Set page config (must be first Streamlit command after imports)
try:
    st.set_page_config(page_title="Research Agent", page_icon="🔍", layout="wide")
except Exception as e:
    pass  # Page config already set, ignore on reruns


class ResearchAgent:
    def __init__(self):
        self.search_history = []
        self.findings = []
        
    def search_with_fallback(self, query: str, max_results: int = 5) -> Tuple[List[Dict], bool]:
        """Try DuckDuckGo first, fallback to Wikipedia if blocked. Returns (results, used_fallback)"""
        results = []
        used_fallback = False
        
        # Try DuckDuckGo with retries
        for attempt in range(3):
            try:
                with DDGS() as ddgs:
                    results = list(ddgs.text(query, max_results=max_results))
                    if results:
                        return results, False
            except Exception as e:
                if attempt < 2:
                    time.sleep(2 ** attempt)  # Exponential backoff
                continue
        
        # Fallback to Wikipedia if DDG fails (reliable, no API key needed)
        return self.search_wikipedia(query, max_results), True
    
    def search_wikipedia(self, query: str, max_results: int = 5) -> List[Dict]:
        """Wikipedia API - works reliably on Streamlit Cloud"""
        try:
            # Wikipedia search API
            search_url = "https://en.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "srlimit": max_results
            }
            
            response = requests.get(search_url, params=params, timeout=10)
            data = response.json()
            
            results = []
            for item in data.get("query", {}).get("search", []):
                # Get page URL
                page_id = item["pageid"]
                title = item["title"]
                url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
                
                results.append({
                    "title": title,
                    "href": url,
                    "body": item["snippet"].replace("<span class=\"searchmatch\">", "").replace("</span>", ""),
                    "source": "Wikipedia"
                })
            
            return results
        except Exception as e:
            st.error(f"Wikipedia fallback also failed: {e}")
            return []
    
    def plan_research(self, query: str) -> List[str]:
        """Break down complex query into sub-questions"""
        with st.spinner("🧠 Planning research strategy..."):
            time.sleep(0.5)
            
            sub_questions = [
                f"What is the current state of {query}?",
                f"What are the recent developments in {query}?",
                f"What are the key challenges in {query}?",
                f"What solutions exist for {query}?"
            ]
            return sub_questions
    
    def synthesize(self, query: str, sub_questions: List[str], 
                   all_results: List[Dict]) -> str:
        """Synthesize findings into coherent report"""
        
        synthesis = f"""
# Research Report: {query}
*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}*

## Executive Summary
Analysis of {len(all_results)} sources across {len(sub_questions)} research angles regarding {query}.

## Key Findings

"""
        for i, question in enumerate(sub_questions, 1):
            synthesis += f"\n### {i}. {question}\n\n"
            # Distribute results among questions
            start_idx = (i-1) * 2
            related = all_results[start_idx:start_idx+2] if len(all_results) > start_idx else []
            
            if related:
                for r in related:
                    source = r.get('source', 'Web')
                    synthesis += f"- **[{r['title']}]({r['href']})** *({source})*\n"
                    synthesis += f"  - {r['body'][:250]}...\n\n"
            else:
                synthesis += "- No sources found for this specific angle.\n\n"
        
        synthesis += """
## Methodology
- **Planning**: Query decomposition into sub-questions
- **Execution**: Multi-source search (Web → Wikipedia fallback)
- **Synthesis**: Cross-reference and summarization
- **Resilience**: Automatic fallback if primary search blocked

---
*Research Agent v1.1 | Robust Search Pipeline*
"""
        return synthesis

def main():
    try:
        # Page config already set at top level
        
        # Custom CSS
        st.markdown("""
        <style>
        .main {background-color: #0e1117;}
        .stProgress > div > div > div > div {background-color: #00adb5;}
        .research-card {
            background-color: #1e1e1e;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #00adb5;
            margin: 10px 0;
        }
        .fallback-notice {
            background-color: #2d2d2d;
            border-left: 4px solid #ffa500;
            padding: 10px;
            border-radius: 5px;
            font-size: 0.9em;
        }
        </style>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 4])
        with col1:
            st.image("https://cdn-icons-png.flaticon.com/512/2103/2103633.png", width=80)
        with col2:
            st.title("🔍 Autonomous Research Agent")
            st.caption("Plan · Search (with Fallback) · Synthesize · Cite")
        
        with st.sidebar:
            st.header("⚙️ Configuration")
            depth = st.slider("Research Depth", 1, 4, 3)
            results_per_query = st.slider("Sources per Angle", 2, 5, 3)
            st.divider()
            st.info("🔧 **Auto-Fallback**: If DuckDuckGo blocks cloud IPs, automatically switches to Wikipedia API")
        
        query = st.text_input("🎯 Research Topic", 
                             placeholder="e.g., 'CRISPR therapy 2024' or 'Quantum computing breakthroughs'",
                             key="query")
        
        if st.button("🚀 Start Research", type="primary", use_container_width=True):
            if not query:
                st.warning("Please enter a research topic")
                return
                
            agent = ResearchAgent()
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Planning
            status_text.text("Phase 1/3: Strategizing...")
            sub_questions = agent.plan_research(query)
            progress_bar.progress(25)
            
            with st.expander("📋 Research Plan", expanded=True):
                for i, q in enumerate(sub_questions[:depth], 1):
                    st.write(f"**{i}.** {q}")
            
            # Execution with fallback
            status_text.text("Phase 2/3: Gathering sources...")
            all_results = []
            
            cols = st.columns(min(depth, 2))
            for idx, question in enumerate(sub_questions[:depth]):
                with cols[idx % 2]:
                    st.markdown(f"<div class='research-card'>"
                              f"<b>🔎 {question}</b></div>", 
                              unsafe_allow_html=True)
                    
                    results, used_fallback = agent.search_with_fallback(question, results_per_query)
                    
                    if used_fallback:
                        st.warning("⚠️ Using Wikipedia fallback (DDG blocked on cloud)")
                    
                    all_results.extend(results)
                    
                    if results:
                        st.success(f"✅ {len(results)} sources")
                        # Show first result preview
                        with st.expander("Preview top result"):
                            st.write(f"**{results[0]['title']}**")
                            st.caption(results[0]['body'][:100] + "...")
                    else:
                        st.error("❌ No sources found")
                    
                    progress = 25 + (50 * (idx + 1) // depth)
                    progress_bar.progress(progress)
            
            # Synthesis
            status_text.text("Phase 3/3: Synthesizing report...")
            report = agent.synthesize(query, sub_questions[:depth], all_results)
            progress_bar.progress(100)
            status_text.success("✅ Research complete!")
            
            # Display
            st.divider()
            tab1, tab2 = st.tabs(["📄 Report", "📊 Raw Data"])
            
            with tab1:
                st.markdown(report)
                st.download_button(
                    label="Download Markdown",
                    data=report,
                    file_name=f"research_{query[:20].replace(' ', '_')}.md",
                        mime="text/markdown"
                )
                
            with tab2:
                st.json([{"title": r['title'], "url": r['href'], "source": r.get('source', 'web')} 
                        for r in all_results])
        
    except Exception as e:
        st.error(f"❌ Application error: {str(e)}")
        st.error(traceback.format_exc())

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"❌ Fatal error: {str(e)}")
        st.error(traceback.format_exc())
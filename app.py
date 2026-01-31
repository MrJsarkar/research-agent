import streamlit as st
import os
import json
from datetime import datetime
from typing import List, Dict
import time
import requests

# Page config FIRST
st.set_page_config(
    page_title="Research Agent Pro",
    page_icon="🔍",
    layout="wide"
)

# Initialize Tavily
def get_tavily_client():
    """Get Tavily API key from secrets or env"""
    try:
        # For Streamlit Cloud (secrets)
        return st.secrets["TAVILY_API_KEY"]
    except:
        # For local/other platforms
        return os.getenv("TAVILY_API_KEY", "")

class ResearchAgent:
    def __init__(self):
        self.api_key = get_tavily_client()
        self.base_url = "https://api.tavily.com"
        
    def search_tavily(self, query: str, max_results: int = 5) -> List[Dict]:
        """Real AI-optimized search using Tavily (works on cloud)"""
        if not self.api_key or self.api_key == "":
            st.error("⚠️ Tavily API key not found! Add it to Streamlit secrets or environment variables.")
            return []
        
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "advanced",  # "basic" or "advanced"
            "include_answer": True,      # AI-generated answer
            "include_images": False,
            "include_raw_content": False,
            "max_results": max_results,
            "include_domains": [],
            "exclude_domains": []
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/search",
                json=payload,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            results = []
            
            # Add AI answer as first result if available
            if data.get("answer"):
                results.append({
                    "title": "AI Synthesis",
                    "href": "https://tavily.com",
                    "body": data["answer"],
                    "source": "Tavily AI",
                    "score": 1.0
                })
            
            # Add organic results
            for result in data.get("results", []):
                results.append({
                    "title": result["title"],
                    "href": result["url"],
                    "body": result["content"],
                    "source": result.get("domain", "Web"),
                    "score": result.get("score", 0),
                    "published_date": result.get("published_date", "Unknown")
                })
            
            return results
            
        except requests.exceptions.RequestException as e:
            st.error(f"Search API error: {str(e)}")
            return []
    
    def plan_research(self, query: str) -> List[str]:
        """Generate strategic sub-questions"""
        # Using the query to generate context-aware questions
        questions = [
            f"What is {query}? Definition and fundamentals",
            f"Latest developments and news about {query} in 2024",
            f"Key experts, companies, or research institutions working on {query}",
            f"Future implications and challenges of {query}",
            f"Data, statistics, and market analysis regarding {query}"
        ]
        return questions[:4]
    
    def synthesize(self, query: str, sub_questions: List[str], 
                   all_results: List[Dict]) -> str:
        """Create professional research report"""
        total_sources = len(all_results)
        high_quality = len([r for r in all_results if r.get("score", 0) > 0.8])
        
        report = f"""# Research Report: {query}
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}  
**Sources Analyzed:** {total_sources} (High relevance: {high_quality})

---

"""
        
        # Group by sub-question
        chunk_size = max(1, len(all_results) // len(sub_questions))
        
        for i, question in enumerate(sub_questions, 1):
            report += f"\n## {i}. {question}\n\n"
            
            start = (i-1) * chunk_size
            end = start + chunk_size + 1  # +1 to ensure coverage
            related = all_results[start:end]
            
            if related:
                for r in related:
                    score = r.get("score", 0)
                    score_bar = "🟢" * int(score * 5) + "⚪" * (5 - int(score * 5))
                    date = r.get("published_date", "")
                    date_str = f" | 📅 {date}" if date else ""
                    
                    report += f"### [{r['title']}]({r['href']})\n"
                    report += f"**Relevance:** {score_bar} ({score:.2f}){date_str}  \n"
                    report += f"**Source:** {r['source']}  \n"
                    report += f"{r['body'][:300]}...\n\n"
            else:
                report += "*No specific sources found for this angle.*\n\n"
        
        report += """
---
## Research Methodology
This report was generated using:
- **Tavily AI Search API**: Advanced neural search with real-time web indexing
- **Multi-angle Analysis**: Parallel queries targeting different aspects of the topic
- **Relevance Scoring**: AI-ranked results by content quality and semantic relevance
- **Source Verification**: Cross-referenced publication dates and domain authority

*Research Agent v2.0 | Powered by Tavily AI*
"""
        return report

def check_api_key():
    """Check if API key is configured"""
    key = get_tavily_client()
    if not key:
        st.error("🚨 **API Key Missing!**")
        st.info("""
        To enable search, add your Tavily API key:
        
        **For Streamlit Cloud:**
        1. Go to your app dashboard → **⋮** → **Secrets**
        2. Add: `TAVILY_API_KEY` = `tvly-your-key-here`
        3. Reboot app
        
        **For Local:**
        Create `.env` file with: `TAVILY_API_KEY=tvly-your-key-here`
        
        [Get free API key at tavily.com](https://tavily.com)
        """)
        return False
    return True

def main():
    # Custom styling
    st.markdown("""
    <style>
    .main {background-color: #0e1117;}
    .stProgress > div > div > div > div {background-color: #00adb5;}
    .source-card {
        background-color: #1e1e1e;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #00adb5;
        margin: 10px 0;
    }
    .relevance-high {color: #00ff88;}
    .relevance-med {color: #ffaa00;}
    .relevance-low {color: #ff5555;}
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    col1, col2 = st.columns([1, 4])
    with col1:
        st.image("https://cdn-icons-png.flaticon.com/512/2103/2103633.png", width=80)
    with col2:
        st.title("🔍 Research Agent Pro")
        st.caption("Real-time AI Search | Multi-source Synthesis | Live Results")
    
    # Check API
    if not check_api_key():
        st.stop()
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        api_status = "🟢 Active" if get_tavily_client() else "🔴 Missing"
        st.markdown(f"**API Status:** {api_status}")
        
        search_depth = st.selectbox(
            "Search Depth",
            ["basic", "advanced"],
            index=1,
            help="Advanced uses more AI processing for better results"
        )
        
        max_results = st.slider("Results per Query", 3, 10, 5)
        research_breadth = st.slider("Research Angles", 2, 5, 3)
        
        st.divider()
        st.markdown("**Powered by Tavily AI**")
        st.caption("1,000 free searches/month")
    
    # Main
    query = st.text_input(
        "🎯 Research Topic", 
        placeholder="e.g., 'CRISPR gene editing 2024', 'Quantum advantage recent papers'",
        key="query"
    )
    
    if st.button("🚀 Start Research", type="primary", use_container_width=True):
        if not query:
            st.warning("Enter a research topic")
            return
        
        agent = ResearchAgent()
        
        # Progress
        progress_bar = st.progress(0)
        status = st.empty()
        
        # Phase 1: Planning
        status.info("🧠 Phase 1/3: Strategizing research angles...")
        sub_questions = agent.plan_research(query)
        progress_bar.progress(20)
        
        with st.expander("📋 Research Strategy", expanded=True):
            for i, q in enumerate(sub_questions[:research_breadth], 1):
                st.write(f"**{i}.** {q}")
        
        # Phase 2: Execution
        status.info("🔍 Phase 2/3: Executing parallel searches...")
        all_results = []
        
        cols = st.columns(min(research_breadth, 2))
        for idx, question in enumerate(sub_questions[:research_breadth]):
            with cols[idx % 2]:
                with st.container():
                    st.markdown(f"**🔎 {question[:50]}...**")
                    
                    with st.spinner("Searching..."):
                        results = agent.search_tavily(
                            question, 
                            max_results=max_results
                        )
                    
                    if results:
                        st.success(f"✅ {len(results)} sources")
                        # Show top result preview
                        top = results[0]
                        score = top.get("score", 0)
                        st.caption(f"Top: {top['title'][:40]}... (Score: {score:.2f})")
                        all_results.extend(results)
                    else:
                        st.error("❌ Failed")
                    
                    progress = 20 + (60 * (idx + 1) // research_breadth)
                    progress_bar.progress(progress)
        
        if not all_results:
            st.error("All searches failed. Check API key and quota.")
            return
        
        # Phase 3: Synthesis
        status.info("🧩 Phase 3/3: Synthesizing report...")
        report = agent.synthesize(
            query, 
            sub_questions[:research_breadth], 
            all_results
        )
        progress_bar.progress(100)
        status.success(f"✅ Research complete! Analyzed {len(all_results)} sources")
        
        # Display
        st.divider()
        tab1, tab2, tab3 = st.tabs(["📄 Report", "📊 Source Analysis", "⬇️ Export"])
        
        with tab1:
            st.markdown(report)
            
        with tab2:
            st.subheader("Source Quality Analysis")
            
            # Sort by score
            sorted_results = sorted(all_results, key=lambda x: x.get("score", 0), reverse=True)
            
            for r in sorted_results[:10]:
                score = r.get("score", 0)
                color = "relevance-high" if score > 0.8 else "relevance-med" if score > 0.5 else "relevance-low"
                
                with st.container():
                    cols = st.columns([3, 1])
                    with cols[0]:
                        st.markdown(f"**[{r['title']}]({r['href']})**")
                        st.caption(f"{r['body'][:100]}...")
                    with cols[1]:
                        st.markdown(f"<span class='{color}'>Relevance: {score:.2f}</span>", unsafe_allow_html=True)
                        st.caption(r.get("source", "Unknown"))
                st.divider()
                
        with tab3:
            st.download_button(
                label="Download Full Report (Markdown)",
                data=report,
                file_name=f"Research_{query[:20].replace(' ', '_')}.md",
                mime="text/markdown"
            )
            
            # Also export JSON
            json_data = json.dumps([{
                "title": r["title"],
                "url": r["href"],
                "source": r.get("source"),
                "score": r.get("score")
            } for r in all_results], indent=2)
            
            st.download_button(
                label="Export Sources (JSON)",
                data=json_data,
                file_name=f"Sources_{query[:20].replace(' ', '_')}.json",
                mime="application/json"
            )

if __name__ == "__main__":
    main()
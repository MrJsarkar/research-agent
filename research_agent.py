import os
import json
import queue
import threading
import uuid
from datetime import datetime
from typing import List, Dict, Any
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"

# In-memory store: research_id -> {queue, report, status, topic}
_sessions: Dict[str, Dict[str, Any]] = {}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0 Safari/537.36"
    )
}


def create_session(topic: str) -> str:
    research_id = str(uuid.uuid4())
    q: queue.Queue = queue.Queue()
    _sessions[research_id] = {
        "topic": topic,
        "queue": q,
        "report": None,
        "status": "running",
        "sources": [],
    }
    return research_id


def get_session(research_id: str) -> Dict[str, Any] | None:
    return _sessions.get(research_id)


# ─── LLM helpers ────────────────────────────────────────────────────────────

def _llm(system: str, user: str, temperature: float = 0.4) -> str:
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        max_tokens=2048,
    )
    return resp.choices[0].message.content.strip()


def _llm_json(system: str, user: str) -> Any:
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.3,
        max_tokens=2048,
        response_format={"type": "json_object"},
    )
    return json.loads(resp.choices[0].message.content)


# ─── Agent steps ─────────────────────────────────────────────────────────────

def _plan(topic: str) -> List[str]:
    data = _llm_json(
        system=(
            "You are a systematic research strategist. "
            "Output ONLY valid JSON with no extra text."
        ),
        user=(
            f"Research topic: \"{topic}\"\n\n"
            "Break this topic into 4-6 precise, searchable sub-questions that together give "
            "comprehensive coverage. Each question should be answerable from web sources.\n\n"
            "Output JSON exactly: {\"sub_questions\": [\"...\", \"...\"]}"
        ),
    )
    return data.get("sub_questions", [f"What is {topic}?"])


def _search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Fetch DuckDuckGo HTML search results and extract snippets."""
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    results = []
    try:
        with httpx.Client(headers=HEADERS, timeout=15, follow_redirects=True) as http:
            r = http.get(url)
        soup = BeautifulSoup(r.text, "html.parser")
        for result in soup.select(".result__body")[:max_results]:
            title_tag = result.select_one(".result__title")
            snippet_tag = result.select_one(".result__snippet")
            url_tag = result.select_one(".result__url")
            title = title_tag.get_text(strip=True) if title_tag else "—"
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
            link = url_tag.get_text(strip=True) if url_tag else ""
            if snippet:
                results.append({"title": title, "snippet": snippet, "url": link})
    except Exception as e:
        results.append({"title": "Search error", "snippet": str(e), "url": ""})
    return results


def _synthesise(sub_question: str, snippets: List[Dict[str, str]]) -> str:
    snippets_text = "\n".join(
        f"[{i+1}] {s['title']}: {s['snippet']}" for i, s in enumerate(snippets)
    )
    return _llm(
        system=(
            "You are a research analyst. Write clear, concise, evidence-based prose. "
            "Do not invent facts beyond the provided snippets."
        ),
        user=(
            f"Sub-question: {sub_question}\n\n"
            f"Web search snippets:\n{snippets_text}\n\n"
            "Write a focused 3-5 sentence synthesis that directly answers the sub-question "
            "using information from the snippets. Be analytical, not bullet-pointy."
        ),
        temperature=0.5,
    )


def _generate_report(topic: str, findings: List[Dict[str, str]], sources: List[Dict[str, str]]) -> str:
    findings_text = "\n\n".join(
        f"### {f['question']}\n{f['synthesis']}" for f in findings
    )
    system = (
        "You are an expert research writer. Produce professional, structured reports "
        "in clean markdown. Be analytical, precise, and insightful."
    )
    user = (
        f"# Research Topic: {topic}\n\n"
        f"## Findings by Sub-Question\n\n{findings_text}\n\n"
        "Write a full research report in markdown with these sections:\n"
        "1. **Executive Summary** (3-4 sentences)\n"
        "2. **Key Findings** (one section per sub-question, with a clear heading)\n"
        "3. **Synthesis & Implications** (overall analytical conclusion, 2-3 paragraphs)\n"
        "4. **Limitations** (brief note on what the research didn't cover)\n\n"
        "Use markdown formatting throughout. Be thorough and professional."
    )
    return _llm(system, user, temperature=0.6)


# ─── Main agent loop ──────────────────────────────────────────────────────────

def _emit(q: queue.Queue, step_type: str, message: str, data: Any = None):
    q.put({
        "type": step_type,
        "message": message,
        "data": data,
        "timestamp": datetime.now().isoformat(),
    })


def run_research(research_id: str):
    session = _sessions[research_id]
    q = session["queue"]
    topic = session["topic"]
    sources: List[Dict[str, str]] = []

    try:
        # ── Phase 1: Planning ─────────────────────────────────────────────
        _emit(q, "plan", f"🧠 Analysing research topic: **{topic}**")
        sub_questions = _plan(topic)
        _emit(q, "plan", f"📋 Research plan complete — {len(sub_questions)} sub-questions identified.", sub_questions)

        findings = []

        # ── Phase 2: Search & Synthesise ─────────────────────────────────
        for i, question in enumerate(sub_questions, 1):
            _emit(q, "search", f"🔍 [{i}/{len(sub_questions)}] Searching: *{question}*")
            snippets = _search(question)
            for s in snippets:
                if s["url"]:
                    sources.append(s)

            source_count = len([s for s in snippets if s["snippet"]])
            _emit(q, "search", f"📄 Found {source_count} sources for sub-question {i}.", snippets)

            _emit(q, "synthesise", f"⚗️ [{i}/{len(sub_questions)}] Synthesising findings...")
            synthesis = _synthesise(question, snippets)
            _emit(q, "synthesise", f"✅ Synthesis complete for sub-question {i}.", {"question": question, "synthesis": synthesis})

            findings.append({"question": question, "synthesis": synthesis})

        session["sources"] = sources

        # ── Phase 3: Report ───────────────────────────────────────────────
        _emit(q, "report", f"📝 Generating final research report...")
        report_md = _generate_report(topic, findings, sources)
        session["report"] = report_md
        session["status"] = "done"

        _emit(q, "done", "🎉 Research complete! Your report is ready.", {"report": report_md})

    except Exception as e:
        session["status"] = "error"
        _emit(q, "error", f"❌ Agent error: {str(e)}")
    finally:
        q.put(None)  # Sentinel to close SSE stream


def start_research_thread(research_id: str):
    t = threading.Thread(target=run_research, args=(research_id,), daemon=True)
    t.start()

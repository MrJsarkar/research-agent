# Autonomous Research Agent

An AI-powered research agent that takes any question or topic, autonomously plans a multi-dimensional investigation, searches the web, synthesises findings, and delivers a structured research report — streamed live in the browser.

## How It Works

1. **Plan** — Groq LLM (llama-3.3-70b-versatile) breaks the topic into 4-6 targeted sub-questions
2. **Search** — DuckDuckGo HTML search fetches real web results for each sub-question (no API key needed)
3. **Synthesise** — LLM analyses and synthesises each set of search results into a focused finding
4. **Report** — LLM writes a full structured markdown report with Executive Summary, Key Findings, Synthesis, and Limitations
5. **Stream** — Every step is streamed live to the browser via Server-Sent Events (SSE)

## Features

- **Live SSE streaming** — Watch the agent reason in real time, step by step
- **Tabbed output** — Live Stream · Report · Sources
- **Rendered report** — Markdown report with copy and download buttons
- **Document upload** — Drag-and-drop PDF, TXT, or MD to use as research seed
- **Glassmorphism UI** — Premium dark-mode design with ambient animations

## Tech Stack

| Layer    | Technology |
|----------|------------|
| Backend  | FastAPI + Python |
| LLM      | Groq (llama-3.3-70b-versatile) |
| Search   | DuckDuckGo HTML (httpx + BeautifulSoup) |
| Streaming| Server-Sent Events (sse-starlette) |
| Frontend | Vanilla HTML / CSS / JS + marked.js |

## Requirements

- Python 3.10+
- Groq API key (set in `.env`)

## Local Run

```bash
pip install -r requirements.txt
python main.py
```

Then open `http://localhost:8000`

## Environment

```env
GROQ_API_KEY=your_key_here
```

## Deployment

This project includes a `Dockerfile` for deployment to any container platform (Cloud Run, Fly.io, etc.).
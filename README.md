# 🔍 Autonomous Research Agent

An agentic AI application that performs multi-step research: planning, web search, synthesis, and citation.

## Features

- **Agentic Planning**: Breaks complex queries into sub-questions
- **Parallel Search**: Executes multiple search angles simultaneously  
- **Source Synthesis**: Aggregates findings into cited reports
- **Chain-of-Thought**: Visible reasoning process
- **Export**: Markdown generation

## Local Development

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 🚀 Deployment (Streamlit Cloud)

This app is ready for immediate deployment on Streamlit Cloud (Free Tier).

### Steps:
1. **Push to GitHub**:
   - Create a new public repository on GitHub.
   - Push your code:
     ```bash
     git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
     git branch -M main
     git push -u origin main
     ```

2. **Deploy**:
   - Visit [share.streamlit.io](https://share.streamlit.io/).
   - Click **"New app"**.
   - Select your repository (`YOUR_USERNAME/YOUR_REPO`) and branch (`main`).
   - Main file path: `app.py`.
   - Click **"Deploy!"**.

### Notes:
- **API Key Required**: This app uses **Tavily AI Search**. Get a free key at [tavily.com](https://tavily.com).
  - **Local**: Add `TAVILY_API_KEY` to your `.env` file or environment variables.
  - **Streamlit Cloud**: Add `TAVILY_API_KEY` in the app's **Secrets** settings.
# IBU BITLoft Chatbot

Created by the **BITLoft Team**, International Balkan University.

AI assistant for **BIT Loft**, the coworking and learning space at
International Balkan University (IBU). It answers questions from the PDFs in `docs/` using
retrieval-augmented generation (FAISS + fastembed embeddings) and a free Groq LLM.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env          # macOS/Linux: cp .env.example .env
```

Get a free API key at https://console.groq.com/keys and put it in `.env` as `GROQ_API_KEY`.

## Run

Web interface (on Windows you can also just double-click `start-chatbot.bat`):

```bash
python app.py
```

Then open http://localhost:8000. To make it reachable from other devices on the network,
set `HOST=0.0.0.0` before starting.

Terminal version:

```bash
python chatbot.py
```

The first start downloads the embedding model and builds the search index in `faiss_index/`.
The index is rebuilt automatically whenever PDFs in `docs/` are added or changed.

## Deploy for free (Render)

1. Push this project to a GitHub repository you own.
2. Sign up at https://render.com with your GitHub account (the free plan needs no credit card).
3. Click **New → Blueprint**, pick the repository, and Render reads `render.yaml`.
4. When asked, paste your Groq key as `GROQ_API_KEY`, then click **Apply**.

The first build takes a few minutes. The chatbot is then live at `https://<service-name>.onrender.com`.
Free services sleep after 15 minutes without visitors; the next visit wakes them in about a minute.

## Project layout

| Path | Purpose |
| --- | --- |
| `rag.py` | Document loading, search index, prompt and LLM call |
| `app.py` | FastAPI web server (`/api/chat`, `/api/health`) |
| `chatbot.py` | Command-line chat |
| `static/` | Web interface (HTML, CSS, JS) |
| `docs/` | Source PDFs the chatbot answers from |

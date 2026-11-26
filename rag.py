"""Core retrieval-augmented generation logic for the IBU BITLoft chatbot.

Shared by the command-line client (chatbot.py) and the web server (app.py).

Created by the BITLoft Team, International Balkan University.
"""

import hashlib
import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_community.vectorstores import FAISS
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_groq import ChatGroq
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

DOCS_DIR = BASE_DIR / "docs"
INDEX_DIR = BASE_DIR / "faiss_index"
MANIFEST_FILE = INDEX_DIR / "manifest.json"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
TOP_K = 6
MAX_HISTORY_MESSAGES = 6

GROQ_MODEL = os.getenv("GROQ_MODEL") or "openai/gpt-oss-20b"

GREETINGS = {"hi", "hello", "hey", "good morning", "good afternoon", "good evening"}
FAREWELLS = {"bye", "goodbye", "see you", "see ya", "take care", "quit", "exit"}

GREETING_REPLY = (
    "Hello! I'm the BITLoft assistant for International Balkan University. "
    "Ask me about BITLoft, admissions, enrollment documents, university rules or staff."
)
FAREWELL_REPLY = "Goodbye! Have a great day!"

SYSTEM_PROMPT = """You are the BITLoft Assistant, a chatbot for BIT Loft (Balkan Information \
Technologies), the coworking and learning space at \
International Balkan University (IBU) in Skopje, North Macedonia. You also answer general \
questions about IBU using the university documents provided.

Rules:
- Answer using the context below. If the context only partly answers the question, share \
what it does say and note what is missing.
- If the context does not contain the answer, say so plainly and suggest contacting \
bit@ibu.edu.mk or the relevant IBU office. Never invent names, dates, fees or emails.
- You are a chatbot. Never claim to be a staff member, student, or any person in the records.
- If asked who created or built you, say you were created by the BITLoft Team at IBU.
- When listing staff or professors, mention that the list may not be complete.
- Keep answers concise and well structured. Use bullet points for lists.

Context:
{context}"""


def _normalise(text: str) -> str:
    return re.sub(r"[^\w\s]", "", text.lower()).strip()


def is_greeting(text: str) -> bool:
    """True only for a bare greeting such as "hi" or "Hello!"."""
    return _normalise(text) in GREETINGS


def is_farewell(text: str) -> bool:
    """True only for a bare farewell, so "exit exam dates?" is still answered."""
    return _normalise(text) in FAREWELLS


def _docs_fingerprint() -> str:
    """Hash of the PDF names, sizes and chunk settings, used to detect a stale index."""
    h = hashlib.sha256()
    h.update(f"fastembed|{EMBEDDING_MODEL}|{CHUNK_SIZE}|{CHUNK_OVERLAP}".encode())
    for pdf in sorted(DOCS_DIR.glob("*.pdf")):
        stat = pdf.stat()
        h.update(f"{pdf.name}|{stat.st_size}|{int(stat.st_mtime)}".encode())
    return h.hexdigest()


def _embeddings() -> FastEmbedEmbeddings:
    # fastembed runs the model with ONNX instead of PyTorch: far less memory, so it fits free hosting.
    return FastEmbedEmbeddings(model_name=EMBEDDING_MODEL, cache_dir=str(BASE_DIR / ".model_cache"))


def build_vectorstore(embeddings=None) -> FAISS:
    if not DOCS_DIR.exists() or not any(DOCS_DIR.glob("*.pdf")):
        raise FileNotFoundError(f"No PDF files found in {DOCS_DIR}")

    print("Loading university PDFs... (this may take a minute)")
    documents = PyPDFDirectoryLoader(str(DOCS_DIR)).load()
    if not documents:
        raise RuntimeError("No pages could be loaded from the PDFs.")

    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    chunks = splitter.split_documents(documents)
    print(f"Loaded {len(documents)} pages, split into {len(chunks)} chunks.")

    print("Building search index...")
    vectorstore = FAISS.from_documents(chunks, embeddings or _embeddings())
    vectorstore.save_local(str(INDEX_DIR))
    MANIFEST_FILE.write_text(json.dumps({"fingerprint": _docs_fingerprint()}))
    print("Index built and saved.")
    return vectorstore


def get_vectorstore() -> FAISS:
    """Load the local index, rebuilding it when the PDFs in docs/ have changed."""
    embeddings = _embeddings()
    try:
        manifest = json.loads(MANIFEST_FILE.read_text())
        if manifest.get("fingerprint") == _docs_fingerprint():
            # The index is created locally by build_vectorstore and never downloaded,
            # so deserialising its pickle file is safe here.
            return FAISS.load_local(
                str(INDEX_DIR), embeddings, allow_dangerous_deserialization=True
            )
        print("Documents changed since the index was built.")
    except FileNotFoundError:
        print("No search index found.")
    except Exception as exc:  # corrupt or incompatible index
        print(f"Could not load the index ({exc}).")
    return build_vectorstore(embeddings)


def _source_name(path: str) -> str:
    name = Path(path).stem
    name = re.sub(r"\s*\(\d+\)$", "", name)  # drop " (2)" download suffixes
    return name.replace("_", " ").replace("-", " ").strip()


class Chatbot:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Add it to the .env file (see .env.example)."
            )
        self.vectorstore = get_vectorstore()
        llm = ChatGroq(model=GROQ_MODEL, api_key=api_key, temperature=0.3)
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder("history"),
            ("human", "{question}"),
        ])
        self.chain = prompt | llm | StrOutputParser()

    def ask(self, question: str, history=None) -> dict:
        """Answer a question.

        history: list of {"role": "user"|"assistant", "content": str}, oldest first.
        Returns {"answer": str, "sources": [str, ...]}.
        """
        question = question.strip()
        history = (history or [])[-MAX_HISTORY_MESSAGES:]

        if is_greeting(question):
            return {"answer": GREETING_REPLY, "sources": []}
        if is_farewell(question):
            return {"answer": FAREWELL_REPLY, "sources": []}

        # Include the previous user turn so follow-ups like "and the fee?" retrieve well.
        last_user = next((m["content"] for m in reversed(history) if m["role"] == "user"), "")
        search_query = f"{last_user}\n{question}" if last_user and len(question) < 60 else question

        docs = self.vectorstore.similarity_search(search_query, k=TOP_K)
        context = "\n\n---\n\n".join(d.page_content for d in docs)

        messages = [
            HumanMessage(m["content"]) if m["role"] == "user" else AIMessage(m["content"])
            for m in history
            if m.get("content")
        ]
        answer = self.chain.invoke(
            {"context": context, "history": messages, "question": question}
        )

        sources = list(dict.fromkeys(_source_name(d.metadata.get("source", "")) for d in docs))
        return {"answer": answer, "sources": [s for s in sources if s]}

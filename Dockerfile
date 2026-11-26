# Container image for the IBU BITLoft chatbot (optional: Render uses render.yaml instead).
FROM python:3.12-slim

RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=7860
WORKDIR $HOME/app

COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

COPY --chown=user . .

# Download the embedding model and build the search index at build time, so the app starts fast.
RUN python -c "from rag import get_vectorstore; get_vectorstore()"

EXPOSE 7860
CMD ["python", "app.py"]

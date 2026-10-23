FROM python:3.13-slim
WORKDIR /app
COPY backend /app/backend
COPY packs /app/packs
COPY data/reference-ledger.jsonl /app/data/reference-ledger.jsonl
COPY run.py requirements.txt config.json DISCLOSURE.md README.md /app/
COPY dist /app/dist
RUN useradd --create-home --uid 10001 vitaloop && mkdir -p /app/data && chown -R vitaloop:vitaloop /app
USER vitaloop
EXPOSE 8765
VOLUME ["/app/data"]
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/api/health', timeout=2)" || exit 1
CMD ["python", "run.py", "--replay", "data/reference-ledger.jsonl", "--host", "0.0.0.0", "--port", "8765"]

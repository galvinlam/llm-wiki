FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY worker.py .
COPY llm_wiki ./llm_wiki

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8787"]

FROM python:3.12-slim

WORKDIR /app
COPY . /app

RUN pip install --upgrade pip && pip install -r requirements.txt

# Fix 11: Run as non-root user to limit blast radius of any code execution vulnerability
RUN useradd -m appuser && chown -R appuser /app
USER appuser

CMD ["streamlit", "run", "chatbot.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
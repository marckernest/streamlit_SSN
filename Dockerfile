FROM python:3.12-slim

WORKDIR /app
COPY . /app

RUN pip install --upgrade pip && pip install -r requirements.txt

CMD ["streamlit", "run", "chatbot.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
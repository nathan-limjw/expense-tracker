FROM python:3.11-slim

WORKDIR /app

COPY bot/requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY bot/ ./bot/
COPY utils/ ./utils/

CMD ["python", "-m", "bot.main"]
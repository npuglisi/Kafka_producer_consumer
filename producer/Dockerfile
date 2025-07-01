FROM python:3.11-slim

WORKDIR /app

COPY producer.py .

RUN pip install --no-cache-dir aiokafka numpy

ENV KAFKA_BROKER = kafka:9092 \
    TOPIC_NAME = user_events \
    N_USERS = 1000 \
    N_ITEMS = 100 \
    EVENTS_PER_SECOND = 100 \
    BATCH_SIZE = 10

CMD ["python", "producer.py"]

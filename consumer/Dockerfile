FROM python:3.11-slim

WORKDIR /app

COPY consumer.py .

RUN pip install --no-cache-dir faust-streaming aiokafka pymongo


ENV KAFKA_BROKER=kafka:9092 \
    TOPIC_NAME=user_events \
    GROUP_ID=realtime-consumer \
    MONGO_URI=mongodb://mongo:27017/ \
    WINDOW_MINUTES=1 \
    MONGO_DATABASE=analytics \
    PARTITIONS=8

CMD ["faust", "-A", "consumer", "worker", "-l", "info"]

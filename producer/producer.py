import os
import asyncio
import random
import json
import time
import numpy as np
from datetime import datetime
from aiokafka import AIOKafkaProducer

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
TOPIC_NAME = os.getenv("TOPIC_NAME", "user_events")
N_USERS = int(os.getenv("N_USERS", 1000))
N_ITEMS = int(os.getenv("N_ITEMS", 100))
EVENTS_PER_SECOND = int(os.getenv("EVENTS_PER_SECOND", 100))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", 10))

INTERACTION_TYPES = ["view", "click", "favorite", "add_to_cart", "purchase"]
users = [i for i in range(N_USERS)]
items = [i for i in range(N_ITEMS)]

# dinamically generate weights for items
def generate_weights(N_ITEMS):
    weights = np.linspace(1, 0.1, N_ITEMS)
    normalized = weights / weights.sum()
    return normalized.tolist()

def generate_random_event():
    weights = generate_weights(len(items))
    return {
        "user_id": random.choice(users),
        "item_id": random.choices(items, weights=weights, k=1)[0],
        "interaction_type": random.choice(INTERACTION_TYPES), "interaction_type": random.choices(INTERACTION_TYPES, weights=[0.45, 0.25, 0.15, 0.1, 0.05], k=1)[0],
        "timestamp": datetime.utcnow().isoformat()
    }

async def produce():
    producer = AIOKafkaProducer(
        bootstrap_servers = KAFKA_BROKER,
        value_serializer = lambda v: json.dumps(v).encode('utf-8')
    )
    await producer.start()
    try:
        interval = 1 / (EVENTS_PER_SECOND / BATCH_SIZE)
        while True:
            batch = [generate_random_event() for _ in range(BATCH_SIZE)]
            print(batch)
            await asyncio.gather(*[
                producer.send_and_wait(TOPIC_NAME, event)
                for event in batch
            ])
            await asyncio.sleep(interval)
    finally:
        await producer.stop()

if __name__ == "__main__":
    asyncio.run(produce())

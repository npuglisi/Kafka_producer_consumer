import faust
import os
from datetime import datetime, timedelta
from pymongo import MongoClient

#env
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
TOPIC_NAME = os.getenv("TOPIC_NAME", "user_events")
GROUP_ID = os.getenv("GROUP_ID", "realtime-consumer")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/")
WINDOW_MINUTES = float(os.getenv("WINDOW_MINUTES", 1))
DB_NAME = os.getenv("MONGO_DATABASE", "analytics")
WINDOW_DURATION = timedelta(minutes=WINDOW_MINUTES)
PARTITIONS = int(os.getenv("PARTITIONS", 8))
mongo_client = MongoClient(MONGO_URI)

# MongoDB setup
db = mongo_client[DB_NAME]
user_collection = db["user_aggregates"]
item_collection = db["item_aggregates"]

# Faust app config
app = faust.App(
    'analytics-app',
    broker=f'kafka://{KAFKA_BROKER}',
    value_serializer='json'
)

# defining model events
class Event(faust.Record, serializer='json'):
    user_id: str
    item_id: str
    interaction_type: str
    timestamp: str

events_topic = app.topic(TOPIC_NAME, value_type=Event)


def stringify_keys(d):
    if isinstance(d, dict):
        return {str(k): stringify_keys(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [stringify_keys(i) for i in d]
    else:
        return d

def on_user_window_close(key, agg):
    now = datetime.utcnow()
    total_types = sum(agg["interactions_per_type"].values()) or 1
    total_items = sum(agg["interactions_per_item"].values()) or 1
    avg_type = {k: round(v/total_types, 2) for k, v in agg["interactions_per_type"].items()}
    avg_item = {k: round(v/total_items, 2) for k, v in agg["interactions_per_item"].items()}
    doc = {
        "user_id": key[0],
        "window_start": agg.get("min_timestamp"),
        "window_end": agg.get("max_timestamp"),
        "avg_interactions_per_type": stringify_keys(avg_type),
        "interactions_per_type": stringify_keys(agg["interactions_per_type"]),
        "total_interactions": agg["total_interactions"],
        "interactions_per_item": stringify_keys(agg["interactions_per_item"]),
        "avg_interactions_per_item": stringify_keys(avg_item),
        "created_at": now
    }
    print(f"User aggregate for {key} at {now}: {doc}")
    user_collection.insert_one(doc)

def on_item_window_close(key, agg):
    now = datetime.utcnow()
    if not agg["user_counts"]:
        return
    min_inter = min(agg["user_counts"].values())
    max_inter = max(agg["user_counts"].values())
    unique_users = len(agg["user_counts"])
    total_types = sum(agg["interactions_per_type"].values()) or 1
    avg_type = {k: round(v/total_types, 2) for k, v in agg["interactions_per_type"].items()}
    doc = {
        "item_id": key[0],
        "window_start": agg.get("min_timestamp"),
        "window_end": agg.get("max_timestamp"),
        "min_interactions": min_inter,
        "max_interactions": max_inter,
        "unique_users": unique_users,
        "avg_interactions_per_type": stringify_keys(avg_type),
        "interactions_per_type": stringify_keys(agg["interactions_per_type"]),
        "created_at": now
    }
    print(f"Item aggregate for {key} at {now}: {doc}")
    item_collection.insert_one(doc)


user_table = app.Table(
    'user_agg',
    default=lambda: {
        "interactions_per_type": {},
        "interactions_per_item": {},
        "total_interactions": 0
    },
    on_window_close=on_user_window_close,
    partitions=PARTITIONS
).tumbling(60.0, expires=10.0)

item_table = app.Table(
    'item_agg',
    default=lambda: {
        "user_counts": {},
        "interactions_per_type": {}
    },
    on_window_close=on_item_window_close,
    partitions=PARTITIONS
).tumbling(60.0, expires=10.0)

@app.agent(events_topic)
async def process(events):
    async for event in events:
        event_ts = datetime.fromisoformat(event.timestamp)
        # User aggregation
        user_win = user_table[event.user_id].current()
        user_win["total_interactions"] += 1
        user_win["interactions_per_type"][event.interaction_type] = user_win["interactions_per_type"].get(event.interaction_type, 0) + 1
        user_win["interactions_per_item"][event.item_id] = user_win["interactions_per_item"].get(event.item_id, 0) + 1
        # Track min/max timestamp
        user_win["min_timestamp"] = min(user_win.get("min_timestamp", event_ts), event_ts)
        user_win["max_timestamp"] = max(user_win.get("max_timestamp", event_ts), event_ts)
        user_table[event.user_id] = user_win

        # Item aggregation
        item_win = item_table[event.item_id].current()
        item_win["user_counts"][event.user_id] = item_win["user_counts"].get(event.user_id, 0) + 1
        item_win["interactions_per_type"][event.interaction_type] = item_win["interactions_per_type"].get(event.interaction_type, 0) + 1
        item_win["min_timestamp"] = min(item_win.get("min_timestamp", event_ts), event_ts)
        item_win["max_timestamp"] = max(item_win.get("max_timestamp", event_ts), event_ts)
        item_table[event.item_id] = item_win

if __name__ == '__main__':
    app.main()
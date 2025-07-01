# Real-Time Data Pipeline with Kafka, MongoDB, and Metabase

This project is a solution to a data engineering case study. It simulates user interactions at scale, streams them using Kafka, performs real-time aggregations, stores them in MongoDB, and visualizes the results using Metabase.

## Case Study Data Engineer

### Problem 1: Random Data Generator and Kafka Producer

- Generates interaction data with `user_id`, `item_id`, `interaction_type`, and `timestamp`
- Kafka producer publishes data to the `user_events` topic
- Scalable and customizable via environment variables:
  - `EVENTS_PER_SECOND`
  - `BATCH_SIZE`
  - `N_USERS`
  - `N_ITEMS`
  - `PARTITIONS`

###  Problem 2: Kafka Consumer and Real-Time Aggregations

- Kafka consumer consumes `user_events`
- Performs real-time aggregations per 1-minute windows using Faust:
  - Average amount
  - Minimum amount
  - Maximum amount
  - Total amount
- Stores results in MongoDB (`analytics` database)
- MongoDB was chosen for:
  - High performance on inserts
  - Schema flexibility
  - Easy integration with Metabase

###  Problem 3: Data Visualization and Dashboarding

- Aggregated metrics visualized using **Metabase**
- MongoDB connected directly to Metabase
- Displays:

![image](https://github.com/user-attachments/assets/c520c218-7d7c-4cb1-986b-ad4462a83e91)

<img width="1673" alt="image" src="https://github.com/user-attachments/assets/beb80e65-0136-48cb-b528-deb00df3589b" />


---

## How to Run

1. Clone the repository:
```bash
git clone <repo_url>
cd <repo>
```

2. Build and start the services:
```bash
docker compose up -d
```

3. Access Metabase at: [http://localhost:3000](http://localhost:3000)

```
login: email@email.com
password: 123456!
```
At home page click at Avrioc Dashboard

---

##  Project Structure

```
.
├── docker-compose.yml
├── producer/
│   ├── producer.py
│   └── Dockerfile
├── consumer/
│   ├── consumer.py
│   └── Dockerfile
└── metabase-data/  # Persistent volume for Metabase
```

---

## Tools

- Kafka (Confluent Platform)
- MongoDB
- Python (asyncio, aiokafka, pymongo, faust)
- Docker + Docker Compose
- Metabase

---

##  Aggregated Metrics

Metrics are grouped by interaction type and item and updated every 1 minute.

- Average `amount`
- Minimum `amount`
- Maximum `amount`
- Total `amount`

---

##  Notes

- The Kafka topic `user_events` is created by the `kafka-init` service.
- Real-time aggregation runs continuously while data is generated.
- Metabase reads directly from MongoDB in near real-time.

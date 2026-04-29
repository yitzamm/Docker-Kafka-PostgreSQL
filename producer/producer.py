from fastapi import FastAPI
from kafka import KafkaProducer
import json
import time

app = FastAPI()

# -------------------------
# KAFKA CONNECTION (WITH RETRY)
# -------------------------
producer = None

for i in range(20):  # retry for ~1 minute
    try:
        producer = KafkaProducer(
            bootstrap_servers="kafka:29092",
            value_serializer=lambda v: json.dumps(v).encode("utf-8")
        )
        print("✅ Kafka connected successfully")
        break
    except Exception as e:
        print(f"⏳ Kafka not ready, retrying... ({i+1}/20)")
        time.sleep(3)

if producer is None:
    raise Exception("❌ Kafka is not available after retries")

TOPIC = "clientes-events"

# -------------------------
# API ENDPOINT (FROM API SERVICE)
# -------------------------
@app.post("/event")
def send_event(event: dict):
    try:
        producer.send(TOPIC, event)
        producer.flush()
        print("📨 Event sent to Kafka:", event)
        return {"status": "sent"}
    except Exception as e:
        print("❌ Error sending to Kafka:", str(e))
        return {"status": "error", "detail": str(e)}
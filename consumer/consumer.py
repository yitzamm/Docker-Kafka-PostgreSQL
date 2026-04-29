from kafka import KafkaConsumer
import json
import psycopg2
import requests
import time

# -------------------------
# DB CONNECTION
# -------------------------
def get_connection():
    return psycopg2.connect(
        host="postgres",
        database="clientesdb",
        user="admin",
        password="admin"
    )

# -------------------------
# LOG FORMATTING
# -------------------------
def format_log(action, name):
    icons = {
        "create": "🟢",
        "delete": "🔴",
        "update": "🟡"
    }
    return f"{icons[action]} Client {action}: {name}"

# -------------------------
# KAFKA CONSUMER
# -------------------------
consumer = None

for i in range(20):   # retry ~1 minute
    try:
        consumer = KafkaConsumer(
            "clientes-events",
            bootstrap_servers="kafka:29092",
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset="earliest",
            group_id="clientes-group"
        )

        print("✅ Kafka consumer connected successfully")
        break

    except Exception as e:
        print(f"⏳ Kafka not ready, retrying... ({i+1}/20)")
        time.sleep(3)

if consumer is None:
    raise Exception("❌ Kafka is not available after retries")

print("Consumer running...")

for msg in consumer:
    event = msg.value
    action = event.get("action")
    if not action:
        print("Skipping event:", event)
        continue

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # CREATE
        if action == "CREATE":
            c = event["cliente"]
            cursor.execute("""
                INSERT INTO clientes
                (nombre, apellido, edad, correo, telefono, direccion)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (c["nombre"], c["apellido"], c["edad"], c["correo"], c["telefono"], c["direccion"]))
            requests.post("http://api:8000/log", json={
                "message": format_log("create", c["nombre"])
            })

        # UPDATE
        elif action == "UPDATE":
            c = event["cliente"]
            cursor.execute("""
                UPDATE clientes
                SET nombre=%s, apellido=%s, edad=%s,
                    correo=%s, telefono=%s, direccion=%s
                WHERE id=%s
            """, (c["nombre"], c["apellido"], c["edad"],
                  c["correo"], c["telefono"], c["direccion"], event["id"]))
            requests.post("http://api:8000/log", json={
                "message": format_log("update", c["nombre"])
            })

        # DELETE
        elif action == "DELETE":
            cursor.execute(
                "DELETE FROM clientes WHERE id=%s",
                (event["id"],)
            )
            requests.post("http://api:8000/log", json={
                "message": format_log("delete", c["nombre"])
            })

        conn.commit()
        print("Processed:", event)

    except Exception as e:
        print("Error:", e)
        conn.rollback()

    finally:
        cursor.close()
        conn.close()


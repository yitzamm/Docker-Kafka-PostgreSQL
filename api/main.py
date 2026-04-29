from fastapi import FastAPI, WebSocket, Request
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import psycopg2

app = FastAPI()

clients: List[WebSocket] = []

class LogEvent(BaseModel):
    message: str

# -------------------------
# CORS
# -------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8083"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# DB CONNECTION (READ ONLY)
# -------------------------
def get_connection():
    return psycopg2.connect(
        host="postgres",
        database="clientesdb",
        user="admin",
        password="admin"
    )

# -------------------------
# MODEL
# -------------------------
class Cliente(BaseModel):
    nombre: str
    apellido: str
    edad: int
    correo: str
    telefono: str
    direccion: str

# -------------------------
# GET CLIENTS (UI TABLE)
# -------------------------
@app.get("/clientes")
def get_clientes():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM clientes")
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return [
        {
            "id": r[0],
            "nombre": r[1],
            "apellido": r[2],
            "edad": r[3],
            "correo": r[4],
            "telefono": r[5],
            "direccion": r[6],
        }
        for r in rows
    ]

# -------------------------
# SEND EVENT TO PRODUCER SERVICE
# -------------------------
PRODUCER_URL = "http://producer:8001/event"

def send_to_producer(event: dict):
    requests.post(PRODUCER_URL, json=event)

# -------------------------
# CREATE
# -------------------------
@app.post("/clientes")
def create_cliente(cliente: Cliente):
    send_to_producer({
        "action": "CREATE",
        "cliente": cliente.model_dump()
    })
    return {"status": "sent"}

# -------------------------
# UPDATE
# -------------------------
@app.put("/clientes/{cliente_id}")
def update_cliente(cliente_id: int, cliente: Cliente):
    send_to_producer({
        "action": "UPDATE",
        "id": cliente_id,
        "cliente": cliente.model_dump()
    })
    return {"status": "sent"}

# -------------------------
# DELETE
# -------------------------
@app.delete("/clientes/{cliente_id}")
def delete_cliente(cliente_id: int):
    send_to_producer({
        "action": "DELETE",
        "id": cliente_id
    })
    return {"status": "sent"}

# -------------------------
# WEBSOCKET - LOGS
# -------------------------
@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)

    try:
        while True:
            # We don't expect messages from frontend
            await websocket.receive_text()
    except:
        clients.remove(websocket)

async def broadcast_log(message: str):
    for client in clients:
        await client.send_text(message)

# -------------------------
# HTTP Bridge Endpoint
# -------------------------
@app.post("/log")
async def receive_log(event: LogEvent):
    await broadcast_log(event.message)
    return {"status": "ok"}
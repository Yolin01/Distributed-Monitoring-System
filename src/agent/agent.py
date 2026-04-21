import asyncio
import psutil
import os
import json
import aio_pika
from datetime import datetime, timezone

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq/")
QUEUE_NAME   = os.getenv("RABBITMQ_QUEUE", "metrics")
INTERVAL_SEC = 10

async def run():
    print("Agent démarré, attente de RabbitMQ...")

    # Attendre que RabbitMQ soit prêt
    connection = None
    for attempt in range(30):
        try:
            connection = await aio_pika.connect_robust(RABBITMQ_URL)
            print("Connecté à RabbitMQ")
            break
        except Exception as e:
            print(f"Tentative {attempt+1}/30 : {e}")
            await asyncio.sleep(5)

    if not connection:
        print(" Impossible de se connecter après 30 tentatives")
        return

    # Connexion persistante — on ne ferme JAMAIS ici
    channel = await connection.channel()
    await channel.declare_queue(QUEUE_NAME, durable=True)
    print(f" Envoi toutes les {INTERVAL_SEC}s...")

    while True:
        try:
            payload = {
                "node_id": 1,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage("/").percent,
            }

            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(payload).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                ),
                routing_key=QUEUE_NAME,
            )
            print(f"✔ CPU={payload['cpu_percent']}% "
                  f"RAM={payload['memory_percent']}% "
                  f"DISK={payload['disk_percent']}%")

        except Exception as e:
            print(f"Erreur: {e} — reconnexion dans 5s")
            await asyncio.sleep(5)
            # connect_robust gère la reconnexion automatiquement
            try:
                channel = await connection.channel()
                await channel.declare_queue(QUEUE_NAME, durable=True)
            except Exception:
                pass

        await asyncio.sleep(INTERVAL_SEC)

asyncio.run(run())
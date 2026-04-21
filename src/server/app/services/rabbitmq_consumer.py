import asyncio
import aio_pika
import json

from config.settings import settings
from ..database import SessionLocal
from ..models import Metric, Node
from .alert_detector import detect_alerts


async def start_consumer():
    print("Consumer RabbitMQ démarré...")

    for attempt in range(10):
        try:
            connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
            print(" Connecté à RabbitMQ")

            channel = await connection.channel()

            queue = await channel.declare_queue(
                settings.RABBITMQ_QUEUE,
                durable=True
            )

            print(f" En attente de messages sur '{settings.RABBITMQ_QUEUE}'...")

            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        try:
                            data = json.loads(message.body)

                            print(f" Message reçu: {data}")

                            db = SessionLocal()

                            try:
                                #  Trouver le node
                                node = db.query(Node).filter_by(
                                    external_id=str(data["node_id"])
                                ).first()

                                #  Créer si inexistant
                                if not node:
                                    node = Node(
                                        external_id=str(data["node_id"]),
                                        name=f"node-{data['node_id']}"
                                    )
                                    db.add(node)
                                    db.commit()
                                    db.refresh(node)

                                #  Créer métrique
                                metric = Metric(
                                    node_id=node.id,
                                    timestamp=data["timestamp"],
                                    cpu_percent=data["cpu_percent"],
                                    memory_percent=data["memory_percent"],
                                    disk_percent=data["disk_percent"]
                                )

                                db.add(metric)

                                #  Alertes
                                alerts = detect_alerts(metric)
                                for alert in alerts:
                                    db.add(alert)

                                db.commit()

                                print(" Données enregistrées")

                            finally:
                                db.close()

                        except Exception as e:
                            print(f" Erreur traitement: {e}")

            return

        except Exception as e:
            print(f" Tentative {attempt + 1}/10 échouée: {e}")
            await asyncio.sleep(5)

    print(" Impossible de se connecter à RabbitMQ")


if __name__ == "__main__":
    asyncio.run(start_consumer())
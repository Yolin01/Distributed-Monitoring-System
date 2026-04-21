"""Initialise la base avec des données de démonstration."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.server.app.database import SessionLocal, engine, Base
from src.server.app.models import User, Node
from src.server.app.security import hash_password

Base.metadata.create_all(bind=engine)
db = SessionLocal()

users = [
    User(username="admin",    hashed_password=hash_password("admin"),    role="admin"),
    User(username="operator", hashed_password=hash_password("operator"), role="operator"),
    User(username="viewer",   hashed_password=hash_password("viewer"),   role="viewer"),
]
nodes = [
    Node(name="node-01", ip_address="192.168.1.10"),
    Node(name="node-02", ip_address="192.168.1.11"),
    Node(name="node-03", ip_address="192.168.1.12"),
]
for obj in users + nodes:
    db.add(obj)
db.commit()
print("Données de démo insérées avec succès.")
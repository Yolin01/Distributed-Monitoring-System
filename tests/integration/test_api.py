"""
Tests automatisés — Monitoring Distribué
Couvre : Auth JWT, Métriques API, Nodes API
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/server'))

from app.main import app
from app.database import Base, get_db
from app.models import User, Node, Metric
from app.security import hash_password

# ─── Base de test en mémoire ─────────────────────────────
SQLALCHEMY_TEST_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Créer un user admin de test
    admin = User(
        username="admin",
        hashed_password=hash_password("admin123"),
        role="admin"
    )
    db.add(admin)

    # Créer un node de test
    node = Node(
        external_id="test-node-01",
        name="Test Node 01",
        status="active"
    )
    db.add(node)
    db.commit()
    db.refresh(node)

    # Créer des métriques de test
    import datetime
    for i in range(5):
        metric = Metric(
            node_id=node.id,
            timestamp=datetime.datetime.utcnow(),
            cpu_percent=float(20 + i * 5),
            memory_percent=float(30 + i * 3),
            disk_percent=10.0
        )
        db.add(metric)
    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_token(client):
    response = client.post(
        "/auth/login",
        data={"username": "admin", "password": "admin123"}
    )
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


# ─── Tests Auth ──────────────────────────────────────────

class TestAuth:

    def test_login_success(self, client):
        response = client.post(
            "/auth/login",
            data={"username": "admin", "password": "admin123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client):
        response = client.post(
            "/auth/login",
            data={"username": "admin", "password": "mauvais"}
        )
        assert response.status_code == 401

    def test_login_unknown_user(self, client):
        response = client.post(
            "/auth/login",
            data={"username": "inconnu", "password": "test"}
        )
        assert response.status_code == 401

    def test_protected_route_without_token(self, client):
        response = client.get("/metrics/")
        assert response.status_code == 401

    def test_protected_route_with_token(self, client, auth_headers):
        response = client.get("/metrics/", headers=auth_headers)
        assert response.status_code == 200

    def test_invalid_token(self, client):
        response = client.get(
            "/metrics/",
            headers={"Authorization": "Bearer token-invalide"}
        )
        assert response.status_code == 401


# ─── Tests Health ────────────────────────────────────────

class TestHealth:

    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_root(self, client):
        response = client.get("/")
        assert response.status_code == 200


# ─── Tests Métriques ─────────────────────────────────────

class TestMetrics:

    def test_list_metrics(self, client, auth_headers):
        response = client.get("/metrics/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 5

    def test_list_metrics_pagination(self, client, auth_headers):
        response = client.get("/metrics/?limit=2&offset=0", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_latest_metrics(self, client, auth_headers):
        response = client.get("/metrics/latest", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert "node" in data[0]
        assert "latest_metric" in data[0]

    def test_node_metrics(self, client, auth_headers):
        response = client.get("/metrics/node/1", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_node_stats(self, client, auth_headers):
        response = client.get("/metrics/node/1/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "cpu_avg" in data
        assert "cpu_min" in data
        assert "cpu_max" in data
        assert "memory_avg" in data
        assert "total_records" in data
        assert data["total_records"] == 5

    def test_metrics_structure(self, client, auth_headers):
        response = client.get("/metrics/", headers=auth_headers)
        metric = response.json()[0]
        assert "id" in metric
        assert "node_id" in metric
        assert "cpu_percent" in metric
        assert "memory_percent" in metric
        assert "disk_percent" in metric
        assert "timestamp" in metric


# ─── Tests Nodes ─────────────────────────────────────────

class TestNodes:

    def test_list_nodes(self, client, auth_headers):
        response = client.get("/nodes/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_node_structure(self, client, auth_headers):
        response = client.get("/nodes/", headers=auth_headers)
        node = response.json()[0]
        assert "id" in node
        assert "name" in node
        assert "status" in node
        assert node["status"] == "active"
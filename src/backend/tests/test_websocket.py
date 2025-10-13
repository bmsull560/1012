from fastapi.testclient import TestClient
from app.main import app

def test_websocket_connection():
    client = TestClient(app)
    with client.websocket_connect("/api/v1/ws/test-workspace") as websocket:
        data = {"message": "Hello"}
        websocket.send_json(data)
        response = websocket.receive_json()
        assert response["type"] == "message"

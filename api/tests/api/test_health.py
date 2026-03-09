from fastapi.testclient import TestClient

def test_health_check(client: TestClient):
    """
    Smoke Test (P0): Rapid verify if the application can start
    and the base route /health is functional.
    """
    response = client.get("/health")
    
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

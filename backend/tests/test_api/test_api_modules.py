from fastapi.testclient import TestClient


def test_properties_endpoint_is_available(client: TestClient) -> None:
    response = client.get("/api/v1/properties/")

    assert response.status_code == 200
    assert response.json()["module"] == "properties"

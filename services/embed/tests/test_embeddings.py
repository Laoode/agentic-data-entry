"""HTTP contract tests for the OpenAI-compatible embedding endpoint.

Hermetic: they run against a FakeEncoder, so no model download and no torch.
"""

import base64
import struct


def test_health_reports_model_and_dims(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["model"] == "fake-encoder"
    assert body["device"] == "cpu"
    assert body["dimensions"] == 8


def test_single_string_input(client):
    resp = client.post("/v1/embeddings", json={"input": "halo dunia"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["object"] == "list"
    assert len(body["data"]) == 1
    first = body["data"][0]
    assert first["object"] == "embedding"
    assert first["index"] == 0
    assert len(first["embedding"]) == 8
    assert body["usage"]["prompt_tokens"] >= 1


def test_list_input_preserves_order_and_indices(client):
    resp = client.post("/v1/embeddings", json={"input": ["a", "b", "c"]})
    body = resp.json()
    assert [d["index"] for d in body["data"]] == [0, 1, 2]
    assert len(body["data"]) == 3


def test_determinism(client):
    a = client.post("/v1/embeddings", json={"input": "same text"}).json()
    b = client.post("/v1/embeddings", json={"input": "same text"}).json()
    assert a["data"][0]["embedding"] == b["data"][0]["embedding"]


def test_base64_encoding_format_is_float32_little_endian(client):
    resp = client.post(
        "/v1/embeddings", json={"input": "x", "encoding_format": "base64"}
    )
    embedding = resp.json()["data"][0]["embedding"]
    assert isinstance(embedding, str)
    raw = base64.b64decode(embedding)
    floats = struct.unpack(f"<{len(raw) // 4}f", raw)
    assert len(floats) == 8


def test_empty_string_input_rejected(client):
    resp = client.post("/v1/embeddings", json={"input": ""})
    assert resp.status_code == 422


def test_empty_list_input_rejected(client):
    resp = client.post("/v1/embeddings", json={"input": []})
    assert resp.status_code == 422


def test_model_field_is_echoed_when_provided(client):
    resp = client.post("/v1/embeddings", json={"input": "x", "model": "custom-name"})
    assert resp.json()["model"] == "custom-name"


def test_model_defaults_to_loaded_model_name(client):
    resp = client.post("/v1/embeddings", json={"input": "x"})
    assert resp.json()["model"] == "fake-encoder"

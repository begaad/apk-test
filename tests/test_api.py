import asyncio
import importlib.util
from pathlib import Path
import httpx

spec = importlib.util.spec_from_file_location("lab_api", Path(__file__).resolve().parents[1] / "backend" / "main.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

async def request(method, path, token=None, json=None):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=m.app), base_url="http://test") as client:
        return await client.request(method, path, headers={"Authorization": f"Bearer {token}"} if token else {}, json=json)

def call(method, path, token=None, json=None):
    return asyncio.run(request(method, path, token, json))

def login(name):
    r = call("POST", "/api/v1/auth/login", json={"username": name, "password": name + "123"})
    assert r.status_code == 200, r.text
    return r.json()["token"]

def test_root_requires_apk():
    assert call("GET", "/").status_code in (200, 503)

def test_regular_order_flow():
    z = login("zhangsan")
    l = login("lisi")
    assert len(call("GET", "/api/v1/products", z).json()) == 3
    assert call("POST", "/api/v1/orders", z, {"product_id": 1}).status_code == 200
    assert all(x["username"] == "zhangsan" for x in call("GET", "/api/v1/orders", z).json())
    assert all(x["username"] == "lisi" for x in call("GET", "/api/v1/orders", l).json())

def test_sensitive_disclosure_is_reproducible():
    z = login("zhangsan")
    out = call("GET", "/api/v1/account/export", z)
    assert out.status_code == 200
    assert {x["username"] for x in out.json()["records"]} == {"zhangsan", "lisi", "admin"}
    assert any(x["recovery_code"] for x in out.json()["records"])

def test_command_injection_is_reproducible():
    z = login("zhangsan")
    out = call("POST", "/api/v1/tools/diagnose", z, {"host": "localhost; id"})
    assert out.status_code == 200
    assert "uid=" in out.json()["output"]

def test_auth_required():
    for path in ("/api/v1/account/export", "/api/v1/orders", "/api/v1/products"):
        assert call("GET", path).status_code == 401

"""Deliberately vulnerable, self-contained API lab. Use ONLY on an isolated network."""
import os
import secrets
import subprocess
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field

app = FastAPI(title="APK API Audit Lab", docs_url=None, redoc_url=None, openapi_url=None)
ROOT = Path(__file__).resolve().parent.parent
APK_PATH = Path(os.getenv("APK_PATH", str(ROOT / "apk" / "app.apk")))
# Entirely synthetic teaching records; no real credentials or personal information.
ACCOUNTS = {
    "zhangsan": {"password": "zhangsan123", "role": "user", "email": "zhangsan@example.invalid", "phone": "13800000001", "recovery_code": "DEMO-ZS-7412"},
    "lisi": {"password": "lisi123", "role": "user", "email": "lisi@example.invalid", "phone": "13800000002", "recovery_code": "DEMO-LS-8631"},
    "admin": {"password": "admin123", "role": "admin", "email": "admin@example.invalid", "phone": "13800000003", "recovery_code": "DEMO-AD-2901"},
}
PRODUCTS = [{"id": 1, "name": "无线鼠标", "price": 59}, {"id": 2, "name": "机械键盘", "price": 199}, {"id": 3, "name": "USB-C 扩展坞", "price": 129}]
TOKENS: dict[str, str] = {}
ORDERS: list[dict] = []

class LoginBody(BaseModel):
    username: str
    password: str

class OrderBody(BaseModel):
    product_id: int

class DiagnoseBody(BaseModel):
    host: str = Field(min_length=1, max_length=200)


def current_user(authorization: Optional[str]) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="请登录")
    name = TOKENS.get(authorization[7:])
    if name is None:
        raise HTTPException(status_code=401, detail="令牌无效")
    return name

@app.get("/", include_in_schema=False)
def download_apk():
    if not APK_PATH.is_file():
        return HTMLResponse("<h2>APK 尚未编译</h2><p>先编译 Android 工程，将 app-debug.apk 放到 apk/app.apk，刷新首页即可下载。</p>", status_code=503)
    return FileResponse(APK_PATH, filename="audit-lab.apk", media_type="application/vnd.android.package-archive")

@app.get("/healthz")
def healthz():
    return {"ok": True, "apk_ready": APK_PATH.is_file()}

@app.post("/api/v1/auth/login")
def login(body: LoginBody):
    record = ACCOUNTS.get(body.username)
    if not record or not secrets.compare_digest(body.password, record["password"]):
        raise HTTPException(status_code=401, detail="账号或密码错误")
    token = secrets.token_urlsafe(24)
    TOKENS[token] = body.username
    return {"token": token, "username": body.username, "role": record["role"]}

@app.get("/api/v1/products")
def products(authorization: Optional[str] = Header(default=None)):
    current_user(authorization)
    return PRODUCTS

@app.get("/api/v1/me")
def me(authorization: Optional[str] = Header(default=None)):
    username = current_user(authorization)
    return {"username": username, "role": ACCOUNTS[username]["role"]}

@app.post("/api/v1/orders")
def create_order(body: OrderBody, authorization: Optional[str] = Header(default=None)):
    username = current_user(authorization)
    item = next((p for p in PRODUCTS if p["id"] == body.product_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail="商品不存在")
    order = {"id": len(ORDERS) + 1, "username": username, "product_id": item["id"], "product_name": item["name"], "amount": item["price"]}
    ORDERS.append(order)
    return order

@app.get("/api/v1/orders")
def orders(authorization: Optional[str] = Header(default=None)):
    username = current_user(authorization)
    return ORDERS if ACCOUNTS[username]["role"] == "admin" else [o for o in ORDERS if o["username"] == username]

# VULNERABILITY #1: authenticated user exports every account's sensitive synthetic data.
# The expected filtering by current_user is accidentally omitted.
@app.get("/api/v1/account/export")
def account_export(authorization: Optional[str] = Header(default=None)):
    current_user(authorization)
    return {"records": [{"username": u, "email": r["email"], "phone": r["phone"], "recovery_code": r["recovery_code"]} for u, r in ACCOUNTS.items()]}

# VULNERABILITY #2: shell metacharacters from host execute inside the deliberately isolated lab container.
# Do not deploy on a host with secrets, mounting docker.sock, or network access to anything sensitive.
@app.post("/api/v1/tools/diagnose")
def diagnose(body: DiagnoseBody, authorization: Optional[str] = Header(default=None)):
    current_user(authorization)
    try:
        result = subprocess.run("getent hosts " + body.host, shell=True, executable="/bin/sh", capture_output=True, text=True, timeout=3, cwd="/tmp")
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="诊断超时")
    return {"exit_code": result.returncode, "output": (result.stdout + result.stderr)[:2000]}

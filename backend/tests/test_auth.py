"""
认证模块测试
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.base import Base
from app.db.database import get_db


# 测试数据库配置
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """覆盖数据库依赖"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    """测试前创建数据库表"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def test_register_success():
    """测试注册成功"""
    response = client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "password": "test123456",
            "confirm_password": "test123456"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "注册成功"
    assert data["user"]["username"] == "testuser"


def test_register_password_mismatch():
    """测试两次密码不一致"""
    response = client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "password": "test123456",
            "confirm_password": "different123"
        }
    )
    assert response.status_code == 400
    assert "两次输入的密码不一致" in response.json()["detail"]


def test_register_username_exists():
    """测试用户名已存在"""
    # 先注册一个用户
    client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "password": "test123456",
            "confirm_password": "test123456"
        }
    )

    # 再次注册相同用户名
    response = client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "password": "test123456",
            "confirm_password": "test123456"
        }
    )
    assert response.status_code == 400
    assert "用户名已存在" in response.json()["detail"]


def test_login_success():
    """测试登录成功"""
    # 先注册
    client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "password": "test123456",
            "confirm_password": "test123456"
        }
    )

    # 登录
    response = client.post(
        "/api/auth/login",
        json={
            "username": "testuser",
            "password": "test123456"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["username"] == "testuser"


def test_login_wrong_password():
    """测试密码错误"""
    # 先注册
    client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "password": "test123456",
            "confirm_password": "test123456"
        }
    )

    # 使用错误密码登录
    response = client.post(
        "/api/auth/login",
        json={
            "username": "testuser",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401
    assert "用户名或密码错误" in response.json()["detail"]


def test_get_me_success():
    """测试获取当前用户信息"""
    # 注册
    client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "password": "test123456",
            "confirm_password": "test123456"
        }
    )

    # 登录获取token
    login_response = client.post(
        "/api/auth/login",
        json={
            "username": "testuser",
            "password": "test123456"
        }
    )
    token = login_response.json()["access_token"]

    # 获取用户信息
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"


def test_get_me_no_token():
    """测试未携带token"""
    response = client.get("/api/auth/me")
    assert response.status_code == 403

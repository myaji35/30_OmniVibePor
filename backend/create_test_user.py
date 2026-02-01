"""테스트 사용자 생성 스크립트"""
import sys
sys.path.append("/app")

from app.services.neo4j_client import get_neo4j_client
from app.models.neo4j_models import UserModel, get_crud_manager
from datetime import datetime

# User 생성
user = UserModel(
    user_id="test_user",
    email="test@example.com",
    name="Test User",
    subscription_tier="free"
)

crud = get_crud_manager()
result = crud.create_user(user)
print(f"User created: {result}")

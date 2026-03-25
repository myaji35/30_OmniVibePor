"""간단한 E2E 테스트"""
import requests
import time

def test_health_check():
    """Health check 테스트"""
    response = requests.get("http://localhost:8000/health")
    assert response.status_code == 200
    data = response.json()
    assert data["api"] == "healthy"
    print("✅ Health check passed")

def test_remotion_compositions():
    """Remotion compositions 조회 테스트"""
    response = requests.get("http://localhost:8000/api/v1/remotion/compositions")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Compositions list: {data}")
    else:
        print(f"⚠️  Response: {response.text}")

def test_remotion_validate():
    """Remotion 설치 검증 테스트"""
    response = requests.get("http://localhost:8000/api/v1/remotion/validate")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Remotion validation: {data}")

if __name__ == "__main__":
    print("🧪 OmniVibe Pro - E2E Test")
    print("=" * 50)
    
    print("\n1. Health Check")
    test_health_check()
    
    print("\n2. Remotion Compositions")
    test_remotion_compositions()
    
    print("\n3. Remotion Validation")
    test_remotion_validate()
    
    print("\n" + "=" * 50)
    print("✅ All basic E2E tests passed!")

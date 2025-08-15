"""
Tests for critical API fixes
"""
import pytest
from fastapi.testclient import TestClient
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set test environment
os.environ["ENVIRONMENT"] = "testing"
os.environ["MAS_SECRET_KEY"] = "test-secret-key"
os.environ["ADMIN_SECRET"] = "test-admin-secret"
os.environ["REDIS_HOST"] = "localhost"
os.environ["REDIS_PORT"] = "6379"
os.environ["DATA_PATH"] = "/tmp/test-data"


class TestAPIImports:
    """Test that all imports work correctly"""
    
    def test_api_imports(self):
        """Test that API module can be imported without errors"""
        try:
            from api import main
            assert main.app is not None
        except ImportError as e:
            pytest.fail(f"Failed to import API: {e}")
    
    def test_security_imports(self):
        """Test that security module imports work"""
        try:
            from api.security import Role, TokenData, check_permission
            assert Role.ADMIN == "admin"
            assert Role.USER == "user"
        except ImportError as e:
            pytest.fail(f"Failed to import security: {e}")
    
    def test_multitool_imports(self):
        """Test that multitool imports are correct"""
        try:
            from tools.multitool import (
                list_tools, list_workflows, list_apps,
                get_tool_versions, get_workflow_versions, get_app_versions,
                rollback_tool, rollback_workflow, rollback_app,
            )
            # These should exist
            assert callable(list_tools)
            assert callable(rollback_app)
        except ImportError as e:
            pytest.fail(f"Failed to import multitool functions: {e}")
    
    def test_removed_imports(self):
        """Test that removed functions don't exist"""
        with pytest.raises(ImportError):
            from tools.multitool import list_instances
        with pytest.raises(ImportError):
            from tools.multitool import get_instance_versions
        with pytest.raises(ImportError):
            from tools.multitool import rollback_instance


class TestAuthSecurity:
    """Test authentication and security fixes"""
    
    @pytest.fixture
    def client(self):
        from api.main import app
        return TestClient(app)
    
    def test_token_issue_requires_secret(self, client):
        """Test that token issuance requires admin secret in production"""
        # Set production environment
        os.environ["ENVIRONMENT"] = "production"
        
        # Without X-Admin-Secret header
        response = client.post(
            "/api/v1/auth/token",
            json={"user_id": "test_user"}
        )
        assert response.status_code in [403, 500]
        
        # With wrong secret
        response = client.post(
            "/api/v1/auth/token",
            json={"user_id": "test_user"},
            headers={"X-Admin-Secret": "wrong-secret"}
        )
        assert response.status_code == 403
        
        # With correct secret
        response = client.post(
            "/api/v1/auth/token",
            json={"user_id": "test_user"},
            headers={"X-Admin-Secret": "test-admin-secret"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    def test_token_validation(self, client):
        """Test input validation for auth endpoint"""
        os.environ["ENVIRONMENT"] = "development"
        
        # Invalid user_id format
        response = client.post(
            "/api/v1/auth/token",
            json={"user_id": "invalid user id!"}
        )
        assert response.status_code == 422
        
        # Invalid role
        response = client.post(
            "/api/v1/auth/token",
            json={"user_id": "test_user", "role": "superadmin"}
        )
        assert response.status_code == 422
        
        # Invalid expires_minutes
        response = client.post(
            "/api/v1/auth/token",
            json={"user_id": "test_user", "expires_minutes": 20000}
        )
        assert response.status_code == 422


class TestProtectedEndpoints:
    """Test that sensitive endpoints are protected"""
    
    @pytest.fixture
    def client(self):
        from api.main import app
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self, client):
        """Get auth headers with admin token"""
        os.environ["ENVIRONMENT"] = "development"
        response = client.post(
            "/api/v1/auth/token",
            json={"user_id": "admin_user", "role": "admin"}
        )
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture
    def user_headers(self, client):
        """Get auth headers with user token"""
        os.environ["ENVIRONMENT"] = "development"
        response = client.post(
            "/api/v1/auth/token",
            json={"user_id": "regular_user", "role": "user"}
        )
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_rollback_requires_admin(self, client, user_headers, auth_headers):
        """Test that rollback endpoints require admin role"""
        # Test without auth
        response = client.post("/api/v1/registry/tools/test/rollback")
        assert response.status_code == 403
        
        # Test with user role
        response = client.post(
            "/api/v1/registry/tools/test/rollback",
            headers=user_headers
        )
        assert response.status_code == 403
        
        # Test with admin role (will fail because tool doesn't exist, but auth passes)
        response = client.post(
            "/api/v1/registry/tools/test/rollback",
            headers=auth_headers
        )
        assert response.status_code in [400, 404]  # Not 403
    
    def test_metrics_requires_auth(self, client, user_headers):
        """Test that metrics endpoint requires authentication"""
        # Without auth
        response = client.get("/metrics")
        assert response.status_code == 403
        
        # With auth (user has metrics:read permission)
        response = client.get("/metrics", headers=user_headers)
        assert response.status_code in [200, 204]  # Prometheus might not be installed


class TestCORSConfiguration:
    """Test CORS is properly configured"""
    
    @pytest.fixture
    def client(self):
        from api.main import app
        return TestClient(app)
    
    def test_cors_headers(self, client):
        """Test that CORS headers are set correctly"""
        # Test preflight request
        response = client.options(
            "/api/v1/chat",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            }
        )
        
        # Should allow configured origins
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        
        # Test from unauthorized origin
        response = client.options(
            "/api/v1/chat",
            headers={
                "Origin": "http://evil.com",
                "Access-Control-Request-Method": "POST",
            }
        )
        
        # Should not have CORS headers for unauthorized origin
        if "access-control-allow-origin" in response.headers:
            assert response.headers["access-control-allow-origin"] != "http://evil.com"


class TestInputValidation:
    """Test input validation for chat endpoints"""
    
    @pytest.fixture
    def client(self):
        from api.main import app
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self, client):
        """Get auth headers"""
        os.environ["ENVIRONMENT"] = "development"
        response = client.post(
            "/api/v1/auth/token",
            json={"user_id": "test_user"}
        )
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_chat_message_validation(self, client, auth_headers):
        """Test chat message validation"""
        # Empty message
        response = client.post(
            "/api/v1/chat",
            json={"message": ""},
            headers=auth_headers
        )
        assert response.status_code == 422
        
        # Message too long
        response = client.post(
            "/api/v1/chat",
            json={"message": "x" * 10001},
            headers=auth_headers
        )
        assert response.status_code == 422
        
        # Invalid user_id
        response = client.post(
            "/api/v1/chat",
            json={"message": "test", "user_id": "invalid user!@#"},
            headers=auth_headers
        )
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
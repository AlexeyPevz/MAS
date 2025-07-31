"""
Comprehensive tests for MAS integration
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from tools.smart_groupchat import SmartGroupChatManager, Message
from agents.core_agents import MetaAgent, CoordinationAgent
from api.integration import MASAPIIntegration


class TestSmartGroupChatManager:
    """Tests for SmartGroupChatManager"""
    
    @pytest.fixture
    async def manager(self):
        """Create test manager instance"""
        manager = SmartGroupChatManager()
        await manager.initialize()
        return manager
    
    @pytest.mark.asyncio
    async def test_initialization(self, manager):
        """Test manager initialization"""
        assert manager._initialized is True
        assert len(manager.agents) > 0
        assert len(manager.routing) > 0
        assert "communicator" in manager.routing
    
    @pytest.mark.asyncio
    async def test_process_user_message(self, manager):
        """Test processing user message"""
        # Mock agent response
        with patch.object(manager, '_route_message_to_agent', return_value="Test response"):
            response = await manager.process_user_message("Hello, test!")
            assert response == "Test response"
            assert len(manager.conversation_history) == 1
    
    @pytest.mark.asyncio
    async def test_message_routing(self, manager):
        """Test message routing between agents"""
        test_message = Message(
            sender="user",
            recipient="meta",
            content="Test routing",
            timestamp=datetime.now()
        )
        
        # Mock agent
        mock_agent = Mock()
        mock_agent.generate_reply = Mock(return_value="Meta response")
        manager.agents["meta"] = mock_agent
        
        response = await manager._route_message_to_agent("meta", test_message)
        assert "response" in response.lower() or "meta" in response.lower()
        mock_agent.generate_reply.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_conversation_history(self, manager):
        """Test conversation history tracking"""
        await manager.process_user_message("Message 1")
        await manager.process_user_message("Message 2")
        
        summary = manager.get_conversation_summary()
        assert summary["total_messages"] >= 2
        assert "user" in summary["active_agents"]
    
    @pytest.mark.asyncio
    async def test_error_handling(self, manager):
        """Test error handling in message processing"""
        # Force an error
        with patch.object(manager, '_route_message_to_agent', side_effect=Exception("Test error")):
            response = await manager.process_user_message("Error test")
            assert "ошибка" in response.lower() or "error" in response.lower()


class TestAgentImplementations:
    """Tests for individual agent implementations"""
    
    def test_meta_agent_creation(self):
        """Test MetaAgent creation"""
        agent = MetaAgent()
        assert agent.name == "meta"
        assert agent.tier == "premium"
    
    def test_coordination_agent_creation(self):
        """Test CoordinationAgent creation"""
        agent = CoordinationAgent()
        assert agent.name == "coordination"
        assert agent.tier == "cheap"
    
    def test_agent_generate_reply(self):
        """Test agent reply generation"""
        agent = MetaAgent()
        reply = agent.generate_reply([{"content": "Test message"}])
        assert isinstance(reply, str)
        assert len(reply) > 0


class TestAPIIntegration:
    """Tests for API integration"""
    
    @pytest.fixture
    async def integration(self):
        """Create test integration instance"""
        integration = MASAPIIntegration()
        return integration
    
    @pytest.mark.asyncio
    async def test_initialization(self, integration):
        """Test API integration initialization"""
        await integration.initialize()
        assert integration._initialized is True
        assert integration.mas_manager is not None
    
    @pytest.mark.asyncio
    async def test_process_message(self, integration):
        """Test message processing through API"""
        await integration.initialize()
        
        with patch.object(integration.mas_manager, 'process_user_message', return_value="API response"):
            response = await integration.process_message("Test API message")
            assert response == "API response"
    
    @pytest.mark.asyncio
    async def test_get_agent_status(self, integration):
        """Test getting agent status"""
        await integration.initialize()
        
        with patch.object(integration.mas_manager, 'get_agent_statistics', return_value={"meta": 5}):
            status = integration.get_agent_status()
            assert isinstance(status, dict)
            assert "meta" in status


class TestEndToEndFlow:
    """End-to-end integration tests"""
    
    @pytest.mark.asyncio
    async def test_full_message_flow(self):
        """Test complete message flow from user to response"""
        # Create integration
        integration = MASAPIIntegration()
        await integration.initialize()
        
        # Process message
        response = await integration.process_message("Create a task: Test integration")
        
        # Verify response
        assert isinstance(response, str)
        assert len(response) > 0
        
        # Check that agents were involved
        stats = integration.get_agent_status()
        assert isinstance(stats, dict)


class TestPerformance:
    """Performance and load tests"""
    
    @pytest.mark.asyncio
    async def test_concurrent_messages(self):
        """Test handling multiple concurrent messages"""
        manager = SmartGroupChatManager()
        await manager.initialize()
        
        # Create multiple concurrent tasks
        tasks = []
        for i in range(10):
            task = manager.process_user_message(f"Concurrent message {i}")
            tasks.append(task)
        
        # Wait for all to complete
        responses = await asyncio.gather(*tasks)
        
        # Verify all got responses
        assert len(responses) == 10
        assert all(isinstance(r, str) for r in responses)
    
    @pytest.mark.asyncio
    async def test_memory_usage(self):
        """Test memory usage with large conversation history"""
        manager = SmartGroupChatManager()
        await manager.initialize()
        
        # Process many messages
        for i in range(100):
            await manager.process_user_message(f"Message {i}")
        
        # Check memory constraints
        assert len(manager.conversation_history) <= manager.max_conversation_length * 2
        
        # Verify old messages are cleaned up
        summary = manager.get_conversation_summary()
        assert summary["total_messages"] <= 100


# Fixtures for pytest
@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
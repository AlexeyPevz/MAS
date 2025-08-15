# Root-MAS Architecture

## Overview

Root-MAS is a self-learning, self-expanding, and proactive Multi-Agent System built on top of Microsoft AutoGen v0.5+. The system is designed to evolve and improve through real-world interactions.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                             │
├─────────────────┬──────────────────┬────────────────────────────┤
│   PWA (React)   │  Telegram Bot   │      REST API Clients      │
└────────┬────────┴────────┬─────────┴──────────┬─────────────────┘
         │                 │                    │
         └─────────────────┴────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway (FastAPI)                       │
│  ┌────────────┬──────────────┬─────────────┬───────────────┐  │
│  │   Auth     │   Rate Limit │    CORS     │   WebSocket   │  │
│  └────────────┴──────────────┴─────────────┴───────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MAS Integration Layer                         │
│  ┌────────────────────────┴─────────────────────────────────┐  │
│  │              SmartGroupChatManager                        │  │
│  └────────────────────────┬─────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Agents Layer                              │
│  ┌─────────────┬──────────────┬──────────────┬──────────────┐  │
│  │Communicator │     Meta     │ Coordination │  Researcher  │  │
│  ├─────────────┼──────────────┼──────────────┼──────────────┤  │
│  │Model Select │Prompt Builder│Agent Builder │ Fact Checker │  │
│  ├─────────────┼──────────────┼──────────────┼──────────────┤  │
│  │  MultiTool  │WorkflowBuild │ WebappBuild  │InstanceFactory│  │
│  └─────────────┴──────────────┴──────────────┴──────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Intelligence Layer                           │
│  ┌─────────────┬──────────────┬──────────────┬──────────────┐  │
│  │  Q-Learning │ A/B Testing  │Knowledge Graph│ Federation   │  │
│  ├─────────────┼──────────────┼──────────────┼──────────────┤  │
│  │Quality Metrics│Error Handler│Event Sourcing│Semantic Cache│  │
│  └─────────────┴──────────────┴──────────────┴──────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Storage Layer                               │
│  ┌─────────────┬──────────────┬──────────────┬──────────────┐  │
│  │    Redis    │  PostgreSQL  │   ChromaDB   │ File System  │  │
│  │  (Cache)    │ (Persistent) │  (Vectors)   │   (Logs)     │  │
│  └─────────────┴──────────────┴──────────────┴──────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. API Gateway (FastAPI)
- **Purpose**: Single entry point for all client interactions
- **Features**:
  - JWT-based authentication
  - Role-based access control (RBAC)
  - Rate limiting
  - WebSocket support for real-time communication
  - Request/response validation

### 2. MAS Integration Layer
- **SmartGroupChatManager**: Orchestrates agent communication
- **Features**:
  - Message routing based on agent capabilities
  - Context preservation across conversations
  - Parallel agent execution
  - Fallback mechanisms

### 3. Agent System
Each agent has specialized responsibilities:

#### Core Agents:
- **Communicator**: User interaction, intent understanding
- **Meta**: High-level planning and strategy
- **Coordination**: Task decomposition and delegation
- **Researcher**: Information gathering and validation

#### Specialized Agents:
- **ModelSelector**: Optimal LLM selection based on task
- **PromptBuilder**: Dynamic prompt optimization
- **AgentBuilder**: Runtime agent creation
- **FactChecker**: Information verification

#### Tool Agents:
- **MultiTool**: External API integration
- **WorkflowBuilder**: n8n workflow creation
- **WebappBuilder**: Application generation
- **InstanceFactory**: Component instantiation

### 4. Intelligence Layer
Advanced capabilities that make the system self-improving:

- **Q-Learning**: Reinforcement learning from interactions
- **A/B Testing**: Automatic prompt optimization
- **Knowledge Graph**: Semantic understanding of relationships
- **Federation**: Knowledge sharing between instances
- **Quality Metrics**: Performance tracking and optimization
- **Semantic Cache**: Intelligent response caching

### 5. Storage Layer
Multi-level persistence strategy:

- **Redis**: Short-term memory, rate limiting, cache
- **PostgreSQL**: Long-term memory, audit trails
- **ChromaDB**: Vector embeddings for semantic search
- **File System**: Logs, temporary files

## Data Flow

1. **Request Reception**: Client sends request to API Gateway
2. **Authentication**: JWT token validation and permission check
3. **Rate Limiting**: Request frequency validation
4. **Integration**: Request forwarded to MAS Integration Layer
5. **Orchestration**: SmartGroupChatManager determines agent routing
6. **Processing**: Agents collaborate to process request
7. **Intelligence**: Learning systems capture metrics and improve
8. **Response**: Result sent back through API Gateway

## Security Architecture

- **Authentication**: JWT with refresh tokens
- **Authorization**: Role-based (Admin, User, Agent, ReadOnly)
- **Encryption**: TLS for transport, bcrypt for passwords
- **Rate Limiting**: Per-IP and per-user limits
- **Input Validation**: Pydantic models for all inputs
- **Audit Trail**: Event sourcing for all actions

## Scalability Considerations

- **Horizontal Scaling**: Stateless API servers
- **Agent Pool**: Dynamic agent spawning based on load
- **Cache Strategy**: Multi-level caching (local, Redis, semantic)
- **Database Pooling**: Connection pooling for all databases
- **Message Queue**: Async task processing (future)

## Deployment Architecture

- **Containerization**: Docker for all components
- **Orchestration**: Docker Compose for development, K8s ready
- **Monitoring**: Prometheus metrics, Grafana dashboards
- **Logging**: Centralized JSON logging
- **Health Checks**: Liveness and readiness probes

# Architecture

## Technology Stack
- **Runtime**: Python 3.13 with async/await
- **Framework**: FastAPI for async REST APIs
- **Authentication**: OAuth2/OIDC with JWT tokens
- **Cache**: Redis for session and rate limiting
- **HTTP Client**: `httpx` for async Claude API calls
- **Validation**: Pydantic v2 for data models
- **Documentation**: Auto-generated OpenAPI/Swagger

## Architecture Pattern
- **Hexagonal Architecture** (Ports & Adapters)
- Clean separation between domain, application, infrastructure
- Dependency injection for testability
- Interface-based design for external dependencies

## Core Components
- **API Layer**: FastAPI routers and middleware
- **Service Layer**: Business logic and orchestration
- **Repository Layer**: Data access abstractions
- **Client Layer**: Claude API integration
- **Auth Layer**: JWT validation and user management
- **Cache Layer**: Redis-based caching and rate limiting

## Data Flow
- Client → API Gateway → Auth Middleware → Route Handler
- Handler → Service → Repository → External APIs
- Response caching at service layer
- Async streaming for real-time responses

## Security Architecture
- **JWT Bearer tokens** for API authentication
- **OAuth2 flows** (authorization code, client credentials)
- **Rate limiting** per user/API key
- **Request validation** with Pydantic schemas
- **CORS** configuration for web clients
- **API key rotation** support

## Integration Points
- **Claude API**: Primary AI service integration
- **Redis**: Cache and session storage
- **OAuth Provider**: External identity provider
- **Monitoring**: Structured logging and metrics
- **Health Checks**: Service dependency monitoring

## Performance Considerations
- **Async I/O** throughout the stack
- **Connection pooling** for external APIs
- **Response caching** with TTL strategies
- **Request debouncing** for similar queries
- **Streaming responses** for long operations
- **Background tasks** for non-critical operations

## Scalability Design
- **Stateless services** for horizontal scaling
- **Redis clustering** for cache scaling
- **Load balancer ready** (health checks)
- **Circuit breaker** pattern for external APIs
- **Queue-based** background processing
- **Database read replicas** support

## Database Design
- **No primary database** (API-first design)
- **Redis**: Session storage, rate limiting, cache
- **Optional PostgreSQL**: User preferences, audit logs
- **Schema versioning** for data migrations

## Caching Strategy
- **L1**: In-memory LRU cache for hot data
- **L2**: Redis distributed cache
- **TTL-based expiration** (5min-1hour)
- **Cache-aside** pattern with fallback
- **Invalidation**: Event-driven cache clearing
- **Compression**: JSON responses cached compressed
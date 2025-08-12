# Design Standards

## API Design Principles
- RESTful resource-based URLs
- HTTP verbs match operations (GET, POST, PUT, DELETE)
- Stateless request/response cycle
- Consistent JSON data formats
- Clear separation of concerns
- Idempotent operations where applicable

## Endpoint Patterns
- Noun-based resource URLs: `/api/v1/conversations`
- Collection vs item: `/conversations` vs `/conversations/{id}`
- Nested resources: `/conversations/{id}/messages`
- Action endpoints: `/conversations/{id}/complete`
- Query parameters for filtering: `?status=active&limit=50`
- Kebab-case for multi-word resources

## Request/Response Format
- JSON content type: `application/json`
- ISO 8601 timestamps: `2025-01-15T10:30:00Z`
- Snake_case field names: `created_at`, `user_id`
- Consistent pagination: `limit`, `offset`, `total_count`
- Envelope format: `{"data": {}, "meta": {}, "errors": []}`
- HTTP status codes match operation results

## Error Handling
- Standard HTTP status codes (400, 401, 403, 404, 422, 500)
- Consistent error object: `{"code": "VALIDATION_ERROR", "message": "...", "field": "email"}`
- Multiple validation errors in array format
- Rate limit headers: `X-RateLimit-Remaining`
- Error correlation IDs for tracking
- User-friendly messages vs developer details

## Authentication Flow
- Bearer token authentication: `Authorization: Bearer {token}`
- JWT tokens with expiration
- API key authentication for service-to-service
- OAuth 2.0 for user delegation
- Token refresh mechanism
- Scope-based permissions

## Rate Limiting
- Per-user rate limits: 1000 req/hour
- Per-endpoint specific limits
- Token bucket algorithm
- Rate limit headers in responses
- HTTP 429 for exceeded limits
- Exponential backoff recommendations

## Versioning Strategy
- URL path versioning: `/api/v1/`
- Semantic versioning principles
- Backward compatibility within major versions
- Deprecation notices with sunset dates
- Version header support: `Accept-Version: v1`
- Migration guides for breaking changes

## SDK Interface
- Method names match API operations: `client.conversations.create()`
- Async/await patterns for Python
- Type hints and dataclasses
- Automatic retry with backoff
- Configuration via environment variables
- Streaming response support

## WebSocket Design
- Connection endpoint: `/ws/v1/conversations/{id}`
- JSON message format with `type` field
- Event-driven message types: `message.created`, `conversation.updated`
- Heartbeat/ping-pong for connection health
- Authentication via query parameter or header
- Graceful reconnection handling

## Documentation Standards
- OpenAPI 3.1 specification
- Interactive Swagger UI
- Code examples in multiple languages
- Request/response schemas with examples
- Error code documentation
- Rate limit documentation
- SDK usage examples
- Postman collection available
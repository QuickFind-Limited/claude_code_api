# 📋 Claude SDK Server - Coding Rules & Standards

This directory contains comprehensive coding rules and standards for the Claude SDK Server project, organized by category. These rules are designed to work with the AIDD (AI-Driven Development) framework and are based on current best practices for Python 3.13, FastAPI, and cloud-native development.

## 📚 Rule Categories

### 00-architecture/
- **[0-hexagonal-architecture.mdc](00-architecture/0-hexagonal-architecture.mdc)** - Hexagonal Architecture (Ports & Adapters) patterns

### 01-standards/
- **[1-api-design.mdc](01-standards/1-api-design.mdc)** - RESTful API design standards and conventions
- **[1-code-organization.mdc](01-standards/1-code-organization.mdc)** - Code organization and project structure

### 02-programming-languages/
- **[2-python-313.mdc](02-programming-languages/2-python-313.mdc)** - Python 3.13 coding standards and best practices

### 03-frameworks-libraries/
- **[3-fastapi.mdc](03-frameworks-libraries/3-fastapi.mdc)** - FastAPI framework patterns and best practices
- **[3-pydantic-v2.mdc](03-frameworks-libraries/3-pydantic-v2.mdc)** - Pydantic v2 data validation patterns
- **[3-async-patterns.mdc](03-frameworks-libraries/3-async-patterns.mdc)** - Asynchronous programming patterns
- **[3-redis-caching.mdc](03-frameworks-libraries/3-redis-caching.mdc)** - Redis caching patterns and strategies

### 04-tools-configurations/
- **[4-docker-deployment.mdc](04-tools-configurations/4-docker-deployment.mdc)** - Docker containerization and deployment

### 05-workflows-processes/
- **[5-development-workflow.mdc](05-workflows-processes/5-development-workflow.mdc)** - Development workflow and processes

### 07-quality-assurance/
- **[7-testing-standards.mdc](07-quality-assurance/7-testing-standards.mdc)** - Comprehensive testing standards
- **[7-security-patterns.mdc](07-quality-assurance/7-security-patterns.mdc)** - Security patterns and best practices

### 08-domain-specific/
- **[8-claude-code-sdk-integration.mdc](08-domain-specific/8-claude-code-sdk-integration.mdc)** - Claude Code SDK Python integration

## 🎯 Key Focus Areas

### 1. **Architecture & Design**
- Hexagonal Architecture with clean separation of concerns
- Domain-driven design principles
- Dependency injection and interface-based design
- RESTful API standards with OpenAPI compliance

### 2. **Python & Async Programming**
- Python 3.13 features and type hints
- Async/await patterns for high-performance I/O
- Proper error handling and exception management
- Memory-efficient data structures

### 3. **FastAPI & Web Development**
- FastAPI best practices for REST APIs
- Pydantic v2 for data validation
- Server-sent events for streaming
- CORS and security configurations

### 4. **Claude Code SDK Integration**
- Claude Code SDK for AI-powered development
- Query patterns and session management
- Tool usage configuration
- Streaming responses and error handling

### 5. **Infrastructure & Deployment**
- Docker multi-stage builds
- Redis caching strategies
- Health checks and monitoring
- CI/CD integration

### 6. **Quality & Security**
- Comprehensive testing (unit, integration, e2e)
- Security patterns (JWT, OAuth2, input validation)
- Performance optimization
- Logging and observability

## 📖 Rule File Format

Each rule file follows this structure:

```markdown
---
description: Brief description of the rule set
globs: ["*.py", "**/*.py"]  # File patterns where rules apply
alwaysApply: true/false      # Whether to always apply these rules
---

## Section Name

- Rule statement (concise)
- Another rule statement
- Code references in `backticks`

```

## 🚀 Usage with AIDD

These rules integrate with the AIDD framework commands:

1. **Generate Rules**: `/generate_rules` - Create new rule files
2. **Load Rules**: Rules are automatically loaded during `/implement_plan`
3. **Validate**: Rules are checked during `/code_quality_review`

## 🔄 Continuous Improvement

Rules should be updated regularly based on:
- New Python/FastAPI releases
- Claude SDK updates
- Security advisories
- Performance findings
- Team feedback

## 📝 Contributing

When adding new rules:
1. Follow the existing file naming convention
2. Use the proper frontmatter format
3. Keep rules concise and actionable
4. Include code examples where helpful
5. Update this README index

## 🎯 Project-Specific Context

These rules are tailored for the **Claude SDK Server** project, which:
- Wraps Claude Code SDK functionality in HTTP endpoints
- Provides streaming responses via SSE
- Manages conversation sessions
- Handles file attachments
- Implements rate limiting and caching
- Follows hexagonal architecture

For more details, see:
- [Project Brief](../memory-bank/PROJECT_BRIEF.md)
- [PRD](../memory-bank/PRD.md)
- [Architecture](../memory-bank/ARCHITECTURE.md)
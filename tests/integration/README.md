# Integration Tests

This directory contains integration tests that run in the CI/CD pipeline before deployment.

## Test Files

- `test_api_health.py`: API health checks, endpoint existence, and basic functionality tests

## Running Tests Locally

```bash
# Install test dependencies
pip install pytest httpx

# Run all integration tests
pytest tests/integration/ -v

# Run with coverage
pytest tests/integration/ -v --cov=api --cov=agents
```

## CI/CD Integration

These tests are automatically run in the Cloud Build pipeline before deployment to ensure:
- API endpoints are accessible
- Health checks pass
- Database connectivity works (in staging/production)
- Basic workflows function correctly

## Environment Variables

- `API_BASE_URL`: Base URL for the API (default: http://localhost:8000)
- `ENVIRONMENT`: test/staging/production (affects which tests run)

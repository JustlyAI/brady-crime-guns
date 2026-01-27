# System Health Check Commands for Compliagent Monorepo

# This script runs a series of health checks for the core infrastructure services.

# Run each command and report the output for debugging and verification.

# 1. Check that the Postgres database and tables exist

echo "🔍 Checking Postgres database tables..."
docker exec -it compli-news-agent-postgres-1 psql -U compliagent_user -d compliagent -c '\dt'

# 2. Verify Redis is operational and rate limiting is functional

echo "🔍 Testing Redis rate limiting key set/get..."
docker exec -it compli-news-agent-redis-1 redis-cli SETEX test:key 10 "working"
docker exec -it compli-news-agent-redis-1 redis-cli GET test:key

# 3. Confirm MinIO bucket for newsletters exists

echo "🔍 Checking MinIO bucket 'compliagent-newsletters' exists..."
curl -s http://localhost:9000/compliagent-newsletters/ -H "Host: localhost:9000" | head -n 1

# 4. Test API health endpoint to ensure all dependencies are loaded

echo "🔍 Testing API /health endpoint..."
curl http://localhost:8000/health

# 5. (Optional) If running locally with uvicorn, use:

# uvicorn compliagent_api.main:app --reload --app-dir src --port 8000

# Please copy and paste the output of each command above for review.
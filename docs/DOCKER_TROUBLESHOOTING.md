# Docker Troubleshooting Guide

## Common Issues and Solutions

### Issue: TLS Handshake Timeout / Network Issues

**Symptoms:**
```
failed to solve: python:3.11-slim: failed to resolve source metadata
net/http: TLS handshake timeout
```

**Solution 1: Retry with BuildKit disabled**

```bash
DOCKER_BUILDKIT=0 docker compose build
```

**Solution 2: Pull image manually first**

```bash
docker pull python:3.11-slim
docker compose build
```

**Solution 3: Increase timeout in Docker Desktop**

1. Docker Desktop → Settings → Docker Engine
2. Add:
```json
{
  "max-concurrent-downloads": 1,
  "max-concurrent-uploads": 1
}
```
3. Apply & Restart

**Solution 4: Check network/proxy settings**

1. Docker Desktop → Settings → Resources → Proxies
2. Configure if behind corporate firewall
3. Or disable proxy if not needed

**Solution 5: Use alternative registry/mirror**

If Docker Hub is blocked, configure a mirror in Docker Desktop settings.

**Solution 6: Check DNS**

```bash
# Flush DNS cache (macOS)
sudo dscacheutil -flushcache

# Test DNS
nslookup registry-1.docker.io
```

**Solution 7: Retry with verbose output**

```bash
docker compose build --progress=plain --no-cache
```

---

### Issue: "docker-credential-desktop: executable file not found in $PATH"

**Symptoms:**
```
error getting credentials - err: exec: "docker-credential-desktop": executable file not found in $PATH
```

**Solution 1: Add Docker Desktop bin to PATH (Recommended)**

Add this to your `~/.zshrc` or `~/.bashrc`:

```bash
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
```

Then reload your shell:
```bash
source ~/.zshrc  # or source ~/.bashrc
```

**Solution 2: Remove credential helper (for public images only)**

If you're only using public Docker images, you can remove the credential helper:

```bash
# Run the fix script
./scripts/fix_docker_credentials.sh

# Or manually edit ~/.docker/config.json
# Remove the "credsStore": "desktop" line
```

**Solution 3: Restart Docker Desktop**

Sometimes Docker Desktop needs to be restarted:
1. Quit Docker Desktop completely
2. Restart Docker Desktop
3. Try again

**Solution 4: Reinstall Docker Desktop**

If the above don't work, reinstall Docker Desktop:
1. Uninstall Docker Desktop
2. Download and install the latest version
3. Restart your computer

---

### Issue: Port Already in Use

**Symptoms:**
```
Error: bind: address already in use
```

**Solution:**

1. Find what's using the port:
```bash
# For port 8000
lsof -i :8000

# For port 8501
lsof -i :8501
```

2. Kill the process or change the port in `docker-compose.yml`:
```yaml
ports:
  - "8001:8000"  # Changed from 8000:8000
```

---

### Issue: Permission Denied on Volumes

**Symptoms:**
```
Permission denied: /app/data
```

**Solution:**

Fix directory permissions:
```bash
mkdir -p data/vectordb data/sessions logs
chmod -R 755 data logs
```

Or if using Docker Desktop, ensure the directories are shared:
1. Docker Desktop → Settings → Resources → File Sharing
2. Add your project directory

---

### Issue: Services Not Starting

**Symptoms:**
```
Container keeps restarting
```

**Solution:**

1. Check logs:
```bash
docker compose logs api
docker compose logs db
```

2. Check health status:
```bash
docker compose ps
```

3. Verify environment variables:
```bash
docker compose config
```

4. Check if services are healthy:
```bash
./scripts/docker_health_check.sh
```

---

### Issue: Database Connection Failed

**Symptoms:**
```
could not connect to server: Connection refused
```

**Solution:**

1. Verify database is running:
```bash
docker compose ps db
```

2. Check database logs:
```bash
docker compose logs db
```

3. Wait for database to be ready:
```bash
# Database health check should pass
docker compose ps db
```

4. Test connection:
```bash
docker compose exec db psql -U postgres -d interview_copilot -c "SELECT 1;"
```

---

### Issue: Out of Memory

**Symptoms:**
```
Container killed (OOM)
```

**Solution:**

1. Increase Docker memory limit:
   - Docker Desktop → Settings → Resources → Advanced
   - Increase Memory to at least 4GB

2. Reduce resource usage:
   - Edit `docker-compose.prod.yml` to reduce limits
   - Or use development mode: `docker-compose.dev.yml`

3. Stop unused containers:
```bash
docker ps -a
docker stop <container_id>
docker rm <container_id>
```

---

### Issue: Build Fails

**Symptoms:**
```
ERROR: failed to solve: ...
```

**Solution:**

1. Clean build cache:
```bash
docker compose build --no-cache
```

2. Check Dockerfile syntax:
```bash
docker build --dry-run -f Dockerfile .
```

3. Verify requirements.txt:
```bash
pip install -r requirements.txt  # Test locally first
```

---

### Issue: Images Not Found

**Symptoms:**
```
Error: image not found
```

**Solution:**

1. Build images first:
```bash
docker compose build
```

2. Or pull images:
```bash
docker compose pull
```

---

### Issue: Network Issues

**Symptoms:**
```
Cannot connect to service
```

**Solution:**

1. Check network:
```bash
docker network ls
docker network inspect interview-copilot-network
```

2. Recreate network:
```bash
docker compose down
docker compose up -d
```

---

### Issue: Health Checks Failing

**Symptoms:**
```
Health check failed
```

**Solution:**

1. Check service logs:
```bash
docker compose logs api
```

2. Test health endpoint manually:
```bash
curl http://localhost:8000/health
```

3. Increase health check timeout in `docker-compose.yml`:
```yaml
healthcheck:
  interval: 30s
  timeout: 20s  # Increased from 10s
  retries: 5    # Increased from 3
```

---

## Quick Diagnostic Commands

```bash
# Check Docker version
docker --version
docker compose version

# Check running containers
docker compose ps

# Check logs
docker compose logs -f

# Check resource usage
docker stats

# Check disk usage
docker system df

# Clean up unused resources
docker system prune -a
```

## Getting Help

If issues persist:

1. Check Docker Desktop logs:
   - Docker Desktop → Troubleshoot → View logs

2. Check container logs:
   ```bash
   docker compose logs > docker-logs.txt
   ```

3. Verify configuration:
   ```bash
   ./scripts/test_docker.sh
   ```

4. Check system resources:
   ```bash
   docker stats
   ```

## Prevention Tips

1. **Keep Docker Desktop updated**
2. **Regularly clean up unused images/containers**
3. **Monitor resource usage**
4. **Use .env file for configuration**
5. **Keep docker-compose files in version control**
6. **Test locally before deploying**


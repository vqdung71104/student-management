# 🚀 Pre-Deployment Checklist

## ✅ Development Environment

### Initial Setup
- [ ] Docker Desktop installed and running
- [ ] Docker version >= 20.10.0
- [ ] Docker Compose version >= 2.0.0
- [ ] At least 4GB RAM available
- [ ] At least 10GB disk space available

### Configuration
- [ ] Copied `.env.docker` and reviewed settings
- [ ] Updated `GOOGLE_API_KEY` in `.env.docker`
- [ ] Reviewed `docker-compose.yml` configuration
- [ ] Checked port availability (5173, 8000, 3306, 8080)

### First Run
- [ ] Run `.\docker-manager.ps1 dev:start` (Windows) or `make dev-start` (Linux/Mac)
- [ ] Wait for all services to start (30-60 seconds)
- [ ] Run health check: `.\healthcheck.ps1` or `./healthcheck.sh`
- [ ] Access frontend: http://localhost:5173
- [ ] Access backend: http://localhost:8000
- [ ] Access API docs: http://localhost:8000/docs
- [ ] Check logs: `.\docker-manager.ps1 dev:logs`

### Testing
- [ ] Test user registration
- [ ] Test user login
- [ ] Test student CRUD operations
- [ ] Test chatbot functionality
- [ ] Test Excel export
- [ ] Check database in phpMyAdmin (http://localhost:8080)

## ✅ Production Deployment

### Security
- [ ] **CRITICAL**: Change `MYSQL_PASSWORD` in `.env.production`
- [ ] **CRITICAL**: Generate new `SECRET_KEY` using:
  ```bash
  # Linux/Mac
  openssl rand -hex 32
  
  # Windows PowerShell
  [System.Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
  ```
- [ ] Update `GOOGLE_API_KEY` with production key
- [ ] Review all environment variables in `.env.production`
- [ ] Ensure `.env.production` is NOT committed to git
- [ ] Set strong MySQL root password
- [ ] Configure firewall rules

### Configuration
- [ ] Update `VITE_API_URL` with production domain
- [ ] Configure domain/DNS settings
- [ ] Set up SSL/TLS certificates
- [ ] Configure reverse proxy (if needed)
- [ ] Review Nginx configuration in `frontend/nginx.conf`
- [ ] Set appropriate `ACCESS_TOKEN_EXPIRE_MINUTES`

### Database
- [ ] Database backup strategy in place
- [ ] Test database backup: `.\docker-manager.ps1 db:backup`
- [ ] Test database restore: `.\docker-manager.ps1 db:restore backup_file.sql`
- [ ] Configure automated backups (cron/scheduled task)
- [ ] Plan for database migrations

### Build & Deploy
- [ ] Build production images: `.\docker-manager.ps1 prod:build`
- [ ] Review build logs for errors
- [ ] Test production build locally first
- [ ] Start production: `.\docker-manager.ps1 prod:start`
- [ ] Run health check: `.\healthcheck.ps1`
- [ ] Check all services are running: `docker-compose -f docker-compose.prod.yml ps`

### Monitoring
- [ ] Set up log monitoring
- [ ] Configure health check endpoints
- [ ] Set up uptime monitoring
- [ ] Configure alerts for service failures
- [ ] Monitor disk space usage
- [ ] Monitor memory usage
- [ ] Monitor CPU usage

### Performance
- [ ] Test application under load
- [ ] Optimize database queries
- [ ] Configure database connection pooling
- [ ] Enable Nginx caching
- [ ] Configure CDN (if needed)
- [ ] Optimize image sizes

### Backup & Recovery
- [ ] Document backup procedures
- [ ] Test disaster recovery plan
- [ ] Store backups in secure location
- [ ] Set up automated backup rotation
- [ ] Document restore procedures

## ✅ Post-Deployment

### Verification
- [ ] Access production URL
- [ ] Test all critical features
- [ ] Verify SSL certificate
- [ ] Check API documentation access
- [ ] Test user authentication
- [ ] Verify database connections
- [ ] Check logs for errors

### Documentation
- [ ] Update README with production URL
- [ ] Document deployment process
- [ ] Create runbook for common issues
- [ ] Document rollback procedures
- [ ] Share credentials securely with team

### Maintenance
- [ ] Schedule regular updates
- [ ] Plan for security patches
- [ ] Set up monitoring alerts
- [ ] Create maintenance window schedule
- [ ] Document scaling procedures

## 🔧 Troubleshooting Checklist

### Services Not Starting
- [ ] Check Docker is running
- [ ] Check port conflicts: `netstat -ano | findstr :8000`
- [ ] Review logs: `docker-compose logs`
- [ ] Check disk space: `docker system df`
- [ ] Verify environment variables

### Database Connection Issues
- [ ] Verify MySQL container is running
- [ ] Check MySQL logs: `docker-compose logs mysql`
- [ ] Verify credentials in `.env` file
- [ ] Wait for MySQL health check (30-60 seconds)
- [ ] Test connection: `docker-compose exec mysql mysql -u root -p`

### Frontend Not Loading
- [ ] Check frontend container status
- [ ] Review Nginx logs: `docker-compose logs frontend`
- [ ] Verify build completed successfully
- [ ] Check browser console for errors
- [ ] Clear browser cache

### Backend API Errors
- [ ] Check backend logs: `docker-compose logs backend`
- [ ] Verify database connection
- [ ] Check Python dependencies
- [ ] Review API error messages
- [ ] Test API endpoints directly

## 📋 Quick Commands Reference

### Development
```bash
# Windows
.\docker-manager.ps1 dev:start
.\docker-manager.ps1 dev:logs
.\docker-manager.ps1 dev:stop
.\healthcheck.ps1

# Linux/Mac
make dev-start
make dev-logs
make dev-stop
./healthcheck.sh
```

### Production
```bash
# Windows
.\docker-manager.ps1 prod:build
.\docker-manager.ps1 prod:start
.\docker-manager.ps1 prod:stop

# Linux/Mac
make prod-build
make prod-start
make prod-stop
```

### Database
```bash
# Windows
.\docker-manager.ps1 db:backup
.\docker-manager.ps1 db:restore backup.sql
.\docker-manager.ps1 db:shell

# Linux/Mac
make db-backup
make db-restore FILE=backup.sql
make db-shell
```

## 🆘 Emergency Procedures

### Complete Reset
```bash
# WARNING: This will delete all data!
# Windows
.\docker-manager.ps1 cleanup

# Linux/Mac
make cleanup
```

### Rollback Deployment
```bash
# Stop current deployment
docker-compose -f docker-compose.prod.yml down

# Restore database backup
.\docker-manager.ps1 db:restore backup_before_deployment.sql

# Start previous version
docker-compose -f docker-compose.prod.yml up -d
```

### View All Logs
```bash
docker-compose logs --tail=100 -f
```

---

**Remember**: Always test in development before deploying to production! 🚀

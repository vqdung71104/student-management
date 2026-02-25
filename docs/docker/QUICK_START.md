# Quick Start Guide

## Development

```bash
# Windows PowerShell
.\docker-manager.ps1 dev:start

# Linux/Mac
make dev-start
# or
./docker-manager.sh dev:start
```

## Production

```bash
# 1. Update .env.production with your credentials
# 2. Build and start

# Windows
.\docker-manager.ps1 prod:build
.\docker-manager.ps1 prod:start

# Linux/Mac
make prod-build
make prod-start
```

## Common Commands

| Task | Windows | Linux/Mac |
|------|---------|-----------|
| Start Dev | `.\docker-manager.ps1 dev:start` | `make dev-start` |
| Stop Dev | `.\docker-manager.ps1 dev:stop` | `make dev-stop` |
| View Logs | `.\docker-manager.ps1 dev:logs` | `make dev-logs` |
| Backup DB | `.\docker-manager.ps1 db:backup` | `make db-backup` |
| Health Check | `.\docker-manager.ps1 health` | `make health` |

See [DOCKER_GUIDE.md](DOCKER_GUIDE.md) for detailed documentation.

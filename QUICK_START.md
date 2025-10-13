# ⚡ ValueVerse Quick Start

## One-Command Deployment

Choose your platform:

### Linux/macOS
```bash
make deploy
```

### Windows (PowerShell)
```powershell
.\deploy.ps1
```

### Alternative (All platforms)
```bash
./deploy.sh
```

---

## Access Your Application

After deployment (3-5 minutes), access:

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

---

## Essential Commands

```bash
make status    # Check if services are running
make logs      # View logs
make restart   # Restart services
make stop      # Stop services
make clean     # Remove everything
```

---

## Prerequisites

✅ Docker Desktop installed and running
✅ 4GB+ RAM available
✅ 10GB+ disk space

[Install Docker](https://docs.docker.com/get-docker/)

---

## Troubleshooting

**Problem:** Port already in use
```bash
make clean
make deploy
```

**Problem:** Docker not running
- Start Docker Desktop
- Wait for it to fully start
- Run `make deploy` again

**Problem:** Services unhealthy
```bash
make logs        # Check for errors
make rebuild     # Rebuild from scratch
```

---

## Full Documentation

See [DEPLOYMENT.md](./DEPLOYMENT.md) for complete details.

---

**That's it!** Your application should be running. 🎉

# ValueVerse Dev Container - Quick Start Guide

## 🚀 Get Up and Running in 5 Minutes

This guide will help you get the ValueVerse development environment running as quickly as possible.

## Prerequisites Checklist

Before you start, make sure you have:

- [ ] **Visual Studio Code** installed ([Download](https://code.visualstudio.com/))
- [ ] **Docker Desktop** running ([Download](https://www.docker.com/products/docker-desktop))
- [ ] **Dev Containers extension** installed in VS Code ([Install](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers))

## Step-by-Step Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-org/valueverse.git
cd valueverse
```

### Step 2: Copy the Dev Container Configuration

If the `.devcontainer` folder is not already in the repository, extract it:

```bash
tar -xzf valueverse-devcontainer.tar.gz
```

### Step 3: Open in VS Code

```bash
code .
```

### Step 4: Reopen in Container

When VS Code opens, you'll see a notification in the bottom-right corner:

> "Folder contains a Dev Container configuration file. Reopen folder to develop in a container."

Click **"Reopen in Container"**.

Alternatively, press `F1` and select **"Dev Containers: Reopen in Container"**.

### Step 5: Wait for the Build

The first time you open the project, Docker will:
1. Build the development container (3-5 minutes)
2. Install all dependencies
3. Set up the database and Redis
4. Configure VS Code extensions

**Grab a coffee! ☕** Subsequent starts will be much faster (10-20 seconds).

### Step 6: Verify the Setup

Once the container is running, open a new terminal in VS Code (`Ctrl+` ` or `View → Terminal`) and run:

```bash
# Check Python
python3 --version
# Should show: Python 3.11.x

# Check Node.js
node --version
# Should show: v22.x.x

# Check database connection
psql -h db -U user -d valuedb -c "SELECT version();"
# Password: password
```

If all commands work, you're ready to code! 🎉

## Running the Application

### Start the Backend

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open [http://localhost:8000/docs](http://localhost:8000/docs) to see the API documentation.

### Start the Frontend

Open a new terminal and run:

```bash
cd frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to see the application.

## Common Commands

| Task | Command |
|------|---------|
| Install Python packages | `pip3 install --user package-name` |
| Install Node packages | `npm install package-name` |
| Run Python tests | `pytest` |
| Run frontend tests | `npm test` |
| Format Python code | `black .` |
| Format TypeScript code | `npm run format` |
| Access database | `psql -h db -U user -d valuedb` |
| Access Redis | `redis-cli -h redis` |

## Troubleshooting

### "Docker is not running"

1. Open Docker Desktop
2. Wait for it to fully start (green icon)
3. Try again

### "Cannot connect to database"

```bash
# Check if services are running
docker-compose ps

# Restart services if needed
docker-compose restart db redis
```

### "Extension not working"

```bash
# Reload VS Code window
# Press F1 → "Developer: Reload Window"
```

### "Out of disk space"

```bash
# Clean up Docker
docker system prune -a
```

## Next Steps

- [ ] Read the [full README](.devcontainer/README.md) for detailed documentation
- [ ] Review the [coding guidelines](../coding_rules_final.md)
- [ ] Set up your environment variables (copy `.env.example` to `.env`)
- [ ] Join the team Slack channel for support

## Getting Help

- **Documentation:** Check `.devcontainer/README.md`
- **Issues:** Search existing issues or create a new one
- **Team:** Ask in the #dev-support Slack channel

---

**Welcome to the team! Happy coding! 🚀**


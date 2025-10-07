# ChemTutor Deployment Guide

## Table of Contents
- [Prerequisites](#prerequisites)
- [Local Development Setup](#local-development-setup)
- [Environment Configuration](#environment-configuration)
- [Building the Knowledge Base](#building-the-knowledge-base)
- [Running the Application](#running-the-application)
- [Production Deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software
- **Python 3.10+**
- **Ollama** (for local LLM)
- **Node.js 16+** (optional, for future build tools)

### Required Services
- **OpenAI API Key** (for TTS/STT)

### System Requirements
- **RAM:** 8GB minimum (16GB recommended)
- **Storage:** 10GB free space
- **GPU:** Optional (for faster LLM inference)

---

## Local Development Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd chemtutor
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Install Ollama
Download and install Ollama from [ollama.ai](https://ollama.ai)

### 5. Pull Required Models
```bash
# LLM Model
ollama pull qwen2.5:14b
# OR use a lighter model
ollama pull mistral

# Embedding Model
ollama pull nomic-embed-text
```

---

## Environment Configuration

### 1. Copy Environment Template
```bash
cp .env.template .env
```

### 2. Configure Environment Variables

Edit `.env` with your settings:

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_DEFAULT_VOICE=alloy
OPENAI_TTS_MODEL=tts-1

# Ollama Configuration
OLLAMA_URL=http://localhost:11434/api/chat
LLM_MODEL=qwen2.5:14b
EMBED_MODEL=nomic-embed-text

# RAG Configuration
RAG_TOP_K=3
RAG_MAX_CONTEXT_LENGTH=300

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=True

# CORS Configuration
CORS_ORIGINS=*

# LLM Generation Configuration
LLM_TEMPERATURE=0.8
LLM_STREAM=True
```

---

## Building the Knowledge Base

### 1. Prepare Your Documents
Place PDF documents in `rag-system/data/`:
```bash
mkdir -p rag-system/data
cp /path/to/your/textbooks/*.pdf rag-system/data/
```

### 2. Build the FAISS Index
```bash
cd rag-system
python indexer.py data/ --directory
```

This will:
- Extract text from all PDFs
- Split text into chunks
- Generate embeddings using `nomic-embed-text`
- Save FAISS index to `vectorstore/`

### 3. Verify Index Creation
```bash
ls -la vectorstore/
# Should see: index.faiss and index.pkl
```

---

## Running the Application

### Development Mode

#### Start Backend Server
```bash
# From project root
python backend/app.py
```

The server will start on `http://localhost:8000`

#### Access Frontend
Open your browser to:
```
http://localhost:8000
```

### Production Mode (Coming Soon)
```bash
# Build optimized frontend
npm run build

# Run with production WSGI server
gunicorn backend.app:create_app() --bind 0.0.0.0:8000
```

---

## Production Deployment

### Using Docker (Recommended)

#### 1. Build Docker Image
```dockerfile
# Dockerfile example
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "backend/app.py"]
```

```bash
docker build -t chemtutor .
docker run -p 8000:8000 --env-file .env chemtutor
```

#### 2. Using Docker Compose
```yaml
version: '3.8'
services:
  chemtutor:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./rag-system:/app/rag-system
      - ./prompts:/app/prompts
    env_file:
      - .env
```

```bash
docker-compose up -d
```

### Using Systemd (Linux)

#### 1. Create Service File
```bash
sudo nano /etc/systemd/system/chemtutor.service
```

```ini
[Unit]
Description=ChemTutor Backend Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/chemtutor
Environment="PATH=/opt/chemtutor/venv/bin"
ExecStart=/opt/chemtutor/venv/bin/python backend/app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

#### 2. Enable and Start Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable chemtutor
sudo systemctl start chemtutor
sudo systemctl status chemtutor
```

### Using Nginx (Reverse Proxy)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # WebSocket support for streaming
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## Troubleshooting

### Common Issues

#### 1. RAG Index Not Found
**Error:** `[RAG index not available]`

**Solution:**
```bash
cd rag-system
python indexer.py data/ --directory
```

#### 2. Ollama Connection Failed
**Error:** `Connection refused to localhost:11434`

**Solution:**
- Ensure Ollama is running: `ollama serve`
- Check if models are pulled: `ollama list`

#### 3. OpenAI API Errors
**Error:** `OpenAI API key not configured`

**Solution:**
- Verify `.env` file has `OPENAI_API_KEY`
- Check API key is valid on OpenAI dashboard

#### 4. Import Errors
**Error:** `ModuleNotFoundError: No module named 'backend'`

**Solution:**
```bash
# Add project root to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/chemtutor"

# Or install in development mode
pip install -e .
```

#### 5. Frontend Not Loading
**Error:** 404 errors for static files

**Solution:**
- Check `FRONTEND_PATH` in `backend/config.py`
- Verify files exist in `frontend/src/`

### Performance Optimization

#### 1. Use GPU for Faster Inference
```bash
# Install CUDA-enabled PyTorch
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# Use GPU-enabled FAISS
pip uninstall faiss-cpu
pip install faiss-gpu
```

#### 2. Reduce Model Size
Use quantized models for lower memory usage:
```bash
ollama pull mistral:7b-instruct-q4_0
```

#### 3. Enable Caching
Add response caching in production for frequently asked questions.

### Logging

Enable detailed logging for debugging:
```python
# In backend/app.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Health Checks

Monitor service health:
```bash
curl http://localhost:8000/api/health
```

---

## Security Considerations

### For Production:
1. **Remove DEBUG mode** - Set `DEBUG=False` in `.env`
2. **Secure API keys** - Use environment variables, never commit to git
3. **Add authentication** - Implement user authentication for API access
4. **Rate limiting** - Add rate limiting to prevent abuse
5. **HTTPS** - Use SSL/TLS certificates (Let's Encrypt)
6. **CORS restrictions** - Limit CORS origins to specific domains
7. **Input validation** - Validate all user inputs
8. **Update dependencies** - Regularly update packages for security patches

---

## Monitoring

### Recommended Tools:
- **Application:** Prometheus + Grafana
- **Logs:** ELK Stack (Elasticsearch, Logstash, Kibana)
- **Uptime:** UptimeRobot or Pingdom

### Metrics to Monitor:
- API response times
- LLM inference latency
- RAG retrieval performance
- Memory usage
- Disk space (for vector index)
- Error rates

---

## Backup and Maintenance

### Regular Backups:
```bash
# Backup vector index
tar -czf vectorstore-backup-$(date +%Y%m%d).tar.gz rag-system/vectorstore/

# Backup configuration
cp .env .env.backup
```

### Updates:
```bash
# Update dependencies
pip install --upgrade -r requirements.txt

# Update Ollama models
ollama pull qwen2.5:14b
```

---

## Support

For issues and questions:
- Create an issue on GitHub
- Check existing documentation
- Review logs for error messages


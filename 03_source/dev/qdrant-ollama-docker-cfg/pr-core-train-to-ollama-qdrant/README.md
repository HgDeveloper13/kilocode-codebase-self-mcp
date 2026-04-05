# ASP.NET Core Embedding Gateway with Redis Cache

## Overview

Architecture: Client → Nginx → (Gateway for embeddings, Ollama directly for chat/generate, Qdrant directly)

- Gateway handles `/api/embed` and `/api/embeddings` with Redis caching
- All other Ollama endpoints go directly to Ollama
- Qdrant is untouched (uses existing config.yaml)

## Architecture Diagram

```
Client → Nginx (:11434, :6333, :6334)
           ├── /api/embed, /api/embeddings → Gateway (:11435) → Redis → Ollama
           ├── /api/chat, /api/generate → Ollama напрямую
           └── Qdrant REST/gRPC → Qdrant напрямую
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| Nginx | 11434, 6333, 6334, 80, 443 | Reverse proxy (entry point) |
| Ollama | internal:11434 | LLM inference |
| Qdrant | internal:6333, 6334 | Vector database |
| Gateway | internal:11435 | Embedding proxy with Redis cache |
| Redis | internal:6379 | Embedding cache (256mb LRU) |

## Quick Start

```bash
cd qdrant-ollama-docker-cfg/pr-core-train-to-ollama-qdrant
docker compose up -d
```

## How Embedding Caching Works

1. Client sends POST to `http://localhost:11434/api/embed`
2. Nginx routes to Gateway at `http://gateway:11435/api/embed`
3. Gateway generates SHA256 hash from request body
4. Checks Redis for cached result (key: `emb:{hash}`)
5. Cache hit → returns from Redis immediately
6. Cache miss → forwards to Ollama, caches result (7 days TTL), returns to client

## Configuration

- Qdrant config: `./qdrant/config.yaml` (unchanged from original)
- Nginx config: `./nginx/nginx.conf` (updated with gateway routing)
- Gateway env vars: `Ollama__Url`, `Redis__Host`, `Redis__Port`

## Health Check

```bash
curl http://localhost:11434/api/embed/health  # Won't work - health is on gateway port
# Gateway is internal only, accessed through Nginx routing
```

## Troubleshooting

- Check logs: `docker compose logs -f gateway`
- Check Redis: `docker exec -it redis-cache redis-cli`
- Test embedding: `curl -X POST http://localhost:11434/api/embed -H "Content-Type: application/json" -d '{"model":"nomic-embed-text","prompt":"test"}'`

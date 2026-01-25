# FastAPI with Swagger Documentation

## ✅ FastAPI Server Running!

The Silver Prediction Agent API is now running with **full Swagger documentation** enabled.

### Access Points

| Interface | URL | Description |
|-----------|-----|-------------|
| **Swagger UI** | http://localhost:8000/docs | Interactive API documentation |
| **ReDoc** | http://localhost:8000/redoc | Alternative documentation UI |
| **OpenAPI JSON** | http://localhost:8000/openapi.json | OpenAPI spec file |
| **Root** | http://localhost:8000 | API information |

### Available Endpoints

#### General
- `GET /` - Root endpoint with API info
- `GET /health` - Health check

#### Collection
- `POST /api/trigger` - Manually trigger collection with custom budget

#### Monitoring
- `GET /api/status` - Get system status and uptime
- `GET /api/metrics` - View quality metrics for all sources

#### Data
- `GET /api/freshness` - Check fresh vs stale data counts
- `GET /api/data/fresh` - Get all fresh price and news data

#### Watchdog
- `POST /api/watchdog/start` - Start automatic monitoring
- `POST /api/watchdog/stop` - Stop monitoring
- `GET /api/watchdog/status` - Check watchdog status

### How to Use Swagger UI

1. **Open in Browser**: Navigate to `http://localhost:8000/docs`

2. **Explore Endpoints**: All endpoints are organized by tags:
   - General
   - Collection
   - Monitoring
   - Data
   - Watchdog

3. **Try It Out**:
   - Click on any endpoint
   - Click "Try it out"
   - Fill in parameters (if any)
   - Click "Execute"
   - See the response!

4. **View Models**: Scroll down to see all Pydantic models with schemas

### Example: Trigger Collection

Using Swagger UI:
```
1. Go to http://localhost:8000/docs
2. Find "POST /api/trigger" under "Collection"
3. Click "Try it out"
4. Enter budget (e.g., 10)
5. Click "Execute"
6. See the collection plan response
```

Using curl:
```bash
curl -X POST "http://localhost:8000/api/trigger?budget=10"
```

Using Python:
```python
import requests

response = requests.post("http://localhost:8000/api/trigger", params={"budget": 10})
print(response.json())
```

### Response Models

All responses use Pydantic models for validation:

**TriggerResponse**:
```json
{
  "success": true,
  "message": "Collection triggered with budget of 10 calls",
  "timestamp": "2026-01-25T02:23:15",
  "collection_plan": {
    "should_collect": true,
    "sources": [...]
  }
}
```

**StatusResponse**:
```json
{
  "status": "running",
  "watchdog_running": false,
  "last_collection": null,
  "uptime_seconds": 120.5
}
```

### Stopping the Server

Press `Ctrl+C` in the terminal where it's running.

### Restarting

```bash
python run_api.py
```

The server has auto-reload enabled, so code changes will automatically restart it.

---

## Features

✅ **Automatic Documentation** - Swagger UI and ReDoc
✅ **Request Validation** - Pydantic models
✅ **CORS Enabled** - For frontend integration
✅ **Type Safety** - Full type hints
✅ **Auto-Reload** - Development mode
✅ **Error Handling** - HTTP exceptions with details

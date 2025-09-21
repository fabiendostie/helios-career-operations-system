# HELIOS Career Operations System - API Documentation

## 📚 Complete API Documentation Suite

This directory contains comprehensive API documentation for all HELIOS services, generated using pydoc and enhanced with cross-service integration guides.

### 🚀 Quick Access

- **[Main Documentation Index](index.html)** - Complete service overview with links to all modules
- **[Cross-Service API Reference](cross-service-reference.html)** - Integration patterns and service communication
- **[Verified Endpoints Summary](verified-endpoints-summary.md)** - Operational endpoint status

### 📦 Service Documentation

| Service | Status | Port | Documentation |
|---------|--------|------|---------------|
| **Profile Ingestor** | ✅ Operational | 8001 | [profile-ingestor/](profile-ingestor/) |
| **HELIOS Orchestrator** | ✅ Operational | 8000 | [orchestrator/](orchestrator/) |
| **Strategist Agent** | ✅ Operational | 8002 | [strategist/](strategist/) |
| **Analyst Agent** | ✅ Operational | 8003 | [analyst/](analyst/) |
| **Architect Agent** | ✅ Operational | 8004 | [architect/](architect/) |
| **Editor Agent** | ✅ Operational | 8005 | [editor/](editor/) |
| **Shared LLM Client** | 🔧 Library | N/A | [shared/](shared/) |

### 🔧 Development Tools

#### Local Documentation Server
```bash
# Start local documentation server (opens browser automatically)
python scripts/serve_docs.py

# Start on custom port
python scripts/serve_docs.py --port 9000

# Check documentation status
python scripts/serve_docs.py --check
```

#### Regenerate Documentation
```bash
# Generate all API documentation
python scripts/generate_docs.py

# Update configuration
# Edit docs/config/pydoc.conf
```

### 🌐 Accessing Documentation

#### Local Browsing
1. Run: `python scripts/serve_docs.py`
2. Open: http://localhost:8080/index.html
3. Navigate through service modules and cross-references

#### Direct File Access
All documentation is in standard HTML format and can be opened directly in any web browser.

### 📋 Documentation Structure

```
docs/api/
├── index.html                      # Main documentation index
├── cross-service-reference.html    # Integration guide
├── verified-endpoints-summary.md   # Endpoint status
├── profile-ingestor/              # Profile Ingestor docs
│   ├── resume_extractor.html
│   ├── resume_extractor.main.html
│   └── ...
├── orchestrator/                  # Orchestrator docs
│   └── api.html
├── strategist/                    # Strategist docs
│   └── api.html
├── analyst/                       # Analyst docs
│   └── api.html
├── architect/                     # Architect docs
│   └── api.html
├── editor/                        # Editor docs
│   └── api.html
└── shared/                        # Shared library docs
    └── llm_client.html
```

### 🔄 Integration Patterns

All services follow the **Orchestrator-Driven Communication** pattern:

1. **Session Creation**: Client → Orchestrator
2. **Service Coordination**: Orchestrator → Individual Services
3. **Data Flow**: Profile → Strategy → Analysis → Architecture → Editing
4. **Response Aggregation**: Orchestrator combines all responses

### 🔗 Live API Documentation

When services are running, interactive API documentation is available:

- **Orchestrator Swagger UI**: http://localhost:8000/docs
- **OpenAPI Schema**: http://localhost:8000/openapi.json

### 📊 System Status

- **Services Documented**: 7/7 (100%)
- **Generation Method**: Automated pydoc + custom enhancements
- **Last Updated**: September 20, 2025
- **Coverage**: All modules, classes, and functions

### 🛠️ Technical Details

- **Documentation Generator**: Python pydoc
- **Enhancement Scripts**: Custom HTML generation
- **Styling**: Modern responsive CSS
- **Navigation**: Hierarchical with cross-references
- **Search**: Browser native (Ctrl+F)

---

**HELIOS Career Operations System** • AI-Powered Career Intelligence Platform
Generated with pydoc • All 6 Services Operational • September 2025

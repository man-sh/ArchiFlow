# SDD Generator

A Python-based application that generates Software Development Documents (SDD) from business requirements and regulatory documents using local LLM (vLLM).

## Features

- **SDD Generation**: Automatically generate comprehensive Software Development Documents from plain text business requirements
- **Regulatory Document Search**: Upload and search regulatory documents using semantic search
- **Code Context Management**: Store and analyze code snippets for change request impact analysis
- **Mermaid Diagram Generation**: Generate architecture diagrams from SDDs
- **Jira Integration**: Sync generated SDDs with Jira issues
- **Local LLM**: Uses vLLM for privacy and control

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│   FastAPI        │────▶│   vLLM Server   │
│   (HTML/JS)     │     │   Backend        │     │   (Local LLM)   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   ChromaDB       │
                    │   Vector Store   │
                    └──────────────────┘
```

## Prerequisites

1. **Python 3.9+**
2. **vLLM server** running locally
3. **Node.js** (optional, for frontend development)

## Installation

### 1. Clone the repository

```bash
cd /workspace
```

### 2. Install Python dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp config/.env.example config/.env
```

Edit `config/.env` to set your vLLM API URL and model name:

```env
VLLM_API_URL=http://localhost:8000/v1
VLLM_MODEL_NAME=llama2-7b-chat
```

### 4. Start vLLM Server

Make sure you have vLLM installed and running:

```bash
# Example for running llama2-7b-chat
python -m vllm.entrypoints.api_server \
    --model meta-llama/Llama-2-7b-chat-hf \
    --host 0.0.0.0 \
    --port 8000
```

### 5. Run the Application

```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

The application will be available at:
- **Frontend**: http://localhost:8080/static/index.html
- **API Docs**: http://localhost:8080/docs

## API Endpoints

### Regulatory Documents
- `POST /api/regulatory/upload` - Upload regulatory document
- `GET /api/regulatory/search?query=<text>` - Search documents
- `GET /api/regulatory/documents` - List all documents
- `DELETE /api/regulatory/{filename}` - Delete document

### SDD Generation
- `POST /api/sdd/generate` - Generate SDD from requirements
- `GET /api/sdd/list` - List all SDDs
- `GET /api/sdd/{filename}` - Get specific SDD

### Code Context
- `POST /api/code/store` - Store code snippet
- `GET /api/code/{code_id}` - Retrieve code
- `POST /api/code/analyze` - Analyze code change impact
- `GET /api/code/search?q=<text>` - Search code
- `GET /api/code/list` - List all code snippets

### Diagrams
- `POST /api/diagram/generate` - Generate Mermaid diagram from SDD

### Jira Integration
- `POST /api/jira/sync` - Sync SDD to Jira issue

## Usage Examples

### Generate an SDD

```bash
curl -X POST "http://localhost:8080/api/sdd/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Payment Processing System",
    "requirements": "Build a payment processing system that handles credit card transactions...",
    "regulatory_query": "PCI-DSS compliance"
  }'
```

### Upload Regulatory Document

```bash
curl -X POST "http://localhost:8080/api/regulatory/upload" \
  -F "file=@pci_dss_requirements.pdf"
```

### Search Regulatory Documents

```bash
curl "http://localhost:8080/api/regulatory/search?query=data%20encryption%20requirements"
```

### Store Code for Context

```bash
curl -X POST "http://localhost:8080/api/code/store" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "payment_processor.py",
    "language": "python",
    "code": "def process_payment(amount, card_number):..."
  }'
```

### Analyze Code Change

```bash
curl -X POST "http://localhost:8080/api/code/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "code_id": "<code_id_from_store>",
    "change_description": "Add support for recurring payments"
  }'
```

## Project Structure

```
/workspace
├── backend/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── llm_client.py        # vLLM API client
│   ├── vector_store.py      # ChromaDB vector store
│   ├── code_context.py      # Code context manager
│   ├── jira_integration.py  # Jira integration
│   └── requirements.txt     # Python dependencies
├── frontend/
│   └── static/
│       └── index.html       # Single-page application
├── config/
│   └── .env.example         # Environment template
├── data/
│   ├── regulatory_docs/     # Uploaded regulatory documents
│   ├── generated_sdd/       # Generated SDDs
│   ├── code_context/        # Stored code snippets
│   └── vector_store/        # ChromaDB persistence
└── docs/
    └── README.md            # This file
```

## Configuration

Key configuration options in `config/.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| VLLM_API_URL | vLLM server URL | http://localhost:8000/v1 |
| VLLM_MODEL_NAME | Model to use | llama2-7b-chat |
| CHROMA_PERSIST_DIR | Vector store location | ./data/vector_store |
| JIRA_API_URL | Jira instance URL | (optional) |
| JIRA_API_TOKEN | Jira API token | (optional) |
| PORT | Server port | 8080 |

## Development

### Running Tests

```bash
pytest backend/tests/
```

### Hot Reload

The server runs with auto-reload enabled in development mode:

```bash
python -m uvicorn main:app --reload
```

## Security Considerations

1. **API Authentication**: Add authentication middleware for production
2. **CORS**: Configure allowed origins properly
3. **File Uploads**: Implement file type validation and size limits
4. **Rate Limiting**: Add rate limiting to prevent abuse

## Troubleshooting

### vLLM Connection Error

Ensure vLLM server is running:
```bash
curl http://localhost:8000/v1/models
```

### ChromaDB Issues

Delete and recreate vector store:
```bash
rm -rf data/vector_store
```

### Memory Issues

Reduce chunk size in `vector_store.py` or use a smaller embedding model.

## License

MIT License

## Contributing

Contributions are welcome! Please submit pull requests or open issues for bugs and feature requests.

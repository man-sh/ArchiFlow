# ArchiFlow
 Initial Implementation of SDD Generator with vLLM, Vector Store, and Frontend
Key features implemented:
- Added core backend API using FastAPI in backend/main.py with endpoints for SDD generation, regulatory document management, code context storage, and Jira integration
- Implemented vLLM client in backend/llm_client.py for LLM interactions including SDD generation, regulatory document search, and code analysis
- Created vector store using ChromaDB in backend/vector_store.py for semantic search of regulatory documents with fallback to hash-based embeddings
- Developed code context manager in backend/code_context.py for storing, retrieving, and searching code snippets with metadata
- Integrated Jira connectivity in backend/jira_integration.py for issue creation, updates, and linking SDDs to tickets
- Built responsive frontend interface in frontend/static/index.html with tabs for SDD generation, regulatory docs, code context, and diagrams
- Added configuration management in backend/config.py with support for vLLM, vector store, file directories, and optional Jira settings
- Included startup script start.py with vLLM server check and automatic FastAPI server launch
- Added .gitignore for Python project files and dependencies
- Created comprehensive documentation in docs/README.md with installation and usage instructions
- Added requirements.txt with dependencies including FastAPI, vLLM, ChromaDB, and sentence transformers

The system provides a complete workflow for generating Software Development Documents from business requirements using local LLMs, managing regulatory compliance documents, and maintaining code context for change requests. The frontend offers intuitive access to all backend functionality with visual feedback and diagram generation capabilities.

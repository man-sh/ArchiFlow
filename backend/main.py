"""
FastAPI application for SDD Generator.
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import aiofiles
from datetime import datetime

from backend.config import settings
from backend.llm_client import vllm_client
from backend.vector_store import document_store
from backend.code_context import code_context_manager
from backend.jira_integration import jira_integration


app = FastAPI(
    title="SDD Generator API",
    description="Generate Software Development Documents from business requirements and regulatory documents",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class BusinessRequirements(BaseModel):
    text: str
    title: str
    jira_issue_key: Optional[str] = None


class RegulatorySearchQuery(BaseModel):
    query: str
    n_results: int = 5


class CodeSnippet(BaseModel):
    filename: str
    code: str
    language: str = "python"
    metadata: Optional[Dict[str, Any]] = None


class ChangeRequest(BaseModel):
    code_id: str
    change_description: str


class SDDGenerationRequest(BaseModel):
    requirements: str
    regulatory_query: Optional[str] = None
    title: str


# Health Check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


# Regulatory Document Management
@app.post("/api/regulatory/upload")
async def upload_regulatory_document(file: UploadFile = File(...)):
    """Upload a regulatory document for indexing."""
    try:
        content = await file.read()
        text_content = content.decode('utf-8')
        
        # Add to vector store
        chunks_added = document_store.add_document(file.filename, text_content)
        
        # Save original file
        filepath = os.path.join(settings.regulatory_docs_dir, file.filename)
        async with aiofiles.open(filepath, 'wb') as f:
            await f.write(content)
        
        return {
            "message": "Document uploaded successfully",
            "filename": file.filename,
            "chunks_indexed": chunks_added
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/regulatory/search")
async def search_regulatory_documents(query: str, n_results: int = 5):
    """Search regulatory documents."""
    try:
        results = document_store.search(query, n_results)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/regulatory/documents")
async def list_regulatory_documents():
    """List all indexed regulatory documents."""
    try:
        stats = document_store.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/regulatory/{filename}")
async def delete_regulatory_document(filename: str):
    """Delete a regulatory document."""
    try:
        document_store.delete_document(filename)
        
        # Delete original file
        filepath = os.path.join(settings.regulatory_docs_dir, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
        
        return {"message": f"Document {filename} deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# SDD Generation
@app.post("/api/sdd/generate")
async def generate_sdd(request: SDDGenerationRequest):
    """Generate Software Development Document."""
    try:
        # Search for relevant regulatory documents if query provided
        regulatory_context = ""
        if request.regulatory_query:
            search_results = document_store.search(request.regulatory_query, n_results=5)
            regulatory_context = "\n\n".join([r['content'] for r in search_results])
        
        # Generate SDD using LLM
        sdd_content = await vllm_client.generate_sdd(
            business_requirements=request.requirements,
            regulatory_context=regulatory_context
        )
        
        # Save SDD
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{request.title.replace(' ', '_')}_{timestamp}.md"
        filepath = os.path.join(settings.generated_sdd_dir, filename)
        
        async with aiofiles.open(filepath, 'w') as f:
            await f.write(sdd_content)
        
        # Link to Jira if issue key provided
        if jira_integration.enabled:
            await jira_integration.link_sdd_to_issue(
                issue_key=request.title,  # In real app, this would be actual Jira key
                sdd_path=filepath,
                sdd_summary=sdd_content[:500]
            )
        
        return {
            "message": "SDD generated successfully",
            "filename": filename,
            "filepath": filepath,
            "content": sdd_content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sdd/{filename}")
async def get_sdd(filename: str):
    """Retrieve a generated SDD."""
    filepath = os.path.join(settings.generated_sdd_dir, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="SDD not found")
    
    async with aiofiles.open(filepath, 'r') as f:
        content = await f.read()
    
    return {"filename": filename, "content": content}


@app.get("/api/sdd/list")
async def list_sdds():
    """List all generated SDDs."""
    sdds = []
    for filename in os.listdir(settings.generated_sdd_dir):
        if filename.endswith('.md'):
            filepath = os.path.join(settings.generated_sdd_dir, filename)
            stat = os.stat(filepath)
            sdds.append({
                "filename": filename,
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "size": stat.st_size
            })
    return {"sdds": sdds}


# Code Context Management
@app.post("/api/code/store")
async def store_code(snippet: CodeSnippet):
    """Store a code snippet for context analysis."""
    try:
        code_id = await code_context_manager.store_code(
            filename=snippet.filename,
            code=snippet.code,
            language=snippet.language,
            metadata=snippet.metadata
        )
        return {"message": "Code stored successfully", "code_id": code_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/code/{code_id}")
async def get_code(code_id: str):
    """Retrieve a code snippet."""
    code = await code_context_manager.get_code(code_id)
    if not code:
        raise HTTPException(status_code=404, detail="Code not found")
    return code


@app.post("/api/code/analyze")
async def analyze_code_change(request: ChangeRequest):
    """Analyze code in context of a change request."""
    try:
        code_doc = await code_context_manager.get_code(request.code_id)
        if not code_doc:
            raise HTTPException(status_code=404, detail="Code not found")
        
        analysis = await vllm_client.analyze_code_context(
            code=code_doc['code'],
            change_request=request.change_description
        )
        
        return {
            "code_id": request.code_id,
            "filename": code_doc['filename'],
            "analysis": analysis
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/code/search")
async def search_code(q: str):
    """Search code snippets."""
    try:
        results = await code_context_manager.search_code(q)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/code/list")
async def list_code():
    """List all stored code snippets."""
    try:
        codes = await code_context_manager.list_all_code()
        return {"codes": codes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Maimaid Diagram Integration (Placeholder)
@app.post("/api/diagram/generate")
async def generate_diagram(sdd_filename: str = Form(...)):
    """Generate diagram from SDD (placeholder for maimaid integration)."""
    try:
        # Read SDD
        filepath = os.path.join(settings.generated_sdd_dir, sdd_filename)
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="SDD not found")
        
        async with aiofiles.open(filepath, 'r') as f:
            sdd_content = await f.read()
        
        # Extract architecture information and generate mermaid diagram
        # This is a placeholder - in production, use LLM to extract and generate proper mermaid
        mermaid_diagram = f"""
graph TD
    A[Business Requirements] --> B[System Architecture]
    B --> C[Component Design]
    C --> D[Data Model]
    D --> E[API Layer]
    E --> F[User Interface]
    
    style A fill:#e1f5ff
    style B fill:#fff5e1
    style C fill:#e1ffe1
    style D fill:#ffe1e1
    style E fill:#f5e1ff
    style F fill:#ffffe1
"""
        
        return {
            "sdd_filename": sdd_filename,
            "mermaid_diagram": mermaid_diagram.strip(),
            "message": "Diagram generated (placeholder implementation)"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Jira Integration
@app.post("/api/jira/sync")
async def sync_to_jira(
    sdd_filename: str,
    jira_issue_key: str,
    summary: str
):
    """Sync SDD to Jira issue."""
    try:
        if not jira_integration.enabled:
            raise HTTPException(status_code=400, detail="Jira integration not configured")
        
        filepath = os.path.join(settings.generated_sdd_dir, sdd_filename)
        async with aiofiles.open(filepath, 'r') as f:
            sdd_content = await f.read()
        
        result = await jira_integration.link_sdd_to_issue(
            issue_key=jira_issue_key,
            sdd_path=filepath,
            sdd_summary=sdd_content
        )
        
        return {"message": "SDD linked to Jira issue", "result": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Serve frontend static files
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)

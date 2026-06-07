"""
Code Context Manager for storing and analyzing code snippets.
"""
import os
import json
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
import aiofiles
from backend.config import settings


class CodeContextManager:
    """Manage code context for change request analysis."""
    
    def __init__(self):
        self.code_dir = settings.code_context_dir
    
    def _generate_id(self, code: str, filename: str) -> str:
        """Generate unique ID for a code snippet."""
        content = f"{filename}:{code[:500]}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def store_code(
        self,
        filename: str,
        code: str,
        language: str = "python",
        metadata: Optional[Dict] = None
    ) -> str:
        """Store code snippet with metadata."""
        code_id = self._generate_id(code, filename)
        filepath = os.path.join(self.code_dir, f"{code_id}.json")
        
        document = {
            "id": code_id,
            "filename": filename,
            "language": language,
            "code": code,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        async with aiofiles.open(filepath, 'w') as f:
            await f.write(json.dumps(document, indent=2))
        
        return code_id
    
    async def get_code(self, code_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve code snippet by ID."""
        filepath = os.path.join(self.code_dir, f"{code_id}.json")
        
        if not os.path.exists(filepath):
            return None
        
        async with aiofiles.open(filepath, 'r') as f:
            content = await f.read()
            return json.loads(content)
    
    async def update_code(self, code_id: str, code: str, metadata: Optional[Dict] = None) -> bool:
        """Update existing code snippet."""
        existing = await self.get_code(code_id)
        if not existing:
            return False
        
        existing["code"] = code
        existing["metadata"] = metadata or existing.get("metadata", {})
        existing["updated_at"] = datetime.utcnow().isoformat()
        
        filepath = os.path.join(self.code_dir, f"{code_id}.json")
        async with aiofiles.open(filepath, 'w') as f:
            await f.write(json.dumps(existing, indent=2))
        
        return True
    
    async def search_code(self, query: str) -> List[Dict[str, Any]]:
        """Search code snippets by filename or metadata."""
        results = []
        
        for filename in os.listdir(self.code_dir):
            if not filename.endswith('.json'):
                continue
            
            filepath = os.path.join(self.code_dir, filename)
            async with aiofiles.open(filepath, 'r') as f:
                content = await f.read()
                doc = json.loads(content)
                
                # Simple text search (can be enhanced with vector search)
                if (query.lower() in doc['filename'].lower() or 
                    query.lower() in doc.get('metadata', {}).get('description', '').lower() or
                    query.lower() in doc['code'][:1000].lower()):
                    results.append({
                        "id": doc['id'],
                        "filename": doc['filename'],
                        "language": doc['language'],
                        "created_at": doc['created_at'],
                        "preview": doc['code'][:200] + "..."
                    })
        
        return results
    
    async def list_all_code(self) -> List[Dict[str, Any]]:
        """List all stored code snippets."""
        results = []
        
        for filename in os.listdir(self.code_dir):
            if not filename.endswith('.json'):
                continue
            
            filepath = os.path.join(self.code_dir, filename)
            async with aiofiles.open(filepath, 'r') as f:
                content = await f.read()
                doc = json.loads(content)
                results.append({
                    "id": doc['id'],
                    "filename": doc['filename'],
                    "language": doc['language'],
                    "created_at": doc['created_at'],
                    "updated_at": doc['updated_at']
                })
        
        return results
    
    async def delete_code(self, code_id: str) -> bool:
        """Delete a code snippet."""
        filepath = os.path.join(self.code_dir, f"{code_id}.json")
        
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False


# Singleton instance
code_context_manager = CodeContextManager()

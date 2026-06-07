"""
Jira Integration for syncing SDD and requirements.
"""
import httpx
from typing import Optional, List, Dict, Any
from backend.config import settings


class JiraIntegration:
    """Integration with Jira for requirement tracking and issue management."""
    
    def __init__(self):
        self.api_url = settings.jira_api_url
        self.api_token = settings.jira_api_token
        self.project_key = settings.jira_project_key
        self.enabled = bool(self.api_url and self.api_token)
    
    async def create_issue(
        self,
        summary: str,
        description: str,
        issue_type: str = "Story",
        labels: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Create a new Jira issue."""
        if not self.enabled:
            return None
        
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "fields": {
                "project": {"key": self.project_key},
                "summary": summary,
                "description": description,
                "issuetype": {"name": issue_type},
                "labels": labels or []
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/rest/api/3/issue",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
    
    async def update_issue(
        self,
        issue_key: str,
        fields: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update an existing Jira issue."""
        if not self.enabled:
            return None
        
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        payload = {"fields": fields}
        
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.api_url}/rest/api/3/issue/{issue_key}",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return {"status": "updated", "issue_key": issue_key}
    
    async def add_comment(self, issue_key: str, comment: str) -> Optional[Dict[str, Any]]:
        """Add a comment to a Jira issue."""
        if not self.enabled:
            return None
        
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        payload = {"body": comment}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/rest/api/3/issue/{issue_key}/comment",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
    
    async def get_issue(self, issue_key: str) -> Optional[Dict[str, Any]]:
        """Get details of a Jira issue."""
        if not self.enabled:
            return None
        
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/rest/api/3/issue/{issue_key}",
                headers=headers
            )
            response.raise_for_status()
            return response.json()
    
    async def link_sdd_to_issue(
        self,
        issue_key: str,
        sdd_path: str,
        sdd_summary: str
    ) -> Optional[Dict[str, Any]]:
        """Link generated SDD to a Jira issue."""
        comment = f"""
📄 **Software Development Document Generated**

SDD Location: `{sdd_path}`

Summary:
{sdd_summary[:500]}...

This SDD was automatically generated from business requirements and regulatory documents.
        """
        return await self.add_comment(issue_key, comment)


# Singleton instance (may be disabled if not configured)
jira_integration = JiraIntegration()

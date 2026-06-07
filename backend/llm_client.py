"""
vLLM LLM Client for interacting with local LLM server.
"""
import httpx
from typing import Optional, List, Dict, Any
from backend.config import settings


class VLLMClient:
    """Client for interacting with vLLM API server."""
    
    def __init__(self):
        self.api_url = settings.vllm_api_url
        self.model_name = settings.vllm_model_name
        self.timeout = 120.0
    
    async def generate_completion(
        self,
        prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        top_p: float = 0.95,
        stop: Optional[List[str]] = None
    ) -> str:
        """Generate text completion using vLLM API."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "stop": stop or []
            }
            
            try:
                response = await client.post(
                    f"{self.api_url}/completions",
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["text"]
            except httpx.HTTPError as e:
                raise Exception(f"vLLM API error: {str(e)}")
    
    async def generate_chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        top_p: float = 0.95
    ) -> str:
        """Generate chat completion using vLLM API."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {
                "model": self.model_name,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p
            }
            
            try:
                response = await client.post(
                    f"{self.api_url}/chat/completions",
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"]
            except httpx.HTTPError as e:
                raise Exception(f"vLLM API error: {str(e)}")
    
    async def generate_sdd(
        self,
        business_requirements: str,
        regulatory_context: str = ""
    ) -> str:
        """Generate Software Development Document from requirements."""
        prompt = f"""You are an expert software architect. Generate a comprehensive Software Development Document (SDD) based on the following business requirements.

BUSINESS REQUIREMENTS:
{business_requirements}

REGULATORY CONTEXT:
{regulatory_context if regulatory_context else "No specific regulatory constraints provided."}

Generate a detailed SDD including:
1. Executive Summary
2. System Architecture Overview
3. Component Design
4. Data Model
5. API Specifications
6. Security Considerations
7. Compliance Mapping (if regulatory context provided)
8. Testing Strategy
9. Deployment Plan

Format the output in Markdown with clear sections and subsections."""

        return await self.generate_completion(prompt, max_tokens=4096, temperature=0.5)
    
    async def search_regulatory_documents(
        self,
        query: str,
        document_chunks: List[str]
    ) -> List[Dict[str, Any]]:
        """Search through regulatory documents for relevant sections."""
        prompt = f"""You are a regulatory compliance expert. Given the following query and document chunks, identify the most relevant sections.

QUERY: {query}

DOCUMENT CHUNKS:
{' '.join(document_chunks[:5])}  # Limit to top 5 chunks

Return a JSON array of relevant sections with their relevance score (0-1) and excerpt. Format:
[{{"relevance": 0.95, "excerpt": "relevant text...", "source": "document name"}}]"""

        response = await self.generate_completion(prompt, max_tokens=2048, temperature=0.3)
        
        # Parse JSON response (basic parsing, production should use proper JSON parser)
        import json
        try:
            return json.loads(response.strip())
        except:
            return [{"relevance": 0.5, "excerpt": response, "source": "unknown"}]
    
    async def analyze_code_context(
        self,
        code: str,
        change_request: str
    ) -> Dict[str, Any]:
        """Analyze code in context of a change request."""
        prompt = f"""You are a senior software engineer. Analyze the following code in the context of this change request.

CHANGE REQUEST:
{change_request}

CODE:
{code[:8000]}  # Limit code length

Provide analysis in JSON format:
{{
    "affected_components": ["list of affected components"],
    "risk_level": "low|medium|high",
    "recommended_changes": ["list of recommended changes"],
    "compliance_impact": "description of any compliance impact",
    "testing_requirements": ["list of required tests"]
}}"""

        response = await self.generate_completion(prompt, max_tokens=2048, temperature=0.3)
        
        import json
        try:
            return json.loads(response.strip())
        except:
            return {
                "affected_components": ["analysis failed"],
                "risk_level": "medium",
                "recommended_changes": [response],
                "compliance_impact": "Unknown",
                "testing_requirements": ["Manual review required"]
            }


# Singleton instance
vllm_client = VLLMClient()

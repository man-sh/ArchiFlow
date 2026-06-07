"""
Configuration management for the SDD Generator application.
"""
import os
from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # vLLM API Configuration
    vllm_api_url: str = Field(default="http://localhost:8000/v1")
    vllm_model_name: str = Field(default="llama2-7b-chat")
    
    # Custom System Prompt for SDD Generation
    sdd_system_prompt: str = Field(
        default="""You are an expert software architect and technical writer. Your task is to generate comprehensive, professional Software Development Documents (SDD) based on business requirements and regulatory context.

Your SDD should be detailed, well-structured, and include all necessary technical specifications for development teams to implement the system correctly."""
    )
    
    # Custom System Prompt for Code Analysis
    code_analysis_system_prompt: str = Field(
        default="""You are a senior software engineer with expertise in code review, architecture analysis, and best practices. Analyze code changes thoroughly and provide actionable recommendations."""
    )
    
    # Vector Store Configuration
    chroma_persist_dir: str = Field(default="./data/vector_store")
    
    # File Storage Directories
    regulatory_docs_dir: str = Field(default="./data/regulatory_docs")
    generated_sdd_dir: str = Field(default="./data/generated_sdd")
    code_context_dir: str = Field(default="./data/code_context")
    
    # Jira Integration (Optional)
    jira_api_url: Optional[str] = Field(default=None)
    jira_api_token: Optional[str] = Field(default=None)
    jira_project_key: Optional[str] = Field(default=None)
    
    # Server Configuration
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8080)
    debug: bool = Field(default=True)
    
    class Config:
        env_file = "config/.env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()

# Ensure directories exist
for dir_path in [settings.chroma_persist_dir, settings.regulatory_docs_dir, 
                 settings.generated_sdd_dir, settings.code_context_dir]:
    os.makedirs(dir_path, exist_ok=True)

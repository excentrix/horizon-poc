# backend/src/prompts/prompt_manager.py
import yaml
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import os
from enum import Enum

class PromptType(Enum):
    MENTOR_CONVERSATION = "mentor_conversation"
    FACT_EXTRACTION = "fact_extraction"
    SESSION_SUMMARY = "session_summary"
    TASK_ANALYSIS = "task_analysis"
    MEMORY_CONSOLIDATION = "memory_consolidation"

class PromptManager:
    def __init__(self, prompts_dir: str = None):
        self.prompts_dir = Path(prompts_dir or os.path.join(os.path.dirname(__file__), "templates"))
        self.cache = {}
        self.version = os.getenv("PROMPT_VERSION", "v1")
    
    def get_prompt(self, prompt_type: PromptType, variables: Dict[str, Any] = None) -> str:
        """Get a prompt template with variable substitution."""
        cache_key = f"{prompt_type.value}_{self.version}"
        
        if cache_key not in self.cache:
            self._load_prompt(prompt_type)
        
        template = self.cache.get(cache_key, {})
        prompt_content = template.get("content", "")
        
        if variables:
            # Simple variable substitution
            for key, value in variables.items():
                prompt_content = prompt_content.replace(f"{{{key}}}", str(value))
        
        return prompt_content
    
    def _load_prompt(self, prompt_type: PromptType):
        """Load prompt from YAML file."""
        file_path = self.prompts_dir / f"{prompt_type.value}.yaml"
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
                cache_key = f"{prompt_type.value}_{self.version}"
                
                # Get version-specific prompt or fallback to default
                version_data = data.get("versions", {}).get(self.version, data.get("default", {}))
                self.cache[cache_key] = version_data
                
        except FileNotFoundError:
            print(f"❌ Prompt file not found: {file_path}")
            self.cache[f"{prompt_type.value}_{self.version}"] = {"content": "System error: prompt not found"}
        except Exception as e:
            print(f"❌ Error loading prompt {prompt_type.value}: {e}")
            self.cache[f"{prompt_type.value}_{self.version}"] = {"content": "System error: prompt loading failed"}
    
    def get_system_message(self, prompt_type: PromptType, variables: Dict[str, Any] = None) -> Dict[str, str]:
        """Get prompt formatted as a system message."""
        content = self.get_prompt(prompt_type, variables)
        return {"role": "system", "content": content}
    
    def list_available_prompts(self) -> List[str]:
        """List all available prompt types."""
        return [prompt_type.value for prompt_type in PromptType]

# Global instance
prompt_manager = PromptManager()
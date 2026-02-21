"""
Prompt definitions registry.

Local prompt templates are the source of truth. Each prompt module calls
register_prompt() to add its definition to PROMPT_REGISTRY, which the
BedrockPromptManager uses at startup to sync content to Bedrock.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class PromptDefinition:
    """A local prompt definition that maps to a Bedrock managed prompt."""

    # Identity
    name: str
    bedrock_config_key: str

    # Content
    template_text: str

    # Bedrock variant configuration
    model_id: str = "anthropic.claude-sonnet-4-20250514"
    temperature: float = 0.0
    top_p: float = 1.0
    max_tokens: int = 4096

    # MCP metadata
    title: str = ""
    description: str = ""
    tags: frozenset[str] = field(default_factory=frozenset)

    @property
    def variables(self) -> list[str]:
        """Extract {{variable_name}} placeholders from template text."""
        return re.findall(r"\{\{(\w+)\}\}", self.template_text)

    def render(self, **kwargs: str) -> str:
        """Substitute {{variable}} placeholders with provided values."""
        text = self.template_text
        for var_name in self.variables:
            placeholder = "{{" + var_name + "}}"
            if var_name in kwargs:
                text = text.replace(placeholder, kwargs[var_name])
        return text


# Global registry: name -> PromptDefinition
PROMPT_REGISTRY: dict[str, PromptDefinition] = {}


def register_prompt(definition: PromptDefinition) -> PromptDefinition:
    """Register a prompt definition. Called at module import time."""
    if definition.name in PROMPT_REGISTRY:
        raise ValueError(f"Duplicate prompt name: {definition.name!r}")
    PROMPT_REGISTRY[definition.name] = definition
    return definition

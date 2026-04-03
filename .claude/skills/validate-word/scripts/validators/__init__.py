"""
Validation modules for Word document processing.
Adapted from Anthropic's official docx skill.
"""

from .base import BaseSchemaValidator
from .docx import DOCXSchemaValidator

__all__ = [
    "BaseSchemaValidator",
    "DOCXSchemaValidator",
]

"""
Code Generation Service

Orchestrates the code generation pipeline:
AI generation → Validation → Regeneration (if needed) → Code output
"""

import json
import logging
import sys
import os

# Add parent directory for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from AI_Integration.main import generate_IEC_JSON, regenerate_IEC_JSON
from validator import validator as code_validator
from generator import generator, GeneratorError

logger = logging.getLogger(__name__)


class CodeGenerationError(Exception):
    """Exception for code generation errors."""
    def __init__(self, message: str, is_validation_error: bool = False):
        super().__init__(message)
        self.is_validation_error = is_validation_error


class CodeGenerationService:
    """Service for generating IEC 61131-3 code from natural language."""
    
    def __init__(self, max_regeneration_attempts: int = 2):
        self.max_attempts = max_regeneration_attempts
    
    def generate(self, narrative: str) -> str:
        """
        Generate IEC 61131-3 code from natural language.
        
        Args:
            narrative: Natural language description
        
        Returns:
            Generated Structured Text code
        
        Raises:
            CodeGenerationError: If generation fails
        """
        attempts_remaining = self.max_attempts
        
        # Step 1: Generate intermediate JSON
        logger.info(f"Generating code for: {narrative[:100]}...")
        intermediate = self._generate_intermediate(narrative)
        
        # Step 2: Parse JSON
        intermediate_json = self._parse_json(intermediate)
        
        # Step 3: Check for "no device found"
        if self._is_no_device_response(intermediate_json):
            raise CodeGenerationError(
                "No matching device found for your query. Please check the available variables.",
                is_validation_error=True
            )
        
        # Step 4: Validate and regenerate if needed
        validation_result = code_validator(intermediate_json)
        
        while not validation_result[0] and attempts_remaining > 0:
            attempts_remaining -= 1
            logger.info(f"Regenerating due to validation errors. Attempts remaining: {attempts_remaining}")
            logger.debug(f"Validation error: {validation_result[1]}")
            
            intermediate = regenerate_IEC_JSON(narrative, validation_result[1], intermediate)
            
            try:
                intermediate_json = self._parse_json(intermediate)
            except CodeGenerationError:
                continue
            
            validation_result = code_validator(intermediate_json)
        
        # Step 5: Check final validation
        if not validation_result[0]:
            raise CodeGenerationError(
                validation_result[1],
                is_validation_error=True
            )
        
        # Step 6: Generate code
        return self._generate_code(intermediate_json)
    
    def _generate_intermediate(self, narrative: str) -> str:
        """Generate intermediate JSON representation."""
        try:
            return generate_IEC_JSON(narrative)
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            raise CodeGenerationError(f"AI generation failed: {e}")
    
    def _parse_json(self, intermediate: str) -> dict:
        """Parse intermediate JSON."""
        try:
            return json.loads(intermediate)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            raise CodeGenerationError(
                "AI generated invalid JSON. Please try rephrasing your request."
            )
    
    def _is_no_device_response(self, data) -> bool:
        """Check if response indicates no device was found."""
        return isinstance(data, dict) and data.get("NO_DEVICE_FOUND")
    
    def _generate_code(self, intermediate_json) -> str:
        """Generate final Structured Text code."""
        try:
            return generator(intermediate_json)
        except GeneratorError as e:
            logger.error(f"Code generation failed: {e}")
            raise CodeGenerationError(str(e))


# Service instance
code_generation_service = CodeGenerationService()


def generate_code(narrative: str) -> str:
    """Convenience function for code generation."""
    return code_generation_service.generate(narrative)

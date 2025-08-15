"""
TypeScript Code Formatter

This module provides functionality to format TypeScript code using Prettier
or other formatting tools from Python backend.
"""

import os
import subprocess
import tempfile
import logging
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class TypeScriptFormatter:
    """
    TypeScript code formatter using Prettier.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the TypeScript formatter.
        
        Args:
            config: Prettier configuration options
        """
        self.config = config or {
            'parser': 'typescript',
            'singleQuote': True,
            'semi': True,
            'tabWidth': 2,
            'printWidth': 100,
            'trailingComma': 'es5',
            'bracketSpacing': True,
            'arrowParens': 'avoid'
        }
    
    def _build_prettier_args(self) -> list:
        """
        Build Prettier command line arguments from config.
        
        Returns:
            List of command line arguments
        """
        args = ['npx', 'prettier']
        
        # Add parser
        if 'parser' in self.config:
            args.extend(['--parser', self.config['parser']])
        
        # Add boolean options
        boolean_options = {
            'singleQuote': '--single-quote',
            'semi': '--semi',
            'bracketSpacing': '--bracket-spacing'
        }
        
        for key, flag in boolean_options.items():
            if key in self.config:
                if self.config[key]:
                    args.append(flag)
                else:
                    args.append(f'--no-{flag.replace("--", "")}')
        
        # Add value options
        value_options = {
            'tabWidth': '--tab-width',
            'printWidth': '--print-width',
            'trailingComma': '--trailing-comma',
            'arrowParens': '--arrow-parens'
        }
        
        for key, flag in value_options.items():
            if key in self.config:
                args.extend([flag, str(self.config[key])])
        
        return args
    
    def format_code(self, code: str, timeout: int = 10) -> str:
        """
        Format TypeScript code using Prettier.
        
        Args:
            code: TypeScript code to format
            timeout: Timeout in seconds for prettier command
            
        Returns:
            Formatted code or original code if formatting fails
        """
        if not code or not code.strip():
            return code
        
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(
                mode='w', 
                suffix='.ts', 
                delete=False,
                encoding='utf-8'
            ) as temp_file:
                temp_file.write(code)
                temp_file_path = temp_file.name
            
            # Build prettier command
            prettier_args = self._build_prettier_args()
            prettier_args.append(temp_file_path)
            
            # Run prettier
            result = subprocess.run(
                prettier_args,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8'
            )
            
            # Clean up temp file
            os.unlink(temp_file_path)
            
            if result.returncode == 0:
                formatted_code = result.stdout
                logger.debug("Successfully formatted TypeScript code with Prettier")
                return formatted_code
            else:
                logger.warning(f"Prettier formatting failed: {result.stderr}")
                return code
                
        except subprocess.TimeoutExpired:
            logger.warning(f"Prettier formatting timed out after {timeout}s")
            if 'temp_file_path' in locals():
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
            return code
        except FileNotFoundError:
            logger.warning("Prettier not found. Install with: npm install -g prettier")
            return code
        except Exception as e:
            logger.warning(f"Error formatting TypeScript code: {str(e)}")
            if 'temp_file_path' in locals():
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
            return code
    
    def format_file(self, file_path: str, in_place: bool = True) -> Optional[str]:
        """
        Format a TypeScript file.
        
        Args:
            file_path: Path to the TypeScript file
            in_place: Whether to format in place or return formatted content
            
        Returns:
            Formatted content if in_place=False, None otherwise
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                logger.error(f"File not found: {file_path}")
                return None
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Format content
            formatted_content = self.format_code(original_content)
            
            if in_place:
                # Write back to file if content changed
                if formatted_content != original_content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(formatted_content)
                    logger.info(f"Formatted file: {file_path}")
                else:
                    logger.debug(f"File already formatted: {file_path}")
                return None
            else:
                return formatted_content
                
        except Exception as e:
            logger.error(f"Error formatting file {file_path}: {str(e)}")
            return None
    
    def is_prettier_available(self) -> bool:
        """
        Check if Prettier is available.
        
        Returns:
            True if Prettier is available, False otherwise
        """
        try:
            result = subprocess.run(
                ['npx', 'prettier', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False


# Global formatter instance
_default_formatter = None

def get_formatter(config: Optional[Dict[str, Any]] = None) -> TypeScriptFormatter:
    """
    Get a TypeScript formatter instance.
    
    Args:
        config: Optional custom configuration
        
    Returns:
        TypeScriptFormatter instance
    """
    global _default_formatter
    
    if config:
        # Return new instance with custom config
        return TypeScriptFormatter(config)
    
    if _default_formatter is None:
        _default_formatter = TypeScriptFormatter()
    
    return _default_formatter


def format_typescript_code(code: str, config: Optional[Dict[str, Any]] = None) -> str:
    """
    Convenience function to format TypeScript code.
    
    Args:
        code: TypeScript code to format
        config: Optional Prettier configuration
        
    Returns:
        Formatted code
    """
    formatter = get_formatter(config)
    return formatter.format_code(code)


def format_test_case_code(code: str, config: Optional[Dict[str, Any]] = None) -> str:
    """
    Format TypeScript test case code with test-specific configuration.
    
    Args:
        code: TypeScript test case code to format
        config: Optional custom configuration (merged with test defaults)
        
    Returns:
        Formatted test case code
    """
    # Default config for test cases
    test_config = {
        'parser': 'typescript',
        'singleQuote': True,
        'semi': True,
        'tabWidth': 2,
        'printWidth': 120,  # Longer lines for test readability
        'trailingComma': 'es5',
        'bracketSpacing': True,
        'arrowParens': 'avoid'
    }
    
    # Merge with custom config if provided
    if config:
        test_config.update(config)
    
    formatter = get_formatter(test_config)
    return formatter.format_code(code)


def format_fixture_code(code: str, config: Optional[Dict[str, Any]] = None) -> str:
    """
    Format TypeScript fixture code with fixture-specific configuration.
    
    Args:
        code: TypeScript fixture code to format
        config: Optional custom configuration (merged with fixture defaults)
        
    Returns:
        Formatted fixture code
    """
    # Default config for fixtures
    fixture_config = {
        'parser': 'typescript',
        'singleQuote': True,
        'semi': True,
        'tabWidth': 2,
        'printWidth': 100,  # Standard width for fixtures
        'trailingComma': 'es5',
        'bracketSpacing': True,
        'arrowParens': 'avoid'
    }
    
    # Merge with custom config if provided
    if config:
        fixture_config.update(config)
    
    formatter = get_formatter(fixture_config)
    return formatter.format_code(code)


def format_typescript_file(file_path: str, in_place: bool = True, 
                          config: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """
    Convenience function to format a TypeScript file.
    
    Args:
        file_path: Path to the TypeScript file
        in_place: Whether to format in place
        config: Optional Prettier configuration
        
    Returns:
        Formatted content if in_place=False, None otherwise
    """
    formatter = get_formatter(config)
    return formatter.format_file(file_path, in_place)

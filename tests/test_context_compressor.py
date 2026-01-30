"""Tests for core/context_compressor.py - Context Compressor."""

import pytest

from code_puppy.core.context_compressor import (
    CompressionResult,
    ContextCompressor,
)


class TestPythonASTPruning:
    """Tests for Python AST pruning."""
    
    def test_prune_simple_function(self):
        """Should extract function signature and docstring."""
        compressor = ContextCompressor()
        
        source = '''
def hello(name: str) -> str:
    """Say hello to someone."""
    greeting = f"Hello, {name}!"
    return greeting
'''
        
        result = compressor.prune_python_ast(source)
        
        assert "def hello(name: str) -> str:" in result
        assert "Say hello to someone." in result
        assert "..." in result  # Body replaced with ellipsis
        assert "greeting =" not in result  # Body removed
    
    def test_prune_class(self):
        """Should extract class signature and docstring."""
        compressor = ContextCompressor()
        
        source = '''
class MyClass(BaseClass):
    """A sample class."""
    
    def __init__(self, value: int):
        """Initialize with value."""
        self.value = value
        self.computed = value * 2
'''
        
        result = compressor.prune_python_ast(source)
        
        assert "class MyClass(BaseClass):" in result
        assert "A sample class." in result
        assert "def __init__(self, value: int):" in result
        assert "self.computed" not in result
    
    def test_preserve_imports(self):
        """Should preserve import statements."""
        compressor = ContextCompressor()
        
        source = '''
import os
from pathlib import Path
from typing import Optional, List

def process(path: Path) -> None:
    """Process a path."""
    if path.exists():
        os.remove(path)
'''
        
        result = compressor.prune_python_ast(source)
        
        assert "import os" in result
        assert "from pathlib import Path" in result
        assert "from typing import Optional, List" in result
    
    def test_handle_syntax_errors_gracefully(self):
        """Should fallback to truncation on syntax errors."""
        compressor = ContextCompressor()
        
        source = '''
def broken(
    this is not valid python
'''
        
        result = compressor.prune_python_ast(source)
        
        # Should return something, not crash
        assert result is not None


class TestHeadTailTruncation:
    """Tests for head/tail truncation."""
    
    def test_truncate_long_content(self):
        """Should keep head and tail, drop middle."""
        compressor = ContextCompressor()
        
        lines = [f"Line {i}" for i in range(100)]
        content = "\n".join(lines)
        
        result = compressor._truncate_head_tail(content, head_lines=10, tail_lines=10)
        
        assert "Line 0" in result
        assert "Line 9" in result
        assert "Line 50" not in result
        assert "Line 90" in result
        assert "Line 99" in result
        assert "truncated" in result.lower()
    
    def test_no_truncation_for_short_content(self):
        """Should not truncate short content."""
        compressor = ContextCompressor()
        
        lines = [f"Line {i}" for i in range(15)]
        content = "\n".join(lines)
        
        result = compressor._truncate_head_tail(content, head_lines=10, tail_lines=10)
        
        assert result == content


class TestToolOutputCompression:
    """Tests for tool output compression."""
    
    def test_compress_long_output(self):
        """Should compress long tool outputs."""
        compressor = ContextCompressor()
        compressor.MAX_TOOL_OUTPUT_LINES = 30
        
        lines = [f"Output line {i}" for i in range(100)]
        output = "\n".join(lines)
        
        result = compressor.compress_tool_output(output, "shell")
        
        assert len(result) < len(output)
        assert "Output line 0" in result
        assert "Output line 99" in result
    
    def test_no_compression_for_short_output(self):
        """Should not compress short outputs."""
        compressor = ContextCompressor()
        
        output = "Short output\nJust two lines"
        
        result = compressor.compress_tool_output(output, "shell")
        
        assert result == output


class TestFileContextCompression:
    """Tests for file context compression."""
    
    def test_active_file_less_compressed(self):
        """Active files should be less compressed."""
        compressor = ContextCompressor()
        
        source = '''
def func1():
    """Function 1."""
    return 1

def func2():
    """Function 2."""
    return 2
'''
        
        active = compressor.compress_file_context("test.py", source, is_active=True)
        reference = compressor.compress_file_context("test.py", source, is_active=False)
        
        # Active should have more content
        assert len(active) >= len(reference)
    
    def test_caching_works(self):
        """Should cache compression results."""
        compressor = ContextCompressor()
        
        source = "def test(): pass"
        
        result1 = compressor.compress_file_context("test.py", source, is_active=False)
        result2 = compressor.compress_file_context("test.py", source, is_active=False)
        
        assert result1 == result2


class TestHistoryCompression:
    """Tests for message history compression."""
    
    def test_compress_history_sliding_window(self):
        """Should apply sliding window to long histories."""
        compressor = ContextCompressor()
        
        # Mock messages (simple strings for testing)
        messages = [f"Message {i}" for i in range(20)]
        
        compressed, result = compressor.compress_history(
            messages, max_messages=5, max_tokens=100_000
        )
        
        assert len(compressed) <= 5
        assert result.strategy_used != "none"
    
    def test_no_compression_for_short_history(self):
        """Should not compress short histories."""
        compressor = ContextCompressor()
        
        messages = ["Message 1", "Message 2"]
        
        compressed, result = compressor.compress_history(
            messages, max_messages=10, max_tokens=100_000
        )
        
        assert len(compressed) == 2
        assert result.strategy_used == "none"


class TestBatchCompression:
    """Tests for batch file compression."""
    
    def test_compress_multiple_files(self):
        """Should compress multiple files with active file priority."""
        compressor = ContextCompressor()
        
        files = {
            "main.py": "def main(): pass",
            "utils.py": "def helper(): pass",
            "config.py": "CONFIG = {}",
        }
        
        compressed, result = compressor.compress_context_batch(
            files,
            active_file="main.py",
            target_tokens=10_000,
        )
        
        assert len(compressed) == 3
        assert result.compression_ratio <= 1.0


class TestCompressionResult:
    """Tests for CompressionResult dataclass."""
    
    def test_tokens_saved_calculation(self):
        """Should calculate tokens saved correctly."""
        result = CompressionResult(
            original_tokens=10_000,
            compressed_tokens=4_000,
            compression_ratio=0.4,
            strategy_used="ast_prune",
        )
        
        assert result.tokens_saved == 6_000

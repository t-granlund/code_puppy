"""Context Compressor - The Pruner.

Reduces input token size for fast models (Cerebras) with:
- AST Pruning: Strip function bodies, keep signatures/docstrings
- History Truncation: Keep head/tail of long outputs, drop middle
- Smart Summarization: Replace old context with summaries
"""

import ast
import hashlib
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class CompressionResult:
    """Result of compression operation."""
    
    original_tokens: int
    compressed_tokens: int
    compression_ratio: float
    strategy_used: str
    
    @property
    def tokens_saved(self) -> int:
        return self.original_tokens - self.compressed_tokens


@dataclass
class ASTContext:
    """Extracted context from AST without full bodies."""
    
    module_docstring: Optional[str] = None
    imports: List[str] = field(default_factory=list)
    classes: List[Dict[str, Any]] = field(default_factory=list)
    functions: List[Dict[str, Any]] = field(default_factory=list)
    globals: List[str] = field(default_factory=list)


class ContextCompressor:
    """Compresses context to reduce token usage.
    
    Strategies:
    1. AST Pruning: For code files, extract signatures only
    2. Head/Tail Truncation: For tool outputs, keep start/end
    3. Summary Injection: Replace verbose context with summaries
    """
    
    # Thresholds
    MAX_TOOL_OUTPUT_LINES = 50
    HEAD_LINES = 20
    TAIL_LINES = 20
    MAX_FILE_CONTEXT_TOKENS = 2000
    
    # Language extensions that support AST pruning
    AST_LANGUAGES = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "javascript",
        ".tsx": "typescript",
    }
    
    def __init__(self, target_tokens: int = 15_000):
        """Initialize compressor.
        
        Args:
            target_tokens: Target total token count after compression
        """
        self.target_tokens = target_tokens
        self._cache: Dict[str, str] = {}  # Hash -> compressed content
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (4 chars per token average)."""
        return len(text) // 4
    
    def _content_hash(self, content: str) -> str:
        """Generate hash for content caching."""
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    # =========================================================================
    # AST Pruning (Python)
    # =========================================================================
    
    def prune_python_ast(self, source: str, keep_bodies: bool = False) -> str:
        """Extract signatures and docstrings from Python code.
        
        Args:
            source: Python source code
            keep_bodies: If True, keep function bodies (for active files)
            
        Returns:
            Pruned source with signatures and docstrings only
        """
        cache_key = self._content_hash(source) + ("_full" if keep_bodies else "_sig")
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            tree = ast.parse(source)
        except SyntaxError:
            # Can't parse - return truncated version
            return self._truncate_head_tail(source, 50, 20)
        
        result_lines = []
        
        # Module docstring
        if (tree.body and isinstance(tree.body[0], ast.Expr) and 
            isinstance(tree.body[0].value, ast.Constant) and 
            isinstance(tree.body[0].value.value, str)):
            result_lines.append(f'"""{tree.body[0].value.value}"""')
            result_lines.append("")
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = ", ".join(alias.name for alias in node.names)
                result_lines.append(f"import {names}")
                
            elif isinstance(node, ast.ImportFrom):
                names = ", ".join(alias.name for alias in node.names)
                result_lines.append(f"from {node.module or ''} import {names}")
                
            elif isinstance(node, ast.ClassDef):
                # Class signature
                bases = ", ".join(self._get_name(b) for b in node.bases)
                sig = f"class {node.name}({bases}):" if bases else f"class {node.name}:"
                result_lines.append("")
                result_lines.append(sig)
                
                # Class docstring
                docstring = ast.get_docstring(node)
                if docstring:
                    result_lines.append(f'    """{docstring[:200]}..."""' if len(docstring) > 200 else f'    """{docstring}"""')
                
            elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                # Function signature
                prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
                args = self._format_arguments(node.args)
                returns = f" -> {self._get_annotation(node.returns)}" if node.returns else ""
                sig = f"{prefix} {node.name}({args}){returns}:"
                
                # Indentation (method vs function)
                indent = "    " if self._is_method(node, tree) else ""
                result_lines.append(f"{indent}{sig}")
                
                # Docstring
                docstring = ast.get_docstring(node)
                if docstring:
                    doc_indent = indent + "    "
                    if len(docstring) > 200:
                        result_lines.append(f'{doc_indent}"""{docstring[:200]}..."""')
                    else:
                        result_lines.append(f'{doc_indent}"""{docstring}"""')
                
                if not keep_bodies:
                    result_lines.append(f"{indent}    ...")
        
        result = "\n".join(result_lines)
        self._cache[cache_key] = result
        return result
    
    def _get_name(self, node: ast.expr) -> str:
        """Get name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            return f"{self._get_name(node.value)}[...]"
        return "..."
    
    def _get_annotation(self, node: Optional[ast.expr]) -> str:
        """Get type annotation as string."""
        if node is None:
            return ""
        return self._get_name(node)
    
    def _format_arguments(self, args: ast.arguments) -> str:
        """Format function arguments."""
        parts = []
        
        # Regular args
        for arg in args.args:
            ann = f": {self._get_annotation(arg.annotation)}" if arg.annotation else ""
            parts.append(f"{arg.arg}{ann}")
        
        # *args
        if args.vararg:
            ann = f": {self._get_annotation(args.vararg.annotation)}" if args.vararg.annotation else ""
            parts.append(f"*{args.vararg.arg}{ann}")
        
        # **kwargs
        if args.kwarg:
            ann = f": {self._get_annotation(args.kwarg.annotation)}" if args.kwarg.annotation else ""
            parts.append(f"**{args.kwarg.arg}{ann}")
        
        return ", ".join(parts)
    
    def _is_method(self, node: ast.FunctionDef, tree: ast.Module) -> bool:
        """Check if function is a method (inside a class)."""
        for parent in ast.walk(tree):
            if isinstance(parent, ast.ClassDef):
                for child in parent.body:
                    if child is node:
                        return True
        return False
    
    # =========================================================================
    # Head/Tail Truncation
    # =========================================================================
    
    def _truncate_head_tail(
        self,
        content: str,
        head_lines: int = 20,
        tail_lines: int = 20,
    ) -> str:
        """Keep head and tail lines, drop middle.
        
        Args:
            content: Text content to truncate
            head_lines: Number of lines to keep from start
            tail_lines: Number of lines to keep from end
            
        Returns:
            Truncated content with marker
        """
        lines = content.splitlines()
        
        if len(lines) <= head_lines + tail_lines:
            return content
        
        head = lines[:head_lines]
        tail = lines[-tail_lines:]
        dropped = len(lines) - head_lines - tail_lines
        
        return "\n".join([
            *head,
            f"\n... [{dropped} lines truncated] ...\n",
            *tail,
        ])
    
    def compress_tool_output(self, output: str, tool_name: str = "") -> str:
        """Compress tool output using appropriate strategy.
        
        Args:
            output: Tool output content
            tool_name: Name of tool for context-aware compression
            
        Returns:
            Compressed output
        """
        lines = output.splitlines()
        
        if len(lines) <= self.MAX_TOOL_OUTPUT_LINES:
            return output
        
        # For file content, try AST pruning first
        if tool_name in ("read_file", "cat", "view"):
            # Check if it looks like Python
            if "def " in output or "class " in output or "import " in output:
                try:
                    return self.prune_python_ast(output, keep_bodies=False)
                except Exception:
                    pass
        
        # Default to head/tail truncation
        return self._truncate_head_tail(output, self.HEAD_LINES, self.TAIL_LINES)
    
    # =========================================================================
    # File Context Compression
    # =========================================================================
    
    def compress_file_context(
        self,
        filepath: str,
        content: str,
        is_active: bool = False,
    ) -> str:
        """Compress file content based on whether it's actively being edited.
        
        Args:
            filepath: Path to file (for language detection)
            content: File content
            is_active: Whether this file is currently being edited
            
        Returns:
            Compressed content
        """
        # Check cache
        cache_key = self._content_hash(content) + ("_active" if is_active else "_ref")
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Active files get full content (with optional size limit)
        if is_active:
            if self._estimate_tokens(content) > self.MAX_FILE_CONTEXT_TOKENS:
                result = self._truncate_head_tail(content, 100, 50)
            else:
                result = content
            self._cache[cache_key] = result
            return result
        
        # Reference files get AST pruning
        ext = "." + filepath.rsplit(".", 1)[-1] if "." in filepath else ""
        
        if ext == ".py":
            try:
                result = self.prune_python_ast(content, keep_bodies=False)
                self._cache[cache_key] = result
                return result
            except Exception:
                pass
        
        # Fallback: head/tail truncation
        result = self._truncate_head_tail(content, 30, 10)
        self._cache[cache_key] = result
        return result
    
    # =========================================================================
    # Message History Compression
    # =========================================================================
    
    def compress_history(
        self,
        messages: List[Any],
        max_messages: int = 8,
        max_tokens: int = 15_000,
    ) -> Tuple[List[Any], CompressionResult]:
        """Compress message history to fit within token budget.
        
        Args:
            messages: List of message objects
            max_messages: Maximum messages to keep
            max_tokens: Target token budget
            
        Returns:
            (compressed_messages, CompressionResult)
        """
        original_count = len(messages)
        original_tokens = sum(
            self._estimate_tokens(str(m)) for m in messages
        )
        
        if original_tokens <= max_tokens and original_count <= max_messages:
            return messages, CompressionResult(
                original_tokens=original_tokens,
                compressed_tokens=original_tokens,
                compression_ratio=1.0,
                strategy_used="none",
            )
        
        # Strategy 1: Keep only last N messages (sliding window)
        if len(messages) > max_messages:
            # Preserve system message if present
            system_msgs = [m for m in messages if self._is_system_message(m)]
            recent = messages[-(max_messages - len(system_msgs)):]
            messages = system_msgs + recent
        
        # Strategy 2: Compress tool outputs in messages
        for msg in messages:
            if hasattr(msg, "parts"):
                for part in msg.parts:
                    if hasattr(part, "content") and isinstance(part.content, str):
                        if len(part.content) > 1000:
                            part.content = self._truncate_head_tail(
                                part.content, 20, 10
                            )
        
        compressed_tokens = sum(
            self._estimate_tokens(str(m)) for m in messages
        )
        
        return messages, CompressionResult(
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            compression_ratio=compressed_tokens / original_tokens if original_tokens > 0 else 1.0,
            strategy_used="sliding_window+truncate",
        )
    
    def _is_system_message(self, message: Any) -> bool:
        """Check if message is a system message."""
        if hasattr(message, "role"):
            return message.role == "system"
        if hasattr(message, "kind"):
            return message.kind == "system"
        return False
    
    # =========================================================================
    # Batch Compression
    # =========================================================================
    
    def compress_context_batch(
        self,
        files: Dict[str, str],
        active_file: Optional[str] = None,
        target_tokens: Optional[int] = None,
    ) -> Tuple[Dict[str, str], CompressionResult]:
        """Compress multiple files as a batch.
        
        Args:
            files: Dict of filepath -> content
            active_file: Path of currently edited file (gets full content)
            target_tokens: Override target token count
            
        Returns:
            (compressed_files, CompressionResult)
        """
        target = target_tokens or self.target_tokens
        original_tokens = sum(self._estimate_tokens(c) for c in files.values())
        
        compressed = {}
        for path, content in files.items():
            is_active = path == active_file
            compressed[path] = self.compress_file_context(path, content, is_active)
        
        compressed_tokens = sum(self._estimate_tokens(c) for c in compressed.values())
        
        # If still over budget, apply more aggressive truncation
        if compressed_tokens > target:
            for path in list(compressed.keys()):
                if path != active_file:
                    compressed[path] = self._truncate_head_tail(
                        compressed[path], 15, 5
                    )
        
        final_tokens = sum(self._estimate_tokens(c) for c in compressed.values())
        
        return compressed, CompressionResult(
            original_tokens=original_tokens,
            compressed_tokens=final_tokens,
            compression_ratio=final_tokens / original_tokens if original_tokens > 0 else 1.0,
            strategy_used="ast_prune+truncate",
        )
    
    def clear_cache(self) -> None:
        """Clear compression cache."""
        self._cache.clear()

"""GitMCP Client - Access GitHub documentation via GitMCP MCP server.

GitMCP (https://gitmcp.io) is a free, open-source, remote MCP server
that transforms any GitHub project into a documentation hub.

This client provides a Python interface to GitMCP, enabling:
- Documentation fetching for any GitHub repository
- Smart search through documentation
- Code search via GitHub's code search API
- URL content fetching

Usage:
    ```python
    client = GitMCPClient("pydantic", "pydantic-ai")
    
    # Fetch primary documentation
    docs = await client.fetch_documentation()
    
    # Search documentation
    results = await client.search_documentation("context compaction")
    
    # Search code
    code = await client.search_code("def compact_messages")
    ```
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass
class GitMCPConfig:
    """Configuration for GitMCP client."""

    base_url: str = "https://gitmcp.io"
    timeout: float = 30.0
    max_retries: int = 3
    
    # Dynamic mode uses gitmcp.io/docs for any repo
    dynamic_mode: bool = False


@dataclass
class DocumentationResult:
    """Result from fetching documentation."""

    content: str
    source: str  # llms.txt, README.md, etc.
    repository: str
    url: Optional[str] = None


@dataclass
class SearchResult:
    """Result from documentation or code search."""

    content: str
    path: Optional[str] = None
    line_number: Optional[int] = None
    score: float = 0.0
    url: Optional[str] = None


@dataclass
class CodeSearchResult:
    """Result from code search."""

    code: str
    path: str
    repository: str
    line_start: int
    line_end: int
    url: str
    language: Optional[str] = None


class GitMCPClient:
    """Client for accessing GitHub repositories via GitMCP.
    
    GitMCP provides MCP-compatible documentation access for any GitHub
    repository without requiring local cloning.
    """

    def __init__(
        self,
        owner: str,
        repo: str,
        config: Optional[GitMCPConfig] = None,
    ):
        """Initialize GitMCP client.
        
        Args:
            owner: GitHub repository owner (user or org)
            repo: Repository name
            config: Optional configuration
        """
        self.owner = owner
        self.repo = repo
        self.config = config or GitMCPConfig()
        self._http_client: Optional[httpx.AsyncClient] = None
    
    @property
    def base_url(self) -> str:
        """Get the base URL for this repository."""
        if self.config.dynamic_mode:
            return f"{self.config.base_url}/docs"
        return f"{self.config.base_url}/{self.owner}/{self.repo}"
    
    @property
    def mcp_url(self) -> str:
        """Get the MCP server URL for this repository."""
        return self.base_url
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=self.config.timeout,
                follow_redirects=True,
            )
        return self._http_client
    
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
    
    async def fetch_documentation(self) -> DocumentationResult:
        """Fetch primary documentation for the repository.
        
        This retrieves the repository's main documentation, prioritizing:
        1. llms.txt (AI-optimized docs)
        2. AI-optimized documentation pages
        3. README.md
        
        Returns:
            DocumentationResult with the documentation content
        """
        client = await self._get_client()
        
        # Try llms.txt first
        try:
            response = await client.get(
                f"https://raw.githubusercontent.com/{self.owner}/{self.repo}/main/llms.txt"
            )
            if response.status_code == 200:
                return DocumentationResult(
                    content=response.text,
                    source="llms.txt",
                    repository=f"{self.owner}/{self.repo}",
                    url=f"https://github.com/{self.owner}/{self.repo}/blob/main/llms.txt",
                )
        except Exception as e:
            logger.debug(f"llms.txt not found: {e}")
        
        # Fall back to README.md
        try:
            response = await client.get(
                f"https://raw.githubusercontent.com/{self.owner}/{self.repo}/main/README.md"
            )
            if response.status_code == 200:
                return DocumentationResult(
                    content=response.text,
                    source="README.md",
                    repository=f"{self.owner}/{self.repo}",
                    url=f"https://github.com/{self.owner}/{self.repo}#readme",
                )
        except Exception as e:
            logger.debug(f"README.md fetch failed: {e}")
        
        # Try alternate branch names
        for branch in ["master", "develop"]:
            try:
                response = await client.get(
                    f"https://raw.githubusercontent.com/{self.owner}/{self.repo}/{branch}/README.md"
                )
                if response.status_code == 200:
                    return DocumentationResult(
                        content=response.text,
                        source="README.md",
                        repository=f"{self.owner}/{self.repo}",
                        url=f"https://github.com/{self.owner}/{self.repo}#readme",
                    )
            except Exception:
                pass
        
        # Return empty result if nothing found
        return DocumentationResult(
            content="",
            source="none",
            repository=f"{self.owner}/{self.repo}",
        )
    
    async def search_documentation(
        self,
        query: str,
        max_results: int = 10,
    ) -> List[SearchResult]:
        """Search through repository documentation.
        
        Uses GitHub's search to find relevant documentation sections.
        
        Args:
            query: Search query
            max_results: Maximum results to return
            
        Returns:
            List of search results
        """
        client = await self._get_client()
        results = []
        
        # Search in docs/ directory
        try:
            # Use GitHub code search API
            search_url = f"https://api.github.com/search/code?q={query}+repo:{self.owner}/{self.repo}+path:*.md"
            response = await client.get(
                search_url,
                headers={"Accept": "application/vnd.github.v3+json"},
            )
            
            if response.status_code == 200:
                data = response.json()
                for item in data.get("items", [])[:max_results]:
                    results.append(SearchResult(
                        content=item.get("name", ""),
                        path=item.get("path"),
                        url=item.get("html_url"),
                        score=item.get("score", 0.0),
                    ))
        except Exception as e:
            logger.warning(f"Documentation search failed: {e}")
        
        return results
    
    async def search_code(
        self,
        query: str,
        language: Optional[str] = None,
        max_results: int = 10,
    ) -> List[CodeSearchResult]:
        """Search through repository code.
        
        Args:
            query: Search query
            language: Optional language filter
            max_results: Maximum results to return
            
        Returns:
            List of code search results
        """
        client = await self._get_client()
        results = []
        
        try:
            search_query = f"{query}+repo:{self.owner}/{self.repo}"
            if language:
                search_query += f"+language:{language}"
            
            response = await client.get(
                f"https://api.github.com/search/code?q={search_query}",
                headers={"Accept": "application/vnd.github.v3+json"},
            )
            
            if response.status_code == 200:
                data = response.json()
                for item in data.get("items", [])[:max_results]:
                    results.append(CodeSearchResult(
                        code="",  # GitHub API doesn't return full content
                        path=item.get("path", ""),
                        repository=f"{self.owner}/{self.repo}",
                        line_start=0,
                        line_end=0,
                        url=item.get("html_url", ""),
                        language=language,
                    ))
        except Exception as e:
            logger.warning(f"Code search failed: {e}")
        
        return results
    
    async def fetch_file(
        self,
        path: str,
        branch: str = "main",
    ) -> Optional[str]:
        """Fetch a specific file from the repository.
        
        Args:
            path: File path relative to repository root
            branch: Branch name
            
        Returns:
            File content or None if not found
        """
        client = await self._get_client()
        
        try:
            response = await client.get(
                f"https://raw.githubusercontent.com/{self.owner}/{self.repo}/{branch}/{path}"
            )
            if response.status_code == 200:
                return response.text
        except Exception as e:
            logger.warning(f"Failed to fetch {path}: {e}")
        
        return None
    
    async def get_repository_info(self) -> Dict[str, Any]:
        """Get repository metadata.
        
        Returns:
            Repository information including description, stars, etc.
        """
        client = await self._get_client()
        
        try:
            response = await client.get(
                f"https://api.github.com/repos/{self.owner}/{self.repo}",
                headers={"Accept": "application/vnd.github.v3+json"},
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.warning(f"Failed to get repo info: {e}")
        
        return {}


class GitMCPDynamicClient(GitMCPClient):
    """Dynamic GitMCP client for accessing any repository.
    
    Uses the gitmcp.io/docs endpoint which allows the AI to specify
    the repository dynamically.
    """

    def __init__(self, config: Optional[GitMCPConfig] = None):
        config = config or GitMCPConfig(dynamic_mode=True)
        super().__init__("", "", config)
    
    async def fetch_documentation_for(
        self,
        owner: str,
        repo: str,
    ) -> DocumentationResult:
        """Fetch documentation for a specific repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Documentation result
        """
        self.owner = owner
        self.repo = repo
        return await self.fetch_documentation()
    
    async def search_documentation_for(
        self,
        owner: str,
        repo: str,
        query: str,
        max_results: int = 10,
    ) -> List[SearchResult]:
        """Search documentation for a specific repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            query: Search query
            max_results: Maximum results
            
        Returns:
            Search results
        """
        self.owner = owner
        self.repo = repo
        return await self.search_documentation(query, max_results)


def get_gitmcp_mcp_config(owner: str, repo: str) -> Dict[str, Any]:
    """Get MCP server configuration for GitMCP.
    
    Returns configuration suitable for adding to mcp_servers.json.
    
    Args:
        owner: Repository owner
        repo: Repository name
        
    Returns:
        MCP server configuration dict
    """
    return {
        "gitmcp": {
            "url": f"https://gitmcp.io/{owner}/{repo}",
            "description": f"Documentation access for {owner}/{repo}",
        }
    }


def get_dynamic_gitmcp_config() -> Dict[str, Any]:
    """Get MCP server configuration for dynamic GitMCP.
    
    Returns:
        MCP server configuration for the dynamic endpoint
    """
    return {
        "gitmcp-dynamic": {
            "url": "https://gitmcp.io/docs",
            "description": "Dynamic documentation access for any GitHub repository",
        }
    }

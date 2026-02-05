"""GitHub API Client - Python equivalent of Octokit.js.

Provides a complete GitHub SDK for Python with:
- REST API client with typed methods
- GraphQL API support
- Pagination handling
- Rate limit management
- Authentication strategies
- Retry logic

This replaces the need for Octokit.js in Python projects.

Usage:
    ```python
    from code_puppy.api.github_client import GitHubClient
    
    # Personal access token
    client = GitHubClient(auth="ghp_xxxxxxxxxxxx")
    
    # Get authenticated user
    user = await client.rest.users.get_authenticated()
    print(f"Hello, {user['login']}")
    
    # Create an issue
    issue = await client.rest.issues.create(
        owner="octocat",
        repo="hello-world",
        title="Hello from Code Puppy!",
    )
    
    # GraphQL query
    result = await client.graphql('''
        query {
            viewer {
                login
            }
        }
    ''')
    ```
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, TypeVar, Union

import httpx

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class RateLimitInfo:
    """GitHub API rate limit information."""

    limit: int
    remaining: int
    reset_timestamp: int
    used: int
    
    @classmethod
    def from_headers(cls, headers: httpx.Headers) -> "RateLimitInfo":
        return cls(
            limit=int(headers.get("x-ratelimit-limit", 0)),
            remaining=int(headers.get("x-ratelimit-remaining", 0)),
            reset_timestamp=int(headers.get("x-ratelimit-reset", 0)),
            used=int(headers.get("x-ratelimit-used", 0)),
        )
    
    @property
    def is_exceeded(self) -> bool:
        return self.remaining <= 0
    
    @property
    def reset_in_seconds(self) -> int:
        return max(0, self.reset_timestamp - int(time.time()))


@dataclass
class RequestError(Exception):
    """Error from GitHub API request."""

    status: int
    message: str
    documentation_url: Optional[str] = None
    errors: List[Dict[str, Any]] = field(default_factory=list)


class AuthStrategy:
    """Base authentication strategy."""

    async def get_auth_header(self) -> Dict[str, str]:
        raise NotImplementedError


class TokenAuth(AuthStrategy):
    """Personal access token authentication."""

    def __init__(self, token: str):
        self.token = token
    
    async def get_auth_header(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}


class GitHubAppAuth(AuthStrategy):
    """GitHub App authentication (JWT)."""

    def __init__(self, app_id: int, private_key: str):
        self.app_id = app_id
        self.private_key = private_key
        self._jwt_cache: Optional[tuple[str, float]] = None
    
    async def get_auth_header(self) -> Dict[str, str]:
        jwt_token = await self._get_or_refresh_jwt()
        return {"Authorization": f"Bearer {jwt_token}"}
    
    async def _get_or_refresh_jwt(self) -> str:
        """Get or refresh the JWT token."""
        import jwt
        
        now = time.time()
        
        # Check cache
        if self._jwt_cache:
            token, expiry = self._jwt_cache
            if now < expiry - 60:  # Refresh 1 min before expiry
                return token
        
        # Generate new JWT
        payload = {
            "iat": int(now),
            "exp": int(now + 600),  # 10 minutes
            "iss": self.app_id,
        }
        
        token = jwt.encode(payload, self.private_key, algorithm="RS256")
        self._jwt_cache = (token, now + 600)
        
        return token


@dataclass
class ClientConfig:
    """GitHub client configuration."""

    base_url: str = "https://api.github.com"
    user_agent: str = "code-puppy-github-client/1.0"
    timeout: float = 30.0
    max_retries: int = 3
    retry_on_rate_limit: bool = True
    preview_features: List[str] = field(default_factory=list)


class RestEndpoint:
    """REST API endpoint wrapper."""

    def __init__(self, client: "GitHubClient", path_prefix: str = ""):
        self._client = client
        self._path_prefix = path_prefix
    
    async def _request(
        self,
        method: str,
        path: str,
        **kwargs,
    ) -> Any:
        """Make a REST API request."""
        return await self._client._request(method, path, **kwargs)


class UsersEndpoint(RestEndpoint):
    """Users REST API endpoints."""

    async def get_authenticated(self) -> Dict[str, Any]:
        """Get the authenticated user."""
        return await self._request("GET", "/user")
    
    async def get(self, username: str) -> Dict[str, Any]:
        """Get a user by username."""
        return await self._request("GET", f"/users/{username}")
    
    async def list_followers(
        self,
        username: Optional[str] = None,
        per_page: int = 30,
    ) -> List[Dict[str, Any]]:
        """List followers for a user."""
        path = f"/users/{username}/followers" if username else "/user/followers"
        return await self._request("GET", path, params={"per_page": per_page})


class ReposEndpoint(RestEndpoint):
    """Repositories REST API endpoints."""

    async def get(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get a repository."""
        return await self._request("GET", f"/repos/{owner}/{repo}")
    
    async def list_for_user(
        self,
        username: str,
        per_page: int = 30,
        sort: str = "updated",
    ) -> List[Dict[str, Any]]:
        """List repositories for a user."""
        return await self._request(
            "GET",
            f"/users/{username}/repos",
            params={"per_page": per_page, "sort": sort},
        )
    
    async def list_for_authenticated_user(
        self,
        per_page: int = 30,
        visibility: str = "all",
    ) -> List[Dict[str, Any]]:
        """List repositories for the authenticated user."""
        return await self._request(
            "GET",
            "/user/repos",
            params={"per_page": per_page, "visibility": visibility},
        )
    
    async def get_content(
        self,
        owner: str,
        repo: str,
        path: str,
        ref: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get repository content."""
        params = {"ref": ref} if ref else {}
        return await self._request(
            "GET",
            f"/repos/{owner}/{repo}/contents/{path}",
            params=params,
        )
    
    async def create_dispatch_event(
        self,
        owner: str,
        repo: str,
        event_type: str,
        client_payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Create a repository dispatch event."""
        await self._request(
            "POST",
            f"/repos/{owner}/{repo}/dispatches",
            json={"event_type": event_type, "client_payload": client_payload or {}},
        )


class IssuesEndpoint(RestEndpoint):
    """Issues REST API endpoints."""

    async def get(self, owner: str, repo: str, issue_number: int) -> Dict[str, Any]:
        """Get an issue."""
        return await self._request("GET", f"/repos/{owner}/{repo}/issues/{issue_number}")
    
    async def create(
        self,
        owner: str,
        repo: str,
        title: str,
        body: Optional[str] = None,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create an issue."""
        data = {"title": title}
        if body:
            data["body"] = body
        if labels:
            data["labels"] = labels
        if assignees:
            data["assignees"] = assignees
        
        return await self._request(
            "POST",
            f"/repos/{owner}/{repo}/issues",
            json=data,
        )
    
    async def list_for_repo(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        per_page: int = 30,
    ) -> List[Dict[str, Any]]:
        """List issues for a repository."""
        return await self._request(
            "GET",
            f"/repos/{owner}/{repo}/issues",
            params={"state": state, "per_page": per_page},
        )
    
    async def create_comment(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        body: str,
    ) -> Dict[str, Any]:
        """Create a comment on an issue."""
        return await self._request(
            "POST",
            f"/repos/{owner}/{repo}/issues/{issue_number}/comments",
            json={"body": body},
        )


class PullsEndpoint(RestEndpoint):
    """Pull Requests REST API endpoints."""

    async def get(self, owner: str, repo: str, pull_number: int) -> Dict[str, Any]:
        """Get a pull request."""
        return await self._request("GET", f"/repos/{owner}/{repo}/pulls/{pull_number}")
    
    async def create(
        self,
        owner: str,
        repo: str,
        title: str,
        head: str,
        base: str,
        body: Optional[str] = None,
        draft: bool = False,
    ) -> Dict[str, Any]:
        """Create a pull request."""
        data = {
            "title": title,
            "head": head,
            "base": base,
            "draft": draft,
        }
        if body:
            data["body"] = body
        
        return await self._request(
            "POST",
            f"/repos/{owner}/{repo}/pulls",
            json=data,
        )
    
    async def list_for_repo(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        per_page: int = 30,
    ) -> List[Dict[str, Any]]:
        """List pull requests for a repository."""
        return await self._request(
            "GET",
            f"/repos/{owner}/{repo}/pulls",
            params={"state": state, "per_page": per_page},
        )
    
    async def merge(
        self,
        owner: str,
        repo: str,
        pull_number: int,
        commit_title: Optional[str] = None,
        commit_message: Optional[str] = None,
        merge_method: str = "merge",
    ) -> Dict[str, Any]:
        """Merge a pull request."""
        data = {"merge_method": merge_method}
        if commit_title:
            data["commit_title"] = commit_title
        if commit_message:
            data["commit_message"] = commit_message
        
        return await self._request(
            "PUT",
            f"/repos/{owner}/{repo}/pulls/{pull_number}/merge",
            json=data,
        )


class ActionsEndpoint(RestEndpoint):
    """GitHub Actions REST API endpoints."""

    async def list_workflows(
        self,
        owner: str,
        repo: str,
        per_page: int = 30,
    ) -> Dict[str, Any]:
        """List workflows for a repository."""
        return await self._request(
            "GET",
            f"/repos/{owner}/{repo}/actions/workflows",
            params={"per_page": per_page},
        )
    
    async def list_workflow_runs(
        self,
        owner: str,
        repo: str,
        workflow_id: Optional[Union[int, str]] = None,
        per_page: int = 30,
    ) -> Dict[str, Any]:
        """List workflow runs."""
        if workflow_id:
            path = f"/repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs"
        else:
            path = f"/repos/{owner}/{repo}/actions/runs"
        
        return await self._request("GET", path, params={"per_page": per_page})
    
    async def dispatch_workflow(
        self,
        owner: str,
        repo: str,
        workflow_id: Union[int, str],
        ref: str,
        inputs: Optional[Dict[str, str]] = None,
    ) -> None:
        """Dispatch a workflow run."""
        data = {"ref": ref}
        if inputs:
            data["inputs"] = inputs
        
        await self._request(
            "POST",
            f"/repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches",
            json=data,
        )


class SearchEndpoint(RestEndpoint):
    """Search REST API endpoints."""

    async def code(
        self,
        query: str,
        per_page: int = 30,
    ) -> Dict[str, Any]:
        """Search code."""
        return await self._request(
            "GET",
            "/search/code",
            params={"q": query, "per_page": per_page},
        )
    
    async def issues_and_pull_requests(
        self,
        query: str,
        per_page: int = 30,
    ) -> Dict[str, Any]:
        """Search issues and pull requests."""
        return await self._request(
            "GET",
            "/search/issues",
            params={"q": query, "per_page": per_page},
        )
    
    async def repositories(
        self,
        query: str,
        sort: Optional[str] = None,
        per_page: int = 30,
    ) -> Dict[str, Any]:
        """Search repositories."""
        params = {"q": query, "per_page": per_page}
        if sort:
            params["sort"] = sort
        return await self._request("GET", "/search/repositories", params=params)


class RestAPI:
    """REST API namespace."""

    def __init__(self, client: "GitHubClient"):
        self.users = UsersEndpoint(client)
        self.repos = ReposEndpoint(client)
        self.issues = IssuesEndpoint(client)
        self.pulls = PullsEndpoint(client)
        self.actions = ActionsEndpoint(client)
        self.search = SearchEndpoint(client)


class GitHubClient:
    """GitHub API client - Python equivalent of Octokit.js.
    
    Provides complete access to GitHub's REST and GraphQL APIs.
    """

    def __init__(
        self,
        auth: Optional[Union[str, AuthStrategy]] = None,
        config: Optional[ClientConfig] = None,
    ):
        """Initialize GitHub client.
        
        Args:
            auth: Authentication - string token or AuthStrategy
            config: Client configuration
        """
        self.config = config or ClientConfig()
        
        # Set up authentication
        if isinstance(auth, str):
            self._auth = TokenAuth(auth)
        elif isinstance(auth, AuthStrategy):
            self._auth = auth
        else:
            self._auth = None
        
        self._http_client: Optional[httpx.AsyncClient] = None
        self._rate_limit: Optional[RateLimitInfo] = None
        
        # REST API namespace
        self.rest = RestAPI(self)
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                follow_redirects=True,
            )
        return self._http_client
    
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
    
    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Make an API request with retry logic."""
        client = await self._get_client()
        
        # Build headers
        request_headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": self.config.user_agent,
            "X-GitHub-Api-Version": "2022-11-28",
        }
        
        # Add preview features
        if self.config.preview_features:
            accept = "application/vnd.github+json"
            for feature in self.config.preview_features:
                accept += f", application/vnd.github.{feature}+json"
            request_headers["Accept"] = accept
        
        # Add auth
        if self._auth:
            request_headers.update(await self._auth.get_auth_header())
        
        if headers:
            request_headers.update(headers)
        
        # Retry loop
        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                response = await client.request(
                    method,
                    path,
                    params=params,
                    json=json,
                    headers=request_headers,
                )
                
                # Update rate limit info
                self._rate_limit = RateLimitInfo.from_headers(response.headers)
                
                # Handle rate limit
                if response.status_code == 403 and self._rate_limit.is_exceeded:
                    if self.config.retry_on_rate_limit:
                        wait_time = self._rate_limit.reset_in_seconds + 1
                        logger.warning(f"Rate limited, waiting {wait_time}s")
                        await asyncio.sleep(wait_time)
                        continue
                
                # Handle success
                if response.status_code < 400:
                    if response.status_code == 204:
                        return None
                    return response.json()
                
                # Handle error
                error_data = response.json() if response.content else {}
                raise RequestError(
                    status=response.status_code,
                    message=error_data.get("message", response.reason_phrase),
                    documentation_url=error_data.get("documentation_url"),
                    errors=error_data.get("errors", []),
                )
                
            except RequestError:
                raise
            except Exception as e:
                last_error = e
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
        
        raise last_error or Exception("Request failed")
    
    async def graphql(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute a GraphQL query.
        
        Args:
            query: GraphQL query string
            variables: Optional query variables
            
        Returns:
            Query result data
        """
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        result = await self._request("POST", "/graphql", json=payload)
        
        if "errors" in result:
            error_messages = [e.get("message", str(e)) for e in result["errors"]]
            raise RequestError(
                status=400,
                message="; ".join(error_messages),
            )
        
        return result.get("data", {})
    
    async def paginate(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        per_page: int = 100,
    ) -> AsyncIterator[Any]:
        """Paginate through all results.
        
        Args:
            method: HTTP method
            path: API path
            params: Query parameters
            per_page: Items per page (max 100)
            
        Yields:
            Items from all pages
        """
        params = params or {}
        params["per_page"] = per_page
        page = 1
        
        while True:
            params["page"] = page
            result = await self._request(method, path, params=params)
            
            # Handle list response
            if isinstance(result, list):
                if not result:
                    break
                for item in result:
                    yield item
                if len(result) < per_page:
                    break
            # Handle dict with items
            elif isinstance(result, dict) and "items" in result:
                items = result["items"]
                if not items:
                    break
                for item in items:
                    yield item
                if len(items) < per_page:
                    break
            else:
                yield result
                break
            
            page += 1
    
    @property
    def rate_limit(self) -> Optional[RateLimitInfo]:
        """Get current rate limit info."""
        return self._rate_limit


# Convenience function
def create_github_client(
    token: Optional[str] = None,
    app_id: Optional[int] = None,
    private_key: Optional[str] = None,
) -> GitHubClient:
    """Create a GitHub client with appropriate authentication.
    
    Args:
        token: Personal access token
        app_id: GitHub App ID (requires private_key)
        private_key: GitHub App private key
        
    Returns:
        Configured GitHubClient
    """
    import os
    
    # Try environment variables if not provided
    if token is None:
        token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    
    if token:
        return GitHubClient(auth=token)
    
    if app_id and private_key:
        return GitHubClient(auth=GitHubAppAuth(app_id, private_key))
    
    # No auth - limited API access
    return GitHubClient()

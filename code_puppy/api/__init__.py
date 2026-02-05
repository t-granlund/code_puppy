"""Code Puppy REST API module.

This module provides a FastAPI-based REST API for Code Puppy configuration,
sessions, commands, and real-time WebSocket communication.

Exports:
    create_app: Factory function to create the FastAPI application
    main: Entry point to run the server
    GitHubClient: Python client for GitHub REST and GraphQL APIs (Octokit.js equivalent)
"""

from code_puppy.api.app import create_app
from code_puppy.api.github_client import (
    GitHubClient,
    RequestError,
    RateLimitInfo,
    TokenAuth,
    GitHubAppAuth,
    ClientConfig,
    create_github_client,
)

__all__ = [
    "create_app",
    # GitHub API Client (Octokit.js equivalent)
    "GitHubClient",
    "RequestError",
    "RateLimitInfo",
    "TokenAuth",
    "GitHubAppAuth",
    "ClientConfig",
    "create_github_client",
]

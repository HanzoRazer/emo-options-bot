# api/__init__.py
"""
REST API Package
RESTful API server for the EMO Options Bot AI Agent.
"""

from .rest_server import app, serve, update_state

__all__ = [
    "app",
    "serve", 
    "update_state"
]
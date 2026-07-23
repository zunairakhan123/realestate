"""
API Client Module

Handles all HTTP communication with the FastAPI backend.
Automatically attaches JWT Bearer tokens and handles error parsing.
"""

from typing import Any, Dict, Optional
import httpx
import streamlit as st

from config import BACKEND_API_URL


class APIClient:
    """Encapsulates backend communication."""

    @staticmethod
    def _get_headers() -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        token = st.session_state.get("access_token")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    @classmethod
    def post(cls, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{BACKEND_API_URL}{endpoint}"
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, json=data, headers=cls._get_headers())
                if response.status_code >= 400:
                    return {"error": response.json().get("detail", "An error occurred.")}
                return response.json()
        except httpx.RequestError as exc:
            return {"error": f"Failed to connect to backend: {exc}"}

    @classmethod
    def get(cls, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{BACKEND_API_URL}{endpoint}"
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(url, params=params, headers=cls._get_headers())
                if response.status_code >= 400:
                    return {"error": response.json().get("detail", "An error occurred.")}
                return response.json()
        except httpx.RequestError as exc:
            return {"error": f"Failed to connect to backend: {exc}"}
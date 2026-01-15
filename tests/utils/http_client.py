"""
HTTP Test Client for gitwebhooks

This module provides a simple HTTP client for sending webhook requests
during testing. Uses only Python standard library (http.client).
"""

import http.client
import json
import socket
import ssl
import urllib.parse
from typing import Optional, Dict, Any


class TestHttpResponse:
    """
    HTTP response object for testing.

    Attributes:
        status_code: HTTP status code (e.g., 200, 404, 500)
        body: Response body as bytes
        headers: dict of response headers
        reason: HTTP reason phrase (e.g., "OK", "Not Found")
    """

    def __init__(self, status_code: int, body: bytes,
                 headers: Dict[str, str], reason: str = ""):
        """
        Initialize HTTP response.

        Args:
            status_code: HTTP status code
            body: Response body bytes
            headers: Response headers dictionary
            reason: HTTP reason phrase
        """
        self.status_code = status_code
        self.body = body
        self.headers = headers
        self.reason = reason

    @property
    def text(self) -> str:
        """Get response body as text."""
        return self.body.decode('utf-8', errors='replace')

    def json(self) -> Dict[str, Any]:
        """
        Parse response body as JSON.

        Returns:
            Parsed JSON as dictionary

        Raises:
            json.JSONDecodeError: If body is not valid JSON
        """
        return json.loads(self.text)

    def __repr__(self) -> str:
        return f"TestHttpResponse(status_code={self.status_code}, body_length={len(self.body)})"


class TestWebhookClient:
    """
    HTTP client for sending webhook requests in tests.

    This client supports both HTTP and HTTPS connections and can send
    POST requests with custom headers and JSON payloads.

    Usage:
        client = TestWebhookClient("localhost", 8080)
        response = client.send_webhook(
            headers={"X-GitHub-Event": "push"},
            payload={"repository": {"full_name": "owner/repo"}}
        )
        assert response.status_code == 200
    """

    def __init__(self, host: str, port: int, use_ssl: bool = False,
                 timeout: int = 10):
        """
        Initialize webhook client.

        Args:
            host: Server hostname or IP address
            port: Server port number
            use_ssl: Whether to use HTTPS
            timeout: Request timeout in seconds
        """
        self.host = host
        self.port = port
        self.use_ssl = use_ssl
        self.timeout = timeout
        self._conn = None

    def _get_connection(self):
        """
        Create HTTP connection.

        Returns:
            HTTPConnection or HTTPSConnection
        """
        if self._conn is None:
            if self.use_ssl:
                # Create context that doesn't verify certificates for testing
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                self._conn = http.client.HTTPSConnection(
                    self.host, self.port, context=context, timeout=self.timeout
                )
            else:
                self._conn = http.client.HTTPConnection(
                    self.host, self.port, timeout=self.timeout
                )
        return self._conn

    def _close_connection(self):
        """Close the HTTP connection."""
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None

    def send_webhook(
        self,
        path: str = "/",
        headers: Optional[Dict[str, str]] = None,
        payload: Optional[Dict[str, Any]] = None,
        content_type: str = "application/json"
    ) -> TestHttpResponse:
        """
        Send POST webhook request.

        Args:
            path: Request path (default: "/")
            headers: Request headers dictionary
            payload: Request body as dictionary (will be JSON serialized)
            content_type: Content-Type header value

        Returns:
            TestHttpResponse: Response object
        """
        conn = self._get_connection()

        # Prepare headers
        if headers is None:
            headers = {}
        request_headers = dict(headers)
        request_headers['Content-Type'] = content_type

        # Prepare body
        body_bytes = b""
        if payload is not None:
            if content_type == "application/json":
                body_bytes = json.dumps(payload).encode('utf-8')
            else:
                body_bytes = str(payload).encode('utf-8')

        try:
            # Send request
            conn.request("POST", path, body=body_bytes, headers=request_headers)

            # Get response
            response = conn.getresponse()
            response_body = response.read()
            response_headers = dict(response.getheaders())

            return TestHttpResponse(
                status_code=response.status,
                body=response_body,
                headers=response_headers,
                reason=response.reason
            )

        except (socket.error, http.client.HTTPException) as e:
            # Return error response
            return TestHttpResponse(
                status_code=0,
                body=str(e).encode('utf-8'),
                headers={},
                reason="Connection Error"
            )
        finally:
            self._close_connection()

    def send_get(self, path: str = "/") -> TestHttpResponse:
        """
        Send GET request (should return 403 for webhook server).

        Args:
            path: Request path (default: "/")

        Returns:
            TestHttpResponse: Response object
        """
        conn = self._get_connection()

        try:
            conn.request("GET", path)
            response = conn.getresponse()
            response_body = response.read()
            response_headers = dict(response.getheaders())

            return TestHttpResponse(
                status_code=response.status,
                body=response_body,
                headers=response_headers,
                reason=response.reason
            )

        except (socket.error, http.client.HTTPException) as e:
            return TestHttpResponse(
                status_code=0,
                body=str(e).encode('utf-8'),
                headers={},
                reason="Connection Error"
            )
        finally:
            self._close_connection()

    def send_raw(
        self,
        method: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[bytes] = None
    ) -> TestHttpResponse:
        """
        Send raw HTTP request.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            path: Request path
            headers: Request headers
            body: Request body as bytes

        Returns:
            TestHttpResponse: Response object
        """
        conn = self._get_connection()

        try:
            conn.request(method, path, body=body, headers=headers or {})
            response = conn.getresponse()
            response_body = response.read()
            response_headers = dict(response.getheaders())

            return TestHttpResponse(
                status_code=response.status,
                body=response_body,
                headers=response_headers,
                reason=response.reason
            )

        except (socket.error, http.client.HTTPException) as e:
            return TestHttpResponse(
                status_code=0,
                body=str(e).encode('utf-8'),
                headers={},
                reason="Connection Error"
            )
        finally:
            self._close_connection()

    def send_form_urlencoded(
        self,
        path: str = "/",
        data: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> TestHttpResponse:
        """
        Send POST request with form-urlencoded data.

        Args:
            path: Request path
            data: Form data dictionary
            headers: Additional headers

        Returns:
            TestHttpResponse: Response object
        """
        if headers is None:
            headers = {}

        request_headers = dict(headers)
        request_headers['Content-Type'] = 'application/x-www-form-urlencoded'

        body_bytes = b""
        if data:
            body_bytes = urllib.parse.urlencode(data).encode('utf-8')

        return self.send_raw("POST", path, request_headers, body_bytes)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self._close_connection()

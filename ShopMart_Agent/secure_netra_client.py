
import httpx
import time
import uuid
import hashlib
import hmac
import json
import os
import platform
from datetime import datetime

class ProfessionalNetraClient:
    """
    A high-fidelity Enterprise Network Client that simulates:
    1. Browser/Professional User-Agents
    2. Netra Protocol Security Headers (Signatures, DIDs)
    3. Proper HTTP Context (Trace IDs, Timestamps, Content-Types)
    """
    
    def __init__(self, base_url, api_key):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        # Simulate a distinct, persistent Identity for this Agent
        self.client_did = f"did:netra:shopmart-agent-{str(uuid.uuid4())[:8]}"
        
        # Rotate User Agents or use a fixed robust one
        self.user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36 "
            "Netra-ShopMart-Agent/2.1 (Enterprise)"
        )

    def _generate_signature(self, payload_str: str, timestamp: str):
        """
        Creates a Professional HMAC Signature to prove request integrity.
        This simulates the 'Signed Request' requirement.
        """
        # Canonical Data String
        data = f"{self.client_did}.{timestamp}.{payload_str}"
        
        # Sign with API Key
        signature = hmac.new(
            self.api_key.encode("utf-8"), 
            data.encode("utf-8"), 
            hashlib.sha256
        ).hexdigest()
        return signature

    def _get_headers(self, payload: dict = None, custom_headers: dict = None):
        """
        Constructs a full suite of professional headers.
        """
        headers = custom_headers.copy() if custom_headers else {}
        
        # 0. Basic Context
        now_iso = datetime.utcnow().isoformat() + "Z"
        unix_ts = str(int(time.time()))
        req_id = str(uuid.uuid4())
        
        # 1. Standard Protocol Headers
        headers.update({
            "User-Agent": self.user_agent,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "DNT": "1", # Do Not Track
            
            # Tracing
            "X-Request-ID": req_id,
            "X-Correlation-ID": req_id,
            "Date": now_iso,
        })

        # 2. Netra Protocol Headers (The critical part for "Missing Auth Headers")
        headers.update({
            "X-Netra-Client-ID": self.client_did,
            "X-Netra-Timestamp": unix_ts,
            "X-Netra-Version": "2.0.0",
            # Often proxies check Authorization too
            "Authorization": f"Bearer {self.api_key}"
        })

        # 3. Payload Signing (If Body exists)
        if payload is not None:
            # Deterministic serialization for signing
            payload_str = json.dumps(payload, sort_keys=True)
            
            # Generate Sig
            sig = self._generate_signature(payload_str, unix_ts)
            
            headers["X-Netra-Signature"] = sig
            headers["Content-Type"] = "application/json"
            # Optional: Content-Length is auto-added by httpx usually, but good to be explicit if simulating
            # headers["Content-Length"] = str(len(payload_str.encode("utf-8"))) # Let httpx handle this to avoid mismatch
        
        return headers

    async def get(self, endpoint, headers=None):
        """Professional GET Request"""
        # Handle absolute or relative URLs
        if endpoint.startswith("http"):
            url = endpoint
        else:
            url = f"{self.base_url}{endpoint}"
            
        final_headers = self._get_headers(payload=None, custom_headers=headers)
        
        print(f"📡 [SECURE CLIENT] GET {url}")
        async with httpx.AsyncClient(timeout=15.0, verify=False) as client:
            return await client.get(url, headers=final_headers)

    async def post(self, endpoint, json_payload, headers=None):
        """Professional POST Request with Signing"""
        if endpoint.startswith("http"):
            url = endpoint
        else:
            url = f"{self.base_url}{endpoint}"
        
        # Pass existing headers (like X-API-KEY from calling code) to be merged
        final_headers = self._get_headers(payload=json_payload, custom_headers=headers)
        
        print(f"📡 [SECURE CLIENT] POST {url}")
        async with httpx.AsyncClient(timeout=15.0, verify=False) as client:
            return await client.post(url, json=json_payload, headers=final_headers)

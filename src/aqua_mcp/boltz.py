"""Boltz Exchange integration for submarine swaps (L-BTC -> Lightning)."""

import hashlib
import json
import secrets
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from typing import Optional

import coincurve

BOLTZ_API = {
    "mainnet": "https://api.boltz.exchange",
    "testnet": "https://api.testnet.boltz.exchange",
}


@dataclass
class SwapInfo:
    """Holds all data for an active/completed submarine swap."""

    swap_id: str
    address: str
    expected_amount: int
    claim_public_key: str
    swap_tree: dict
    timeout_block_height: int
    refund_private_key: str
    refund_public_key: str
    invoice: str
    status: str
    network: str
    created_at: str
    lockup_txid: Optional[str] = None
    preimage: Optional[str] = None
    claim_txid: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


class BoltzClient:
    """HTTP client for Boltz API v2."""

    def __init__(self, network: str = "mainnet"):
        self.base_url = BOLTZ_API[network]
        self.network = network

    def _api_request(self, method: str, path: str, body: dict | None = None) -> dict:
        """Make HTTP request to Boltz API."""
        url = f"{self.base_url}{path}"
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(
            url,
            data=data,
            method=method,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "aqua-mcp",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())

    def get_submarine_pairs(self) -> dict:
        """GET /v2/swap/submarine - fetch available pairs, fees, limits."""
        return self._api_request("GET", "/v2/swap/submarine")

    def create_submarine_swap(self, invoice: str, refund_public_key: str) -> dict:
        """POST /v2/swap/submarine - create a new swap."""
        return self._api_request("POST", "/v2/swap/submarine", {
            "invoice": invoice,
            "from": "L-BTC",
            "to": "BTC",
            "refundPublicKey": refund_public_key,
        })

    def get_swap_status(self, swap_id: str) -> dict:
        """GET /v2/swap/{swap_id} - get current swap status."""
        return self._api_request("GET", f"/v2/swap/{swap_id}")

    def get_claim_details(self, swap_id: str) -> dict:
        """GET /v2/swap/submarine/{swap_id}/claim - get preimage after invoice paid."""
        return self._api_request("GET", f"/v2/swap/submarine/{swap_id}/claim")


def generate_keypair() -> tuple[str, str]:
    """Generate ephemeral secp256k1 keypair for refund.

    Returns (private_key_hex, public_key_hex).
    """
    privkey = secrets.token_bytes(32)
    pubkey = coincurve.PublicKey.from_secret(privkey)
    return privkey.hex(), pubkey.format(compressed=True).hex()


def verify_preimage(preimage_hex: str, expected_hash_hex: str) -> bool:
    """Verify SHA256(preimage) == expected_hash. Pure stdlib."""
    preimage = bytes.fromhex(preimage_hex)
    computed = hashlib.sha256(preimage).hexdigest()
    return computed == expected_hash_hex.lower()

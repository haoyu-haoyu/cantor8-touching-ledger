from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


@dataclass(frozen=True)
class Ed25519KeyPair:
    private_key_hex: str
    public_key_hex: str

    @classmethod
    def generate(cls) -> "Ed25519KeyPair":
        private_key = Ed25519PrivateKey.generate()
        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )
        public_bytes = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return cls(private_key_hex=private_bytes.hex(), public_key_hex=public_bytes.hex())

    @classmethod
    def load(cls, path: Path) -> "Ed25519KeyPair":
        body = json.loads(path.read_text())
        return cls(
            private_key_hex=body["private_key_hex"],
            public_key_hex=body["public_key_hex"],
        )

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "private_key_hex": self.private_key_hex,
                    "public_key_hex": self.public_key_hex,
                },
                indent=2,
            )
            + "\n"
        )
        path.chmod(0o600)

    def sign_hash_hex(self, hash_hex: str) -> str:
        private_key = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(self.private_key_hex))
        return private_key.sign(bytes.fromhex(hash_hex)).hex()


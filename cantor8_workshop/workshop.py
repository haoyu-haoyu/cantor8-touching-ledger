from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from .client import ApiClient
from .crypto import Ed25519KeyPair
from .errors import WorkshopError
from .payloads import (
    TRANSFER_PREAPPROVAL_PROPOSAL_TEMPLATE_ID,
    TRANSFER_PREAPPROVAL_TEMPLATE_ID,
    build_active_contracts_request,
    build_allocate_party_request,
    build_preapproval_proposal_request,
    build_signed_topology_request,
)


class Workshop:
    def __init__(self, api: ApiClient, output_dir: Path | str = ".") -> None:
        self.api = api
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def authenticated_user_id(self) -> str:
        body = self.api.ledger("GET", "/v2/authenticated-user")
        return body["user"]["id"]

    def create_internal_party(self, party_hint: str, user_id: str | None = None) -> str:
        payload = build_allocate_party_request(party_hint, user_id)
        body = self.api.ledger("POST", "/v2/parties", json=payload)
        party_id = body["partyDetails"]["party"]
        (self.output_dir / "partyid.txt").write_text(f"{party_id}\n")
        print(f"partyId={party_id}")
        return party_id

    def discover_provider_context(self) -> tuple[str, str]:
        body = self.api.validator("GET", "/v0/admin/transfer-preapprovals")
        contracts = body.get("contracts", [])
        for item in contracts:
            payload = item.get("contract", {}).get("payload", {})
            provider = payload.get("provider")
            dso = payload.get("dso")
            if provider and dso:
                print(f"providerParty={provider}")
                print(f"dsoParty={dso}")
                return provider, dso
        raise WorkshopError(
            "Could not infer provider/dso parties from /v0/admin/transfer-preapprovals. "
            "Set CANTON_PROVIDER_PARTY and CANTON_DSO_PARTY."
        )

    def setup_external_party_topology(
        self, party_hint: str, key_path: Path | str | None = None
    ) -> str:
        key_path = Path(key_path or self.output_dir / "external_party_key.json")
        if key_path.exists():
            key_pair = Ed25519KeyPair.load(key_path)
            print(f"usingExistingKey={key_path}")
        else:
            key_pair = Ed25519KeyPair.generate()
            key_pair.save(key_path)
            print(f"createdKey={key_path}")

        generated = self.api.validator(
            "POST",
            "/v0/admin/external-party/topology/generate",
            json={"party_hint": party_hint, "public_key": key_pair.public_key_hex},
        )
        signed_transactions = [
            {
                "topology_tx": item["topology_tx"],
                "signed_hash": key_pair.sign_hash_hex(item["hash"]),
            }
            for item in generated["topology_txs"]
        ]
        submitted = self.api.validator(
            "POST",
            "/v0/admin/external-party/topology/submit",
            json=build_signed_topology_request(key_pair.public_key_hex, signed_transactions),
        )
        party_id = submitted.get("party_id") or generated["party_id"]
        (self.output_dir / "external_partyid.txt").write_text(f"{party_id}\n")
        print(f"externalPartyId={party_id}")
        print(f"topologyTransactions={len(signed_transactions)}")
        return party_id

    def setup_preapproval_proposal(
        self,
        receiver_party: str,
        provider_party: str,
        dso_party: str,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        command_id = f"cantor8-preapproval-{uuid.uuid4()}"
        payload = build_preapproval_proposal_request(
            receiver_party=receiver_party,
            provider_party=provider_party,
            dso_party=dso_party,
            command_id=command_id,
            user_id=user_id,
        )
        body = self.api.ledger(
            "POST", "/v2/commands/submit-and-wait-for-transaction", json=payload
        )
        update_id = body.get("transaction", {}).get("updateId")
        if update_id:
            print(f"preapprovalProposalUpdateId={update_id}")
        else:
            print("preapprovalProposalSubmitted=true")
        return body

    def check_balance(self, party_id: str) -> dict[str, Any]:
        ledger_end = self.api.ledger("GET", "/v2/state/ledger-end")
        offset = int(ledger_end["offset"])
        body = self.api.ledger(
            "POST",
            "/v2/state/active-contracts",
            params={"limit": 1000},
            json=build_active_contracts_request(party_id, offset),
        )
        summary = summarize_acs(body)
        print(f"ledgerEnd={offset}")
        print(f"holdingContracts={summary['holding_contracts']}")
        print(f"transferPreapprovalContracts={summary['transfer_preapproval_contracts']}")
        print(f"transferPreapprovalProposalContracts={summary['transfer_preapproval_proposal_contracts']}")
        print(f"estimatedBalance={summary['estimated_balance']}")
        return summary


def summarize_acs(responses: list[dict[str, Any]]) -> dict[str, Any]:
    holdings = 0
    preapprovals = 0
    proposals = 0
    balance = 0.0
    for response in responses:
        created = _created_event(response)
        if not created:
            continue
        template_id = created.get("templateId", "")
        if "TransferPreapprovalProposal" in template_id or template_id.endswith(
            TRANSFER_PREAPPROVAL_PROPOSAL_TEMPLATE_ID.removeprefix("#")
        ):
            proposals += 1
        if "TransferPreapproval" in template_id or template_id.endswith(
            TRANSFER_PREAPPROVAL_TEMPLATE_ID.removeprefix("#")
        ):
            preapprovals += 1
        for view in created.get("interfaceViews", []):
            view_value = view.get("viewValue") or {}
            amount = _find_amount(view_value)
            if amount is not None:
                holdings += 1
                balance += amount
                break
    return {
        "holding_contracts": holdings,
        "transfer_preapproval_contracts": preapprovals,
        "transfer_preapproval_proposal_contracts": proposals,
        "estimated_balance": f"{balance:.10f}".rstrip("0").rstrip(".") or "0",
    }


def _created_event(response: dict[str, Any]) -> dict[str, Any] | None:
    entry = response.get("contractEntry") or response.get("contract_entry") or {}
    if "JsActiveContract" in entry:
        return entry["JsActiveContract"].get("createdEvent")
    if "ActiveContract" in entry:
        return entry["ActiveContract"].get("createdEvent")
    if "CreatedEvent" in entry:
        return entry["CreatedEvent"]
    if "createdEvent" in entry:
        return entry["createdEvent"]
    return None


def _find_amount(value: Any) -> float | None:
    if isinstance(value, dict):
        for key in ("amount", "amountAsDecimal", "quantity"):
            if key in value:
                return _to_float(value[key])
        for nested in value.values():
            found = _find_amount(nested)
            if found is not None:
                return found
    if isinstance(value, list):
        for nested in value:
            found = _find_amount(nested)
            if found is not None:
                return found
    return None


def _to_float(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    if isinstance(value, dict):
        for nested in value.values():
            found = _to_float(nested)
            if found is not None:
                return found
    return None

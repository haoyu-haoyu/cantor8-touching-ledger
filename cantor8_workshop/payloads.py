from __future__ import annotations

from typing import Any

HOLDING_INTERFACE_ID = "#splice-api-token-holding-v1:Splice.Api.Token.HoldingV1:Holding"
TRANSFER_PREAPPROVAL_TEMPLATE_ID = "#splice-amulet:Splice.AmuletRules:TransferPreapproval"
TRANSFER_PREAPPROVAL_PROPOSAL_TEMPLATE_ID = (
    "#splice-wallet:Splice.Wallet.TransferPreapproval:TransferPreapprovalProposal"
)


def build_allocate_party_request(party_hint: str, user_id: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "partyIdHint": party_hint,
        "localMetadata": {
            "annotations": {
                "workshop": "cantor8-touching-ledger",
            }
        },
    }
    if user_id:
        payload["userId"] = user_id
    return payload


def build_preapproval_proposal_request(
    receiver_party: str,
    provider_party: str,
    dso_party: str,
    command_id: str,
    user_id: str | None = None,
) -> dict[str, Any]:
    commands: dict[str, Any] = {
        "commands": [
            {
                "CreateCommand": {
                    "templateId": TRANSFER_PREAPPROVAL_PROPOSAL_TEMPLATE_ID,
                    "createArguments": {
                        "receiver": receiver_party,
                        "provider": provider_party,
                        "expectedDso": dso_party,
                    },
                }
            }
        ],
        "commandId": command_id,
        "actAs": [receiver_party],
        "readAs": [receiver_party, provider_party],
    }
    if user_id:
        commands["userId"] = user_id
    return {"commands": commands}


def build_active_contracts_request(party: str, active_at_offset: int) -> dict[str, Any]:
    cumulative = [
        {
            "identifierFilter": {
                "InterfaceFilter": {
                    "value": {
                        "interfaceId": HOLDING_INTERFACE_ID,
                        "includeInterfaceView": True,
                        "includeCreatedEventBlob": True,
                    }
                }
            }
        },
        _template_filter(TRANSFER_PREAPPROVAL_TEMPLATE_ID),
        _template_filter(TRANSFER_PREAPPROVAL_PROPOSAL_TEMPLATE_ID),
    ]
    return {
        "activeAtOffset": active_at_offset,
        "eventFormat": {
            "filtersByParty": {party: {"cumulative": cumulative}},
            "verbose": True,
        },
    }


def _template_filter(template_id: str) -> dict[str, Any]:
    return {
        "identifierFilter": {
            "TemplateFilter": {
                "value": {
                    "templateId": template_id,
                    "includeCreatedEventBlob": True,
                }
            }
        }
    }


def build_signed_topology_request(
    public_key: str, signed_transactions: list[dict[str, str]]
) -> dict[str, Any]:
    return {"public_key": public_key, "signed_topology_txs": signed_transactions}

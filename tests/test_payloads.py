from cantor8_workshop.payloads import (
    HOLDING_INTERFACE_ID,
    TRANSFER_PREAPPROVAL_PROPOSAL_TEMPLATE_ID,
    build_active_contracts_request,
    build_allocate_party_request,
    build_preapproval_proposal_request,
    build_signed_topology_request,
)


def test_allocate_party_payload_grants_authenticated_user_rights():
    payload = build_allocate_party_request("learner", "validator-backend@clients")

    assert payload["partyIdHint"] == "learner"
    assert payload["userId"] == "validator-backend@clients"
    assert payload["localMetadata"]["annotations"]["workshop"] == "cantor8-touching-ledger"


def test_preapproval_proposal_command_uses_documented_template_and_fields():
    payload = build_preapproval_proposal_request(
        receiver_party="receiver::fingerprint",
        provider_party="provider::fingerprint",
        dso_party="DSO::fingerprint",
        command_id="cmd-1",
    )

    commands = payload["commands"]
    assert commands["commandId"] == "cmd-1"
    assert commands["actAs"] == ["receiver::fingerprint"]
    create = commands["commands"][0]["CreateCommand"]
    assert create["templateId"] == TRANSFER_PREAPPROVAL_PROPOSAL_TEMPLATE_ID
    assert create["createArguments"] == {
        "receiver": "receiver::fingerprint",
        "provider": "provider::fingerprint",
        "expectedDso": "DSO::fingerprint",
    }


def test_acs_request_filters_holding_interface_and_preapproval_templates():
    payload = build_active_contracts_request("party::id", 42)
    cumulative = payload["eventFormat"]["filtersByParty"]["party::id"]["cumulative"]

    assert payload["activeAtOffset"] == 42
    assert "verbose" not in payload
    interface_filter = cumulative[0]["identifierFilter"]["InterfaceFilter"]["value"]
    assert interface_filter["interfaceId"] == HOLDING_INTERFACE_ID
    assert interface_filter["includeInterfaceView"] is True
    template_ids = {
        item["identifierFilter"]["TemplateFilter"]["value"]["templateId"]
        for item in cumulative[1:]
    }
    assert TRANSFER_PREAPPROVAL_PROPOSAL_TEMPLATE_ID in template_ids


def test_signed_topology_payload_preserves_original_transactions():
    payload = build_signed_topology_request(
        public_key="ab12",
        signed_transactions=[
            {"topology_tx": "base64-one", "signed_hash": "sig-one"},
            {"topology_tx": "base64-two", "signed_hash": "sig-two"},
        ],
    )

    assert payload == {
        "public_key": "ab12",
        "signed_topology_txs": [
            {"topology_tx": "base64-one", "signed_hash": "sig-one"},
            {"topology_tx": "base64-two", "signed_hash": "sig-two"},
        ],
    }

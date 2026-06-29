import httpx

from cantor8_workshop.client import ApiClient
from cantor8_workshop.config import Settings
from cantor8_workshop.workshop import Workshop, summarize_acs


class StaticToken:
    def get_token(self) -> str:
        return "token"


def test_create_internal_party_saves_party_id(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/ledger/v2/parties"
        return httpx.Response(
            200,
            json={
                "partyDetails": {
                    "party": "learner::1220",
                    "isLocal": True,
                    "localMetadata": {},
                }
            },
        )

    api = ApiClient(
        Settings(client_id="client", client_secret="secret"),
        StaticToken(),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    workshop = Workshop(api, output_dir=tmp_path)

    assert workshop.create_internal_party("learner", "user-id") == "learner::1220"
    assert (tmp_path / "partyid.txt").read_text() == "learner::1220\n"


def test_summarize_acs_handles_js_active_contract_envelope():
    summary = summarize_acs(
        [
            {
                "contractEntry": {
                    "JsActiveContract": {
                        "createdEvent": {
                            "templateId": "pkg:Splice.AmuletRules:TransferPreapproval",
                            "interfaceViews": [],
                        }
                    }
                }
            }
        ]
    )

    assert summary["transfer_preapproval_contracts"] == 1

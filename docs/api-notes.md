# API Notes

Source document: the Google Doc opened successfully in browser tooling and was also exported through Google Docs plain text export for exact text extraction.

Credential discovery:

- `CANTON_CLIENT_ID=hackathon`
- `CANTON_CLIENT_SECRET=<32-character value from the workshop document>`
- Token endpoint returned HTTP 200 with `access_token` and `expires_in=900`.

Official references used:

- Canton JSON API overview: https://docs.canton.network/sdks-tools/api-reference/json-api
- Party allocation endpoint: https://docs.canton.network/reference/json-api-reference/post-v2parties
- Command submission endpoint: https://docs.canton.network/reference/json-api-reference/post-v2commandssubmit-and-wait-for-transaction
- ACS endpoint: https://docs.canton.network/reference/json-api-reference/post-v2stateactive-contracts
- Validator APIs: https://docs.canton.network/sdks-tools/api-reference/splice-validator-api
- Token Standard: https://docs.canton.network/appdev/deep-dives/token-standard
- TransferPreapproval Daml reference: https://docs.canton.network/sdks-tools/api-reference/splice-daml/splice-wallet/splice-wallet-transferpreapproval

Workshop-specific implementation choices:

- The code uses `/v0/admin/external-party/topology/generate` and `/v0/admin/external-party/topology/submit`.
- The code does not call `/v0/admin/external-party/setup-proposal`.
- The preapproval setup is submitted through the Ledger JSON API using the documented `CreateCommand` envelope for `#splice-wallet:Splice.Wallet.TransferPreapproval:TransferPreapprovalProposal`.
- The validator automation completed that proposal into an active `Splice.AmuletRules:TransferPreapproval` contract for the receiver party.


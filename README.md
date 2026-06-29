# Cantor8 Touching the Ledger

Python implementation of the Cantor8 Canton Network DevNet workshop flow:

1. OAuth2 client credentials token.
2. External-party topology setup through `/v0/admin/external-party/topology/{generate,submit}`.
3. Internal party allocation through the Ledger JSON API.
4. Transfer preapproval setup through a low-level Ledger API command.
5. ACS balance and preapproval checks.

The code never hardcodes credentials. Set them as environment variables.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

```bash
export CANTON_CLIENT_ID=hackathon
export CANTON_CLIENT_SECRET='<value from workshop document>'
```

## Run

```bash
python3 main.py run --party-hint cantor8-your-name
```

Useful follow-up commands:

```bash
python3 main.py balance '<party-id>'
python3 main.py topology --party-hint cantor8-external-demo
```

`external_party_key.json` is generated locally for signing topology hashes and is intentionally gitignored.

## Proof of Completion

Live run on Canton DevNet:

- Authenticated user: `validator-backend@clients`
- External party topology submitted with 3 topology transactions.
- External party: `cantor8-haoyu-20260629001700-external::12207cb9cc30c133207cb1caf23b909b253a4330ada7d9d6f675b762163e8372ae4b`
- Internal party: `cantor8-haoyu-20260629001700::12204e94c0e449c0efcd270dd1e68259c36471cebef132e5c7dfc2750fe8c9eed77f`
- Provider party: `cantor8-digik-1::12204e94c0e449c0efcd270dd1e68259c36471cebef132e5c7dfc2750fe8c9eed77f`
- DSO party: `DSO::1220be58c29e65de40bf273be1dc2b266d43a9a002ea5b18955aeef7aac881bb471a`
- Preapproval setup update ID: `12208ea7425f465e18bd91f78d2d82e83946d49c6ae039abbb29f36995d6a4b23bdb`
- ACS check at ledger end `2185680`: `holdingContracts=0`, `transferPreapprovalContracts=1`, `estimatedBalance=0`

Logs:

- Full proof run: `logs/run-20260629T001701Z.log`

After the Cantor8 team sends CC to the internal party, rerun:

```bash
python3 main.py balance 'cantor8-haoyu-20260629001700::12204e94c0e449c0efcd270dd1e68259c36471cebef132e5c7dfc2750fe8c9eed77f'
```

## Tests

```bash
python3 -m pytest -q
```

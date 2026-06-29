from __future__ import annotations

import argparse
import contextlib
import os
import sys
from pathlib import Path

import httpx

from cantor8_workshop.auth import TokenManager
from cantor8_workshop.client import ApiClient
from cantor8_workshop.config import Settings
from cantor8_workshop.errors import WorkshopError
from cantor8_workshop.logging_utils import Tee, open_log, print_step
from cantor8_workshop.workshop import Workshop


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the Cantor8 Touching the Ledger workshop against DevNet."
    )
    subparsers = parser.add_subparsers(dest="command")

    run = subparsers.add_parser("run", help="Run steps 1-4 end to end.")
    run.add_argument("--party-hint", default="cantor8-learner", help="Party ID hint.")
    run.add_argument(
        "--skip-external-topology",
        action="store_true",
        help="Skip /v0/admin/external-party/topology/{generate,submit}.",
    )
    run.add_argument(
        "--output-dir",
        default=".",
        help="Directory for partyid.txt, external_partyid.txt, key material, and logs.",
    )
    run.add_argument(
        "--receiver-party",
        help="Use an existing receiver party instead of allocating a new internal party.",
    )

    subparsers.add_parser("token", help="Fetch a token and print its expiry.")

    balance = subparsers.add_parser("balance", help="Check ACS balance for a party.")
    balance.add_argument("party_id")

    topology = subparsers.add_parser("topology", help="Generate and submit external party topology.")
    topology.add_argument("--party-hint", default="cantor8-external")
    topology.add_argument("--output-dir", default=".")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        args = parser.parse_args(["run"])

    try:
        settings = Settings.from_env()
        token_manager = TokenManager(settings)
        api = ApiClient(settings, token_manager)

        if args.command == "token":
            token = token_manager.get_token()
            print(f"tokenReceived=true")
            print(f"tokenPreview={token[:12]}...")
            return 0

        output_dir = Path(getattr(args, "output_dir", "."))
        log_file, log_path = open_log(output_dir / "logs")
        with log_file, contextlib.redirect_stdout(Tee(sys.stdout, log_file)):
            workshop = Workshop(api, output_dir=output_dir)
            if args.command == "run":
                run_workshop(args, workshop)
            elif args.command == "balance":
                print_step("Check Balance")
                workshop.check_balance(args.party_id)
            elif args.command == "topology":
                print_step("External Party Topology")
                workshop.setup_external_party_topology(args.party_hint)
            else:
                parser.error(f"unknown command {args.command}")
        print(f"logFile={log_path}")
        return 0
    except WorkshopError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except httpx.HTTPError as exc:
        print(f"HTTP ERROR: {exc}", file=sys.stderr)
        return 1


def run_workshop(args: argparse.Namespace, workshop: Workshop) -> None:
    print_step("Token")
    user_id = workshop.authenticated_user_id()
    print(f"authenticatedUser={user_id}")

    external_party = None
    if not args.skip_external_topology:
        print_step("External Party Topology")
        external_party = workshop.setup_external_party_topology(f"{args.party_hint}-external")

    print_step("Create Internal Party")
    if args.receiver_party:
        receiver_party = args.receiver_party
        print(f"partyId={receiver_party}")
        (Path(args.output_dir) / "partyid.txt").write_text(f"{receiver_party}\n")
    else:
        receiver_party = workshop.create_internal_party(args.party_hint, user_id=user_id)

    print_step("Provider Context")
    provider_party = os.environ.get("CANTON_PROVIDER_PARTY", "").strip()
    dso_party = os.environ.get("CANTON_DSO_PARTY", "").strip()
    if provider_party and dso_party:
        print(f"providerParty={provider_party}")
        print(f"dsoParty={dso_party}")
    else:
        provider_party, dso_party = workshop.discover_provider_context()

    print_step("Setup TransferPreapproval Proposal")
    workshop.setup_preapproval_proposal(
        receiver_party=receiver_party,
        provider_party=provider_party,
        dso_party=dso_party,
        user_id=user_id,
    )

    print_step("Check Balance")
    workshop.check_balance(receiver_party)
    if external_party:
        print(f"externalTopologyPartyForProof={external_party}")


if __name__ == "__main__":
    raise SystemExit(main())


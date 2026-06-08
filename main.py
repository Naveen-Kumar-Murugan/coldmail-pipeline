#!/usr/bin/env python3
"""
main.py — ColdMail Automated Outreach Pipeline
One domain in → lookalike companies → decision-makers → emails → sent.

Usage:
    python main.py stripe.com
    python main.py stripe.com --count 20
    python main.py stripe.com --resume
    python main.py --list-runs
    python main.py stripe.com --dry-run
    python main.py stripe.com --skip-confirm
"""
import argparse
import os
import sys
import time

from dotenv import load_dotenv
load_dotenv()

from utils.logger import console, ok, warn, err, info, _RICH
from utils import checkpoint

import pipeline.stage1_ocean     as stage1
import pipeline.stage2_prospeo   as stage2
import pipeline.stage3_enricher as stage3
import pipeline.stage4_brevo     as stage4

_REQUIRED_KEYS = {
    "OCEAN_API_KEY":   "Stage 1 — Ocean.io lookalike companies",
    "PROSPEO_API_KEY": "Stage 2/3 — Prospeo contacts & emails",
    "BREVO_API_KEY":   "Stage 4 — Brevo email sending",
    "SENDER_EMAIL":    "Stage 4 — your verified Brevo sender address",
    "EAZYREACH_CLIENT_ID":     "Stage 3 — EazyReach Client ID required for email enrichment",
    "EAZYREACH_CLIENT_SECRET": "Stage 3 — EazyReach Client Secret required for email enrichment",
}


def validate_env() -> dict:
    config: dict = {}
    missing = []
    for key, desc in _REQUIRED_KEYS.items():
        val = os.getenv(key, "").strip()
        if not val: missing.append(f"  ✗  {key}  (needed for {desc})")
        else: config[key] = val
    for key in ("SENDER_NAME","OCEAN_LOOKALIKE_COUNT",
                "PROSPEO_MAX_PER_COMPANY","SKIP_SEND_CONFIRM"):
        val = os.getenv(key,"")
        if val: config[key] = val
    if missing:
        print("\nMissing required environment variables:")
        for m in missing: print(m)
        print("\nCopy .env.example → .env and fill in your API keys.\n")
        sys.exit(1)
    return config

def main_ui(port: int = 5055) -> None:
    """Start the Flask dashboard and open it in the browser."""
    validate_env()
    from dashboard.server import start_server
    start_server(port=port, open_browser=True)

def print_banner(seed_domain: str, run_id: str) -> None:
    sep = "═" * 60
    if _RICH:
        from rich.panel import Panel
        console.print(Panel(
            f"\n  🚀  [bold cyan]Coldmail Outreach Pipeline[/bold cyan]\n"
            f"  Seed domain : [bold]{seed_domain}[/bold]\n"
            f"  Run ID      : [bold]{run_id}[/bold]\n"
            f"  Started     : [bold]{time.strftime('%Y-%m-%d %H:%M:%S')}[/bold]\n",
            border_style="cyan", padding=(0,2)
        ))
    else:
        print(f"\n{sep}")
        print(f"  🚀  Coldmail Outreach Pipeline")
        print(f"  Seed domain : {seed_domain}")
        print(f"  Run ID      : {run_id}")
        print(f"  Started     : {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{sep}\n")


def print_summary(seed_domain, companies, contacts, elapsed):
    resolved = sum(1 for c in contacts if c.get("email"))
    sent     = sum(1 for c in contacts if c.get("send_status") == "SENT")
    failed   = sum(1 for c in contacts if (c.get("send_status") or "").startswith("FAILED"))
    sep = "─" * 60
    print(f"\n{sep}")
    print("  Pipeline Complete")
    print(f"{sep}")
    print(f"  Seed domain         : {seed_domain}")
    print(f"  Lookalike companies : {len(companies)}")
    print(f"  Contacts found      : {len(contacts)}")
    print(f"  Emails resolved     : {resolved}")
    print(f"  Emails sent         : {sent}")
    print(f"  Send failures       : {failed}")
    print(f"  Total time          : {elapsed:.1f}s")
    print(f"{sep}\n")


def run_stage(stage_name, fn, input_data, config, run_id, resume):
    if resume and checkpoint.exists(run_id, stage_name):
        data = checkpoint.load(run_id, stage_name)
        print(f"  ↩  Resuming {stage_name} from checkpoint ({len(data)} records)")
        return data
    result = fn(input_data, config)
    checkpoint.save(run_id, stage_name, result)
    return result


def parse_args():
    p = argparse.ArgumentParser(
        prog="coldmail-pipeline",
        description="Automated cold-outreach pipeline: domain → emails sent.",
    )
    p.add_argument("domain", nargs="?", help="Seed domain, e.g. stripe.com")
    p.add_argument("--count", "-c", type=int, default=None,
                   help="Number of lookalike companies (default: 3)")
    p.add_argument("--max-per-company", "-m", type=int, default=None, dest="max_per_company",
                   help="Max decision-makers per company (default: 3)")
    p.add_argument("--resume", "-r", action="store_true",
                   help="Resume last run for this domain")
    p.add_argument("--list-runs", action="store_true",
                   help="List all saved runs and exit")
    p.add_argument("--dry-run", action="store_true",
                   help="Run Stages 1-3 only, skip email send")
    p.add_argument("--ui", action="store_true",
                   help="Open the web dashboard instead of CLI mode")
    p.add_argument("--port", type=int, default=5055,
                   help="Port for the web dashboard (default: 5055)")
    p.add_argument("--skip-confirm", action="store_true",
                   help="Skip send-confirmation prompt (auto-fires!)")
    return p.parse_args()


def list_runs_and_exit():
    runs = checkpoint.list_runs()
    if not runs:
        print("No saved runs found."); sys.exit(0)
    print(f"\n  {'Run ID':<35}  {'Seed Domain':<25}  Companies  Contacts  Sent")
    print(f"  {'─'*35}  {'─'*25}  {'─'*9}  {'─'*8}  ─────")
    for rid in runs:
        meta  = checkpoint.load(rid, "meta") or {}
        comps = checkpoint.load(rid, "stage1_companies") or []
        conts = checkpoint.load(rid, "stage3_emails") or []
        sent  = checkpoint.load(rid, "stage4_sent") or []
        sc    = sum(1 for c in sent if c.get("send_status") == "SENT")
        print(f"  {rid:<35}  {meta.get('seed_domain','—'):<25}  {len(comps):<9}  {len(conts):<8}  {sc}")
    print()
    sys.exit(0)


def main():
    args = parse_args()
 
    if args.ui:
        main_ui(port=args.port)
        return
 
    if args.list_runs:
        list_runs_and_exit()

    if not args.domain:
        err("Please provide a seed domain.  Example:  python main.py stripe.com")
        sys.exit(1)

    seed_domain = args.domain.strip().lower()
    if seed_domain.startswith("https://"):
        seed_domain = seed_domain[len("https://"):]
    if seed_domain.startswith("http://"):
        seed_domain = seed_domain[len("http://"):]
    if seed_domain.startswith("www."):
        seed_domain = seed_domain[4:]
    seed_domain = seed_domain.rstrip("/")

    config = validate_env()
    if args.count is not None:       config["OCEAN_LOOKALIKE_COUNT"]    = str(args.count)
    if args.max_per_company is not None: config["PROSPEO_MAX_PER_COMPANY"] = str(args.max_per_company)
    if args.skip_confirm:            config["SKIP_SEND_CONFIRM"]        = "true"

    if args.resume:
        existing = [r for r in checkpoint.list_runs()
                    if seed_domain.replace(".", "_") in r]
        if existing:
            run_id = existing[0]
            print(f"\n  Resuming run: {run_id}\n")
        else:
            warn("No previous run found. Starting fresh.")
            run_id = checkpoint.new_run_id(seed_domain)
    else:
        run_id = checkpoint.new_run_id(seed_domain)
        checkpoint.save_meta(run_id, seed_domain)

    print_banner(seed_domain, run_id)
    t_start = time.monotonic()

    try:
        companies = run_stage(
            "stage1_companies",
            lambda _, cfg: stage1.run(seed_domain, cfg),
            None, config, run_id, args.resume,
        )
        if not companies:
            err("No lookalike companies found. Exiting."); sys.exit(1)

        contacts = run_stage(
            "stage2_contacts",
            stage2.run,
            companies, config, run_id, args.resume,
        )
        if not contacts:
            warn("No contacts found. Exiting."); sys.exit(0)

        contacts = run_stage(
            "stage3_emails",
            stage3.run,
            contacts, config, run_id, args.resume,
        )

        if args.dry_run:
            warn("--dry-run: Stage 4 skipped. No emails sent.")
            checkpoint.save(run_id, "stage4_sent", contacts)
        else:
            contacts = run_stage(
                "stage4_sent",
                stage4.run,
                contacts, config, run_id, args.resume,
            )

    except KeyboardInterrupt:
        warn("\nInterrupted. Progress saved.")
        warn(f"Resume with:  python main.py {seed_domain} --resume")
        sys.exit(130)
    except Exception as exc:
        err(f"Fatal error: {exc}")
        if _RICH: console.print_exception(show_locals=False)
        else: import traceback; traceback.print_exc()
        warn(f"Resume with:  python main.py {seed_domain} --resume")
        sys.exit(1)

    elapsed = time.monotonic() - t_start
    print_summary(seed_domain, companies, contacts, elapsed)


if __name__ == "__main__":
    main()
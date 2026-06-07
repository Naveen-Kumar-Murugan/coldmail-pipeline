"""
pipeline/stage2_prospeo.py
Stage 2 · Prospeo — Decision-Maker Discovery

API: POST https://api.prospeo.io/search-person
Auth header: X-KEY: <key>
Filters: seniority [C-Suite, VP, Founder/Owner, Director], by company website
"""
import os
import sys
from typing import Any
import requests
from utils.logger import stage_header, ok, warn, err, info, console, _RICH
from utils.rate_limiter import raise_for_rate_limit, sleep_between, retry_request

_SEARCH_URL = "https://api.prospeo.io/search-person"
_TARGET_SENIORITIES = ["C-Suite", "Founder/Owner", "Director","Partner","Vice President","Head"]
_DEFAULT_MAX_PER_CO = 3


@retry_request
def _search_people(api_key: str, domain: str, page: int = 1) -> dict:
    resp = requests.post(
        _SEARCH_URL,
        headers={"X-KEY": api_key, "Content-Type": "application/json"},
        json={
            "page": page,
            "filters": {
                "company": {"websites": {"include": [domain]}},
                "person_seniority": {"include": _TARGET_SENIORITIES},
            },
        },
        timeout=30,
    )
    raise_for_rate_limit(resp)
    resp.raise_for_status()
    return resp.json()


def _extract_contacts(results: dict, company: dict, max_n: int) -> list[dict]:
    contacts = []
    for item in (results.get("results") or [])[:max_n]:
        if not isinstance(item, dict):
            continue
        person  = item.get("person") or {}
        co_data = item.get("company") or {}
        pid     = person.get("person_id", "")
        li      = person.get("linkedin_url", "")
        if not pid and not li: continue
        contacts.append({
            "person_id":        pid,
            "full_name":        person.get("full_name", ""),
            "first_name":       person.get("first_name", ""),
            "last_name":        person.get("last_name", ""),
            "job_title":        person.get("current_job_title", ""),
            "linkedin_url":     li,
            "company_name":     co_data.get("name") or company.get("name", ""),
            "company_domain":   co_data.get("domain") or company.get("domain", ""),
            "company_linkedin": co_data.get("linkedin_url", ""),
            "email":            None,
            "email_status":     None,
        })
    return contacts


def run(companies: list[dict], config: dict) -> list[dict[str, Any]]:
    stage_header(2, "Prospeo", "Finding decision-makers")

    api_key = config.get("PROSPEO_API_KEY") or os.getenv("PROSPEO_API_KEY", "")
    if not api_key:
        err("PROSPEO_API_KEY is missing.")
        return []
    if not companies:
        warn("Stage 2: No companies to search."); return []

    try:
        max_per_co = int(
            config.get("PROSPEO_MAX_PER_COMPANY", _DEFAULT_MAX_PER_CO)
        )
    except ValueError:
        warn("Invalid PROSPEO_MAX_PER_COMPANY. Using default value.")
        max_per_co = _DEFAULT_MAX_PER_CO

    all_contacts: list[dict] = []
    seen_pids: set[str] = set()
    seen_li:  set[str]  = set()
    total = len(companies)

    for idx, company in enumerate(companies, 1):
        domain  = company.get("domain", "")
        co_name = company.get("name", domain)
        print(f"  [{idx}/{total}] Searching {co_name} ({domain}) …", end=" ", flush=True)

        try:
            result = _search_people(api_key, domain)
        except requests.HTTPError as exc:
            response = exc.response
            status = response.status_code if response is not None else None
            body   = {}
            try: body = exc.response.json()
            except Exception: pass
            ec = body.get("error_code", "")
            if ec == "NO_RESULTS":   print("no results.")
            elif ec == "INSUFFICIENT_CREDITS":
                err("\nProspeo: Insufficient credits. Stopping."); break
            elif status in (401, 403):
                err("\nProspeo: Auth failed — check PROSPEO_API_KEY."); break
            else: 
                print(f"HTTP {status} — skipping.")
                print(f"Response: {body.get('error_code', '')}")
                return []
            sleep_between(1.1); continue
        except Exception as exc:
            print(f"error: {exc}"); sleep_between(1.1); continue

        if result.get("error"):
            ec = result.get("error_code", "")
            if ec == "NO_RESULTS": print("no contacts found.")
            elif ec == "INSUFFICIENT_CREDITS":
                err("\nProspeo: Insufficient credits. Stopping."); break
            else: print(f"error: {ec}")
            sleep_between(1.1); continue

        contacts = _extract_contacts(result, company, max_per_co)
        fresh = []
        for c in contacts:
            pid = c.get("person_id"); li = (c.get("linkedin_url") or "").rstrip("/")
            if pid and pid in seen_pids: continue
            if li  and li  in seen_li:  continue
            if pid: seen_pids.add(pid)
            if li:  seen_li.add(li)
            fresh.append(c)

        all_contacts.extend(fresh)
        print(f"{len(fresh)} contact(s) added.")
        sleep_between(1.1)

    if all_contacts:
        ok(f"Stage 2 complete — {len(all_contacts)} unique contacts found.")
        _print_table(all_contacts)
    else:
        warn("Stage 2: No contacts found.")
    return all_contacts


def _print_table(contacts: list[dict]) -> None:
    if _RICH:
        from rich.table import Table
        tbl = Table(title="Decision-Makers Found", show_lines=False, border_style="dim")
        tbl.add_column("#", style="dim", width=3)
        tbl.add_column("Name", style="bold")
        tbl.add_column("Title", style="cyan")
        tbl.add_column("Company")
        tbl.add_column("Domain", style="dim")
        tbl.add_column("LinkedIn", style="blue", overflow="fold")
        for i, c in enumerate(contacts, 1):
            tbl.add_row(str(i), c.get("full_name") or "—", c.get("job_title") or "—",
                        c.get("company_name") or "—", c.get("company_domain") or "—", c.get("linkedin_url") or "—")
        console.print(tbl)
    else:
        print(f"\n  {'#':>3}  {'Name':<25}  {'Title':<30}  {'Company':<25}  Domain  LinkedIn")
        for i, c in enumerate(contacts, 1):
            print(f"  {i:>3}  {c.get('full_name',''):<25}  {c.get('job_title',''):<30}  "
                  f"{c.get('company_name',''):<25}  {c.get('company_domain','')}  {c.get('linkedin_url','')}")
"""
pipeline/stage1_ocean.py
Stage 1 · Ocean.io — Lookalike Company Search

API: POST https://api.ocean.io/v3/search/companies
Auth: query param ?apiToken=<key>  OR  header x-api-token: <key>
"""
import os
from typing import Any
import requests
from utils.logger import stage_header, ok, warn, err, info, console, _RICH
from utils.rate_limiter import raise_for_rate_limit, sleep_between, retry_request

_OCEAN_URL = "https://api.ocean.io/v3/search/companies"

_JUNK_SUFFIXES = {".gov", ".edu", ".mil"}
_JUNK_DOMAINS  = {
    "linkedin.com","facebook.com","twitter.com","x.com","instagram.com",
    "youtube.com","wikipedia.org","glassdoor.com","indeed.com","crunchbase.com",
}

def _is_junk_domain(domain: str) -> bool:
    if not domain: return True
    d = domain.lower().strip()
    if any(d.endswith(s) for s in _JUNK_SUFFIXES): return True
    if d in _JUNK_DOMAINS: return True
    if "." not in d or " " in d: return True
    return False


@retry_request
def _call_ocean(api_key: str, seed_domain: str, count: int) -> dict:
    resp = requests.post(
        _OCEAN_URL,
        params={"apiToken": api_key},
        headers={"x-api-token": api_key, "Content-Type": "application/json"},
        json={
            "size": count,
            "companiesFilters": {
                "lookalikeDomains": [seed_domain],
                "socialMedias": {"medias": {"any_of":["linkedin"]}},
            },
        },
        timeout=30,
    )
    raise_for_rate_limit(resp)
    resp.raise_for_status()
    return resp.json()


def run(seed_domain: str, config: dict) -> list[dict[str, Any]]:
    stage_header(1, "Ocean.io", f"Finding lookalikes for {seed_domain}")

    api_key = config.get("OCEAN_API_KEY") or os.getenv("OCEAN_API_KEY", "")
    if not api_key:
        err("OCEAN_API_KEY is not set."); raise ValueError("Missing OCEAN_API_KEY")

    count = int(config.get("OCEAN_LOOKALIKE_COUNT", 15))
    info(f"Requesting {count} lookalike companies …")

    try:
        data = _call_ocean(api_key, seed_domain, count)
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response else "?"
        if status == 402:   err("Ocean.io: Insufficient credits (HTTP 402)L.")
        elif status in (401, 403): err("Ocean.io: Auth failed — check OCEAN_API_KEY.")
        elif status == 422: err(f"Ocean.io: Validation error — is '{seed_domain}' a valid domain?")
        else:               err(f"Ocean.io: HTTP {status}")
        raise

    raw_companies = data.get("companies", [])
    info(f"Ocean.io returned {len(raw_companies)} records (total hits: {data.get('total', '?'):,}).")

    failed = data.get("failedLookalikeDomains", [])
    if failed: warn(f"Ocean.io couldn't match seed domain(s): {failed}")

    companies: list[dict] = []
    seen: set[str] = set()

    for item in raw_companies:
        company = item.get("company") or item
        domain  = (company.get("domain") or "").strip().lower()
        if domain in seen: continue
        seen.add(domain)
        if _is_junk_domain(domain) or domain == seed_domain.lower().strip(): continue
        companies.append({
            "name":           company.get("name", ""),
            "domain":         domain,
            "size":           company.get("companySize", ""),
            "primaryCountry": company.get("primaryCountry", ""),
            "industries":     company.get("industries") or [],
            "linkedinHandle": company.get("medias").get("linkedin", {}).get("handle", "") if company.get("medias") else "",
            "relevance":      item.get("relevance", ""),
        })

    if companies:
        ok(f"Stage 1 complete — {len(companies)} valid lookalike companies found.")
        _print_table(companies)
    else:
        warn("Stage 1: No valid lookalike companies found.")
    return companies


def _print_table(companies: list[dict]) -> None:
    if _RICH:
        from rich.table import Table
        tbl = Table(title="Lookalike Companies", show_lines=False, border_style="dim")
        tbl.add_column("#", style="dim", width=3)
        tbl.add_column("Name", style="bold")
        tbl.add_column("Domain", style="cyan")
        tbl.add_column("Size", style="dim")
        tbl.add_column("Country", style="dim")
        for i, c in enumerate(companies, 1):
            tbl.add_row(str(i), c["name"] or "—", c["domain"],
                        c["size"] or "—", (c["primaryCountry"] or "—").upper())
        console.print(tbl)
    else:
        print(f"\n  {'#':>3}  {'Name':<30}  {'Domain':<25}  {'Size'}")
        for i, c in enumerate(companies, 1):
            print(f"  {i:>3}  {c['name']:<30}  {c['domain']:<25}  {c['size']}")
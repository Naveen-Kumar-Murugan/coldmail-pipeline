"""
pipeline/stage1_ocean.py
Stage 1 · Ocean.io — Lookalike Company Search

API: POST https://api.ocean.io/v3/search/companies
Auth: query param ?apiToken=<key>  OR  header x-api-token: <key>
"""
import os
from typing import Any
import requests
import re
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

def _is_valid_domain(domain: str) -> bool:
    pattern = r"^(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$"
    return bool(re.match(pattern, domain.strip()))

def run(seed_domain: str, config: dict) -> list[dict[str, Any]]:
    stage_header(1, "Ocean.io", f"Finding lookalikes for {seed_domain}")

    seed_domain = seed_domain.lower().strip()
    if not _is_valid_domain(seed_domain):
        err(
            f"Invalid domain '{seed_domain}'. "
            "Expected a domain such as 'shopify.com'."
        )
        raise SystemExit(1)

    api_key = config.get("OCEAN_API_KEY") or os.getenv("OCEAN_API_KEY", "")
    if not api_key:
        err("OCEAN_API_KEY is missing."); 
        raise SystemExit(1)

    count = int(config.get("OCEAN_LOOKALIKE_COUNT", 3))
    info(f"Requesting {count} lookalike companies …")

    try:
        data = _call_ocean(api_key, seed_domain, count)
    except requests.HTTPError as exc:
        response = exc.response
        status = response.status_code if response is not None else None
        if status in (401, 403):
            err("Ocean.io authentication failed.")
            warn("Check OCEAN_API_KEY and verify it has sufficient permissions or if the OCEAN_API_KEY is valid.")
            return []
        elif status == 402:
            err("Ocean.io account has insufficient credits.")
            return []
        elif status == 422:
            err(f"'{seed_domain}' is not a valid domain.")
            return []
        err(f"Ocean.io returned HTTP {status}.")
        return []
    except Exception:
        err("Unexpected Ocean.io failure.")
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
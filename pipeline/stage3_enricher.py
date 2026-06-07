"""
pipeline/stage3_eazyreach.py
Stage 3 · Email Resolution

Flow:
1. Try EazyReach
   - Exchange Client ID + Secret for auth token
   - Lookup LinkedIn URL
   - Use first VERIFIED email
2. Fallback to Prospeo enrich-person
3. Never stop pipeline because EazyReach failed

Config:
    EAZYREACH_CLIENT_ID
    EAZYREACH_CLIENT_SECRET
    PROSPEO_API_KEY
"""

import os
from typing import Any
import requests
import json
from utils.logger import (stage_header, ok, warn, err, info, console, _RICH)
from utils.rate_limiter import (raise_for_rate_limit, sleep_between, retry_request)

_PROSPEO_ENRICH_URL = "https://api.prospeo.io/enrich-person"
_EAZYREACH_AUTH_URL = "https://api.superflow.run/b2b/createAuthToken/"
_EAZYREACH_LOOKUP_URL = "https://api.superflow.run/b2b/linkedin-emails"

@retry_request
def _prospeo_enrich(api_key: str, contact: dict) -> dict:
    payload: dict[str, Any] = {}
    if contact.get("person_id"):
        payload["person_id"] = contact["person_id"]
    elif contact.get("linkedin_url"):
        payload["linkedin_url"] = contact["linkedin_url"]
    else:
        if contact.get("first_name") and contact.get("last_name"):
            payload["first_name"] = contact["first_name"]
            payload["last_name"] = contact["last_name"]
        elif contact.get("full_name"):
            payload["full_name"] = contact["full_name"]
        if contact.get("company_domain"):
            payload["company_website"] = contact["company_domain"]
        if contact.get("company_name"):
            payload["company_name"] = contact["company_name"]
        if contact.get("company_linkedin"):
            payload["company_linkedin_url"] = contact["company_linkedin"]

    resp = requests.post(
        _PROSPEO_ENRICH_URL,
        headers={
            "X-KEY": api_key,
            "Content-Type": "application/json",
        },
        json={
            "only_verified_email": True,
            "data": payload,
        },
        timeout=30,
    )

    raise_for_rate_limit(resp)
    resp.raise_for_status()

    return resp.json()


def _extract_email(result: dict) -> dict:
    person = result.get("person") or {}
    email_obj = person.get("email") or {}

    email = email_obj.get("email")
    status = email_obj.get("status", "UNKNOWN")
    revealed = email_obj.get("revealed", False)

    return {
        "email": email,
        "status": status,
        "revealed": revealed,
    }

@retry_request
def _get_eazyreach_token(client_id: str,client_secret: str) -> str | None:
    info("EazyReach: requesting auth token...")
    if not client_id or not client_secret:
        warn("EazyReach Client ID or Client Secret missing.")
        return None
    resp = requests.post(
        _EAZYREACH_AUTH_URL,
        headers={"Content-Type": "application/json",},
        json={
            "clientId": client_id,
            "clientSecret": client_secret,
        },
        timeout=30,
    )

    raise_for_rate_limit(resp)

    if not resp.ok:
        warn(f"EazyReach auth failed (HTTP {resp.status_code}), check your Client ID and Secret.")
        return None

    try:
        payload = resp.json()
    except Exception:
        warn("EazyReach auth returned invalid JSON.")
        return None

    token = payload.get("authToken")
    if token:
        ok("EazyReach auth token acquired.")
    else:
        warn("EazyReach auth token missing.")

    return token


@retry_request
def _eazyreach_lookup(token: str,linkedin_url: str) -> tuple[int, dict]:
    headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}",}
    data = json.dumps({
        "linkedinUrl": linkedin_url
    })
    resp = requests.post(
        _EAZYREACH_LOOKUP_URL,
        headers = headers,
        data = data
    )
    raise_for_rate_limit(resp)
    try:
        payload = resp.json()
    except Exception:
        payload = {}
    return resp.status_code, payload


def _extract_eazyreach_email(payload: dict) -> tuple[str | None, str]:
    emails = payload.get("emails", [])
    for item in emails:
        email = item.get("email")
        verification = item.get("verification")
        if email and verification == "verified":
            return email, "VERIFIED"
    return None, "NOT_FOUND"

def run(contacts: list[dict],config: dict) -> list[dict[str, Any]]:
    stage_header(3,"Email Resolution","Enriching contacts with verified emails",)
    prospeo_key = (config.get("PROSPEO_API_KEY") or os.getenv("PROSPEO_API_KEY", ""))
    eazyreach_client_id = (config.get("EAZYREACH_CLIENT_ID") or os.getenv("EAZYREACH_CLIENT_ID", ""))
    eazyreach_client_secret = (config.get("EAZYREACH_CLIENT_SECRET") or os.getenv("EAZYREACH_CLIENT_SECRET", ""))

    use_eazyreach = bool(eazyreach_client_id and eazyreach_client_secret)

    if use_eazyreach:
        info("Primary provider: EazyReach (fallback: Prospeo)")
    elif prospeo_key:
        info("EazyReach disabled or Client ID and Client Secret missing, using Prospeo only.")
    else:
        err("No enrichment provider configured.")
        return contacts

    if not contacts:
        warn("Stage 3: No contacts to enrich.")
        return contacts

    eazyreach_token = None
    if use_eazyreach:
        try:
            eazyreach_token = _get_eazyreach_token(eazyreach_client_id,eazyreach_client_secret,)
        except Exception as exc:
            warn(f"EazyReach auth error: {exc}")

    resolved = 0
    skipped = 0
    failed = 0
    total = len(contacts)
    ifeazyReachBalance= True
    for idx, contact in enumerate(contacts, start=1):
        name = (contact.get("full_name") or contact.get("first_name") or "Unknown")
        domain = (contact.get("company_domain") or "Unknown")
        # info(f"[{idx}/{total}] Processing {name} @ {domain}")
        email_found = False
        
        linkedin_url = contact.get("linkedin_url")
        if (eazyreach_token and linkedin_url and ifeazyReachBalance):
            try:
                info("Trying EazyReach LinkedIn resolver...")
                status_code, payload = (_eazyreach_lookup(eazyreach_token,linkedin_url))
                info(f"EazyReach response: HTTP {status_code} Payload: {payload}")
                if status_code == 200:
                    email, status = (_extract_eazyreach_email(payload))
                    if email:
                        contact["email"] = email
                        contact["email_status"] = status
                        resolved += 1
                        email_found = True
                        ok(f"EazyReach resolved: {email}")
                    else: warn("EazyReach returned no verified email.")
                elif status_code == 401: 
                    warn("EazyReach balance exhausted. Falling back to Prospeo.")
                    ifeazyReachBalance = False
                elif status_code == 404: warn("LinkedIn profile not found in EazyReach.")
                elif status_code == 402: warn("EazyReach authenticationfailed.")
                else: warn(f"EazyReach HTTP {status_code}")

            except Exception as exc:
                warn(f"EazyReach exception: {exc}")

        if not email_found:
            if not prospeo_key:
                err("PROSPEO_API_KEY is missing.")
                return []
            
            info("Falling back to Prospeo enrich-person...")
            try:
                result = _prospeo_enrich(prospeo_key, contact)
            except requests.HTTPError as exc:
                response = exc.response
                status = response.status_code if response is not None else None
                body = {}
                try:
                    body = response.json() if response is not None else {}
                except Exception:
                    pass

                error_code = body.get("error_code", "")
                if error_code == "NO_MATCH":
                    contact["email_status"] = "NOT_FOUND"
                    skipped += 1
                    warn("Prospeo: no email found.")
                elif error_code == "INSUFFICIENT_CREDITS":
                    err("Prospeo: Insufficient credits. Stopping.")
                    break
                elif status in (401, 403):
                    err("Prospeo: Auth failed — check PROSPEO_API_KEY.")
                    break
                else:
                    contact["email_status"] = f"HTTP_{status}"
                    failed += 1
                    warn(f"Prospeo HTTP {status} Response: {error_code}")
                    return []
                sleep_between(0.25)
                continue

            except Exception as exc:
                contact["email_status"] = "EXCEPTION"
                failed += 1
                warn(f"Prospeo exception: {exc}")
                sleep_between(0.25)
                continue


            if result.get("error"):
                error_code = result.get("error_code", "")
                if error_code == "NO_MATCH":
                    contact["email_status"] = "NOT_FOUND"
                    skipped += 1
                    warn("Prospeo: no email found.")
                elif error_code == "INSUFFICIENT_CREDITS":
                    err("Prospeo: Insufficient credits. Stopping.")
                    break
                else:
                    contact["email_status"] = f"ERROR:{error_code}"
                    failed += 1
                    warn(f"Prospeo error: {error_code}")
                sleep_between(0.25)
                continue

            email_data = _extract_email(result)

            if email_data["revealed"] and email_data["email"]:
                contact["email"] = email_data["email"]
                contact["email_status"] = email_data["status"]
                resolved += 1
                ok(f"Prospeo resolved: {email_data['email']}")
            else:
                contact["email_status"] = "NOT_FOUND"
                skipped += 1
                warn("Prospeo returned no email.")

    ok(f"Stage 3 complete — {resolved} resolved, {skipped} skipped, {failed} errors.")
    if resolved == 0:
        warn("No emails resolved. Stage 4 will have nothing to send.")

    _print_table(contacts)
    return contacts

def _print_table(contacts: list[dict],) -> None:

    if _RICH:
        from rich.table import Table
        table = Table(title="Email Enrichment Results", show_lines=False, border_style="dim")
        table.add_column("#", style="dim", width=3)
        table.add_column("Name", style="bold")
        table.add_column("Title", style="cyan")
        table.add_column("Email", style="green")
        table.add_column("Status", style="dim")

        for idx, contact in enumerate(contacts,start=1):
            table.add_row(str(idx), contact.get("full_name") or "—", contact.get("job_title") or "—", contact.get("email") or "—",contact.get("email_status") or "—",)
        console.print(table)

    else:
        print(f"\n{'#':>3} {'Name':<25} {'Email':<35} Status")

        for idx, contact in enumerate(contacts,start=1):
            print(f"{idx:>3} {contact.get('full_name',''):<25} {contact.get('email','—'):<35} {contact.get('email_status','—')}")
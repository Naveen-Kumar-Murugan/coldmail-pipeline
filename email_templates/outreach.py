"""
email_templates/outreach.py
────────────────────────────
Personalized cold-outreach email copy.

Two variants by seniority:
  • C-Suite / Founder  → strategic ROI / market angle
  • VP / Director      → operational efficiency angle

Edit the copy freely — the pipeline only cares that build_email() returns
a dict with keys:  subject, html_body, text_body
"""

from __future__ import annotations


def _first_name(contact: dict) -> str:
    return (contact.get("first_name") or contact.get("full_name", "").split()[0] or "there").strip()


def _is_c_suite(contact: dict) -> bool:
    title = (contact.get("job_title") or "").lower()
    keywords = {"ceo", "cto", "coo", "cfo", "cpo", "founder", "co-founder", "president", "owner"}
    return any(k in title for k in keywords)


# ── C-Suite / Founder copy ────────────────────────────────────────────────────

_CSUITE_SUBJECT = "Quick question about {company}'s outreach pipeline"

_CSUITE_HTML = """
<html>
<body style="font-family: Arial, sans-serif; font-size: 15px; color: #222; line-height: 1.6;">
  <p>Hi {first_name},</p>

  <p>
    I came across {company} while researching companies in your space — impressive
    traction, especially on the sales side.
  </p>

  <p>
    At <strong>NavDev</strong>, we help growth-stage teams automate their
    outbound pipeline end-to-end — from prospect discovery to personalised
    outreach — without adding headcount.
  </p>

  <p>
    For {company} specifically, I think there's a clear opportunity to
    <strong>3x outbound volume</strong> while cutting the manual work your team
    currently does between tools.
  </p>

  <p>
    Worth a 15-minute call this week to see if it's a fit?
  </p>

  <p>Best,<br/>{sender_name}</p>

  <hr style="border:none;border-top:1px solid #eee;margin:20px 0;"/>
  <p style="font-size:12px;color:#999;">
    You're receiving this because {company} came up in our research as a potential fit.
    If this isn't relevant, just reply and I'll remove you from our list.
  </p>
</body>
</html>
""".strip()

_CSUITE_TEXT = """Hi {first_name},

I came across {company} while researching companies in your space — impressive traction, especially on the sales side.

At NavDev, we help growth-stage teams automate their outbound pipeline end-to-end — from prospect discovery to personalised outreach — without adding headcount.

For {company} specifically, I think there's a clear opportunity to 3x outbound volume while cutting the manual work your team currently does between tools.

Worth a 15-minute call this week to see if it's a fit?

Best,
{sender_name}

---
You're receiving this because {company} came up in our research as a potential fit.
Reply to be removed from this list.
""".strip()


# ── VP / Director copy ────────────────────────────────────────────────────────

_VP_SUBJECT = "Automating {company}'s outreach — quick idea"

_VP_HTML = """
<html>
<body style="font-family: Arial, sans-serif; font-size: 15px; color: #222; line-height: 1.6;">
  <p>Hi {first_name},</p>

  <p>
    I noticed {company} is scaling in a market we work with closely.
    As {title}, you're likely balancing pipeline targets with a team that
    doesn't have infinite hours.
  </p>

  <p>
    <strong>NavDev</strong> builds fully automated outbound pipelines:
    one domain in → lookalike discovery → verified contacts → personalised
    emails sent — zero manual steps.
  </p>

  <p>
    Teams we work with typically see <strong>40–60% more qualified meetings</strong>
    in the first 30 days without adding BDRs.
  </p>

  <p>
    Happy to share a quick walkthrough if you're curious.
    Does Thursday or Friday work for a 15-min call?
  </p>

  <p>Best,<br/>{sender_name}</p>

  <hr style="border:none;border-top:1px solid #eee;margin:20px 0;"/>
  <p style="font-size:12px;color:#999;">
    You're receiving this because {company} matched our ideal-fit criteria.
    Reply "unsubscribe" to opt out.
  </p>
</body>
</html>
""".strip()

_VP_TEXT = """Hi {first_name},

I noticed {company} is scaling in a market we work with closely. As {title}, you're likely balancing pipeline targets with a team that doesn't have infinite hours.

VocalLabs builds fully automated outbound pipelines: one domain in → lookalike discovery → verified contacts → personalised emails sent — zero manual steps.

Teams we work with typically see 40-60% more qualified meetings in the first 30 days without adding BDRs.

Happy to share a quick walkthrough if you're curious. Does Thursday or Friday work for a 15-min call?

Best,
{sender_name}

---
Reply "unsubscribe" to opt out.
""".strip()


# ── Public API ────────────────────────────────────────────────────────────────

def build_email(contact: dict, sender_name: str) -> dict[str, str]:
    """
    Build a personalised email for one contact.

    Parameters
    ----------
    contact     : enriched contact dict (must have email, full_name, company_name, job_title)
    sender_name : from-name used in the email body

    Returns
    -------
    dict with keys: subject, html_body, text_body
    """
    fn      = _first_name(contact)
    company = contact.get("company_name") or contact.get("company_domain", "your company")
    title   = contact.get("job_title", "")

    if _is_c_suite(contact):
        subject   = _CSUITE_SUBJECT.format(company=company)
        html_body = _CSUITE_HTML.format(
            first_name=fn, company=company,
            title=title, sender_name=sender_name,
        )
        text_body = _CSUITE_TEXT.format(
            first_name=fn, company=company,
            title=title, sender_name=sender_name,
        )
    else:
        subject   = _VP_SUBJECT.format(company=company)
        html_body = _VP_HTML.format(
            first_name=fn, company=company,
            title=title, sender_name=sender_name,
        )
        text_body = _VP_TEXT.format(
            first_name=fn, company=company,
            title=title, sender_name=sender_name,
        )

    return {
        "subject":   subject,
        "html_body": html_body,
        "text_body": text_body,
    }
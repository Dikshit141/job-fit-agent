#!/usr/bin/env python3
"""
Job Fit Agent v2 (free: Google Gemini free tier + Remotive + Adzuna free APIs)

What it does
  1. SEARCH   Gemini decides what to search and calls two job sources:
              Remotive (remote jobs worldwide) and Adzuna (local/on-site/hybrid, e.g. India).
  2. FILTER   Drops jobs above/below your experience level (--level) and jobs you've seen before.
  3. TRIAGE   Scores every remaining job 0-100 against your resume; drops those under --min-score.
  4. ANALYZE  Deep analysis of the top jobs: why it fits, gaps, resume edits, interview prep.
  5. FILES    For the best match(es): a tailored resume (.docx) and a cover letter (.docx).
  6. TRACK    Appends reported jobs to applications.csv so reruns show only NEW jobs.

Setup
  pip install -r requirements_v2.txt
  PowerShell:
    $env:GEMINI_API_KEY="..."          # free: https://aistudio.google.com/apikey
    $env:ADZUNA_APP_ID="..."           # free: https://developer.adzuna.com  (optional but recommended)
    $env:ADZUNA_APP_KEY="..."
  Run:
    python job_fit_agent_v2.py resume.pdf --target "backend engineer, python developer" --level junior --top 3
"""
import argparse
import csv
import html
import json
import os
import re
import sys
import time
from datetime import date
from pathlib import Path

import requests
from docx import Document
from google import genai
from google.genai import errors, types
from pydantic import BaseModel

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

COUNTRY_NAMES = {
    "in": "India", "us": "United States", "gb": "United Kingdom", "ca": "Canada",
    "au": "Australia", "de": "Germany", "sg": "Singapore", "nl": "Netherlands",
    "fr": "France", "nz": "New Zealand", "za": "South Africa",
}

LEVEL_HINTS = {
    "junior": "entry-level: graduate, junior, associate, trainee, 0-2 years of experience",
    "mid": "mid-level: roughly 2-5 years of experience",
    "senior": "senior: 5+ years of experience, may lead projects",
    "any": "any level",
}

# Title words that make a job a mismatch for each level (applied before any AI call)
TITLE_EXCLUDE = {
    "junior": ["senior", "sr", "lead", "principal", "staff", "head of", "director",
               "manager", "architect", "vp"],
    "mid": ["principal", "staff", "head of", "director", "vp", "intern", "internship"],
    "senior": ["intern", "internship", "junior", "graduate", "trainee"],
    "any": [],
}

CFG = {"country": "in"}  # filled from CLI
POOL: list = []          # every job found by the search tools, deduped by url
TRACKER_FIELDS = ["date", "title", "company", "location", "score", "url", "status"]


# ---------------------------------------------------------------- helpers
def log(*a):
    print(*a, file=sys.stderr)


def strip_html(raw: str) -> str:
    raw = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", raw or "")
    raw = re.sub(r"(?s)<[^>]+>", " ", raw)
    return re.sub(r"\s+", " ", html.unescape(raw)).strip()


def strip_fences(text: str) -> str:
    text = (text or "").strip()
    text = re.sub(r"^```[a-zA-Z]*\n", "", text)
    return re.sub(r"\n```$", "", text).strip()


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (text or "job").lower()).strip("_")[:40] or "job"


def load_resume(path: str) -> str:
    p = Path(path)
    if not p.exists():
        sys.exit(f"Resume not found: {path}")
    if p.suffix.lower() == ".pdf":
        from pypdf import PdfReader
        return "\n".join((pg.extract_text() or "") for pg in PdfReader(str(p)).pages)
    if p.suffix.lower() == ".docx":
        return "\n".join(par.text for par in Document(str(p)).paragraphs)
    return p.read_text(encoding="utf-8", errors="ignore")


def add_to_pool(job: dict) -> bool:
    if not job.get("url") or any(j["url"] == job["url"] for j in POOL):
        return False
    job["id"] = len(POOL) + 1
    POOL.append(job)
    return True


def compact(job: dict) -> dict:
    """Short form shown to the model during search (saves tokens)."""
    return {k: job[k] for k in ("id", "title", "company", "location", "salary", "source")} | {
        "snippet": job["description"][:200]
    }


# ---------------------------------------------------------------- search tools
def search_remote_jobs(query: str) -> list:
    """Search remote jobs worldwide (Remotive). Use short keyword queries like 'python backend'.

    Args:
        query: Short keywords, e.g. 'python developer' or 'data engineer'.
    """
    log(f"  -> search_remote_jobs({query!r})")
    try:
        r = requests.get("https://remotive.com/api/remote-jobs",
                         params={"search": query, "limit": 10}, timeout=20)
        r.raise_for_status()
        out = []
        for j in r.json().get("jobs", [])[:10]:
            job = {
                "title": j.get("title"), "company": j.get("company_name"),
                "location": j.get("candidate_required_location") or "Remote",
                "salary": j.get("salary") or "not listed", "url": j.get("url"),
                "source": "remotive",
                "description": strip_html(j.get("description", ""))[:2500],
            }
            if add_to_pool(job):
                out.append(compact(job))
        return out or [{"note": "no new results for this query"}]
    except Exception as e:
        return [{"error": str(e)}]


def search_local_jobs(query: str, location: str = "") -> list:
    """Search local, on-site, hybrid and remote jobs in the candidate's country (Adzuna).

    Args:
        query: Short keywords, e.g. 'python developer'. Fewer words give more results.
        location: Optional city or state, e.g. 'Bangalore' or 'Punjab'. Leave empty for the whole country.
    """
    log(f"  -> search_local_jobs({query!r}, {location!r})")
    app_id, app_key = os.getenv("ADZUNA_APP_ID"), os.getenv("ADZUNA_APP_KEY")
    if not app_id or not app_key:
        return [{"error": "Adzuna is not configured. Use search_remote_jobs only."}]
    params = {"app_id": app_id, "app_key": app_key, "results_per_page": 10,
              "what": query, "content-type": "application/json"}
    if location:
        params["where"] = location
    try:
        r = requests.get(
            f"https://api.adzuna.com/v1/api/jobs/{CFG['country']}/search/1",
            params=params, timeout=20)
        r.raise_for_status()
        out = []
        for j in r.json().get("results", []):
            lo, hi = j.get("salary_min"), j.get("salary_max")
            job = {
                "title": j.get("title"),
                "company": (j.get("company") or {}).get("display_name", "Unknown"),
                "location": (j.get("location") or {}).get("display_name", ""),
                "salary": f"{int(lo)}-{int(hi)}" if lo and hi else "not listed",
                "url": j.get("redirect_url"), "source": "adzuna",
                "description": strip_html(j.get("description", ""))[:2500],
            }
            job["title"] = strip_html(job["title"] or "")
            if add_to_pool(job):
                out.append(compact(job))
        return out or [{"note": "no new results for this query"}]
    except Exception as e:
        return [{"error": str(e)}]


def try_fetch_full_text(url: str) -> str:
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0 job-fit-agent"})
        r.raise_for_status()
        return strip_html(r.text)[:5000]
    except Exception:
        return ""


# ---------------------------------------------------------------- schemas
class Score(BaseModel):
    job_id: int
    score: int
    reason: str


class Triage(BaseModel):
    scores: list[Score]


class Gap(BaseModel):
    item: str
    severity: str   # "must-have" or "nice-to-have"
    fixability: str


class Question(BaseModel):
    question: str
    hint: str


class Evaluation(BaseModel):
    job_id: int
    score: int
    why_fit: list[str]
    gaps: list[Gap]
    tailoring: list[str]
    interview: list[Question]


class Analysis(BaseModel):
    candidate_snapshot: str
    evaluations: list[Evaluation]
    overall_advice: str


# ---------------------------------------------------------------- Gemini calls
def gemini_call(fn, retries=4):
    for attempt in range(retries):
        try:
            return fn()
        except errors.APIError as e:
            if e.code in (429, 503) and attempt < retries - 1:
                wait = 30 * (attempt + 1)
                log(f"  Rate limited / busy. Waiting {wait}s...")
                time.sleep(wait)
                continue
            raise


def json_config(schema, system: str) -> types.GenerateContentConfig:
    return types.GenerateContentConfig(
        system_instruction=system, response_mime_type="application/json",
        response_schema=schema, max_output_tokens=16000)


def phase_search(client, model, resume, args):
    system = (
        "You are the search stage of a job fit agent. Use the tools to build a pool of relevant jobs. "
        "Run at least 5 searches with DIFFERENT short queries (role titles, skill combos, adjacent roles), "
        "using BOTH search_local_jobs and search_remote_jobs. Include level words when helpful "
        "(e.g. 'junior', 'graduate', 'associate'). When done, reply with just: done."
    )
    prompt = (
        f"Target roles: {args.target}\nExperience level wanted: {LEVEL_HINTS[args.level]}\n"
        f"Location preference: {args.location}\nCandidate based in: {COUNTRY_NAMES.get(args.country, args.country)}\n\n"
        f"=== RESUME ===\n{resume[:6000]}\n=== END ==="
    )
    config = types.GenerateContentConfig(
        system_instruction=system,
        tools=[search_local_jobs, search_remote_jobs],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(maximum_remote_calls=10),
    )
    chat = client.chats.create(model=model, config=config)
    gemini_call(lambda: chat.send_message(prompt))


def phase_triage(client, model, resume, jobs, args) -> dict:
    system = (
        "You score how well each job fits a candidate. Be honest and calibrated: 85+ apply now, "
        "70-84 strong with tailoring, 55-69 stretch, below 55 weak. Penalize heavily (score <= 35) any job that "
        "(a) requires far more years of experience than the candidate has, or (b) is not open to candidates "
        "based in the candidate's country. Score EVERY job id given."
    )
    listing = [{"id": j["id"], "title": j["title"], "company": j["company"], "location": j["location"],
                "description": j["description"][:900]} for j in jobs]
    prompt = (
        f"Target roles: {args.target}\nLevel wanted: {LEVEL_HINTS[args.level]}\n"
        f"Candidate based in: {COUNTRY_NAMES.get(args.country, args.country)}\n\n"
        f"=== RESUME ===\n{resume[:6000]}\n=== END ===\n\nJOBS:\n{json.dumps(listing)}"
    )
    resp = gemini_call(lambda: client.models.generate_content(
        model=model, contents=prompt, config=json_config(Triage, system)))
    triage = Triage.model_validate_json(resp.text)
    return {s.job_id: s for s in triage.scores}


def phase_analyze(client, model, resume, jobs, args) -> Analysis:
    system = (
        "You are a candid career coach. For each job write: 2-3 'why_fit' bullets citing specific resume "
        "evidence; 'gaps' (each labelled severity 'must-have' or 'nice-to-have' with a short fixability note); "
        "3-5 'tailoring' edits (which bullets to move up, which keywords to mirror, how to reframe EXISTING "
        "experience; NEVER suggest claiming skills or work the candidate lacks); 5 'interview' questions with a "
        "one-line hint grounded in the candidate's real background. Give an honest score 0-100. "
        "In overall_advice: patterns across jobs, the top skill to learn, application order, and any resume "
        "problems you notice (e.g. leftover mentions of another company, inconsistent dates, typos)."
    )
    listing = [{"id": j["id"], "title": j["title"], "company": j["company"], "location": j["location"],
                "salary": j["salary"], "description": j["description"]} for j in jobs]
    prompt = (
        f"Target roles: {args.target}\nLevel wanted: {LEVEL_HINTS[args.level]}\n\n"
        f"=== RESUME ===\n{resume[:8000]}\n=== END ===\n\nJOBS:\n{json.dumps(listing)}"
    )
    resp = gemini_call(lambda: client.models.generate_content(
        model=model, contents=prompt, config=json_config(Analysis, system)))
    return Analysis.model_validate_json(resp.text)


def phase_documents(client, model, resume, job, outdir: Path) -> list:
    base = f"{slug(job['company'])}_{slug(job['title'])}"
    files = []

    resume_prompt = (
        "Rewrite the candidate's resume tailored to the job below.\n"
        "RULES: Use ONLY facts present in the original resume. You may reorder sections and bullets, "
        "tighten wording, and mirror the job's keywords where the candidate truly has that skill. NEVER add "
        "skills, employers, dates, numbers, or degrees that are not in the original. Remove any mention of a "
        "different specific target employer. Keep it to about one page.\n"
        "OUTPUT: Markdown only. '# Full Name', one contact line if present in the original, then '## ' "
        "section headings with '- ' bullets. No commentary, no code fences.\n\n"
        f"=== ORIGINAL RESUME ===\n{resume[:8000]}\n\n=== JOB ===\n{job['title']} at {job['company']}\n"
        f"{job['description']}"
    )
    letter_prompt = (
        "Write a cover letter for this job from this candidate. 3 short paragraphs, under 250 words, "
        "specific and warm, no clichés. Use ONLY facts from the resume. Start with 'Dear Hiring Team,' and "
        "end with 'Sincerely,' and the candidate's name. Output plain text paragraphs, no code fences.\n\n"
        f"=== RESUME ===\n{resume[:8000]}\n\n=== JOB ===\n{job['title']} at {job['company']}\n"
        f"{job['description']}"
    )
    for label, prompt in (("tailored_resume", resume_prompt), ("cover_letter", letter_prompt)):
        resp = gemini_call(lambda p=prompt: client.models.generate_content(model=model, contents=p))
        path = outdir / f"{label}_{base}.docx"
        md_to_docx(strip_fences(resp.text), path)
        files.append(str(path))
    return files


# ---------------------------------------------------------------- output
def add_runs(par, text: str):
    for i, part in enumerate(re.split(r"\*\*(.+?)\*\*", text)):
        if part:
            par.add_run(part).bold = (i % 2 == 1)


def md_to_docx(md: str, path: Path):
    doc = Document()
    for line in md.splitlines():
        s = line.rstrip()
        if not s.strip():
            continue
        if s.startswith("# "):
            doc.add_heading(s[2:], 0)
        elif s.startswith("## "):
            doc.add_heading(s[3:], 1)
        elif s.startswith("### "):
            doc.add_heading(s[4:], 2)
        elif s.lstrip().startswith(("- ", "* ")):
            add_runs(doc.add_paragraph(style="List Bullet"), s.lstrip()[2:])
        else:
            add_runs(doc.add_paragraph(), s)
    doc.save(str(path))


def build_report(analysis: Analysis, ranked: list, files: dict, args) -> str:
    out = ["# Job Fit Report", f"*{date.today().isoformat()} | level: {args.level} | target: {args.target}*",
           "", "## Candidate snapshot", analysis.candidate_snapshot, ""]
    for n, (job, ev) in enumerate(ranked, 1):
        out += [f"---\n### {n}. {job['title']} @ {job['company']}  -  Fit: {ev.score}/100",
                f"- Link: {job['url']}", f"- Location: {job['location']}  |  Salary: {job['salary']}  "
                f"|  Source: {job['source']}", "", "**Why it fits**"]
        out += [f"- {x}" for x in ev.why_fit]
        out += ["", "**Gaps**"] + [f"- [{g.severity}] {g.item} ({g.fixability})" for g in ev.gaps]
        out += ["", "**Resume tailoring**"] + [f"- {x}" for x in ev.tailoring]
        out += ["", "**Interview prep**"]
        for i, q in enumerate(ev.interview, 1):
            out += [f"{i}. {q.question}", f"   - *Hint:* {q.hint}"]
        if job["id"] in files:
            out += ["", "**Files:** " + ", ".join(f"`{Path(f).name}`" for f in files[job["id"]])]
        out.append("")
    out += ["---", "## Overall advice", analysis.overall_advice]
    return "\n".join(out)


# ---------------------------------------------------------------- tracker
def load_seen(path: Path) -> set:
    if not path.exists():
        return set()
    with open(path, newline="", encoding="utf-8-sig") as f:
        return {row["url"] for row in csv.DictReader(f)}


def append_tracker(path: Path, rows: list):
    new = not path.exists()
    try:
        with open(path, "a", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=TRACKER_FIELDS)
            if new:
                w.writeheader()
            w.writerows(rows)
    except PermissionError:
        log(f"  Could not write {path} (is it open in Excel?). Close it and rerun to track these jobs.")


# ---------------------------------------------------------------- main
def level_ok(title: str, level: str) -> bool:
    words = TITLE_EXCLUDE.get(level, [])
    if not words:
        return True
    pat = r"\b(" + "|".join(re.escape(w) for w in words) + r")\b"
    return not re.search(pat, (title or "").lower())


def main():
    ap = argparse.ArgumentParser(description="Job fit agent v2 (free)")
    ap.add_argument("resume", help="Resume file (.pdf, .docx, .txt, .md)")
    ap.add_argument("--target", required=True, help="Role(s) you want, e.g. 'backend engineer, python developer'")
    ap.add_argument("--level", choices=list(LEVEL_HINTS), default="any")
    ap.add_argument("--location", default="any (remote or local)", help="Work/location preference, e.g. 'Chandigarh or remote'")
    ap.add_argument("--country", default="in", help="Adzuna country code (in, us, gb, ca, au, de, sg...)")
    ap.add_argument("--top", type=int, default=3, help="Jobs in the detailed report")
    ap.add_argument("--min-score", type=int, default=55, help="Drop jobs scoring below this")
    ap.add_argument("--docs", type=int, default=1, help="Make tailored resume + cover letter for the top N jobs (0 = none)")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--outdir", default="output")
    ap.add_argument("--tracker", default="applications.csv")
    ap.add_argument("--include-seen", action="store_true", help="Don't skip jobs already in the tracker")
    args = ap.parse_args()

    if not (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")):
        sys.exit("Set GEMINI_API_KEY first (free key: https://aistudio.google.com/apikey)")
    if not (os.getenv("ADZUNA_APP_ID") and os.getenv("ADZUNA_APP_KEY")):
        log("Note: ADZUNA_APP_ID / ADZUNA_APP_KEY not set, so only remote jobs will be searched.")

    CFG["country"] = args.country
    resume = load_resume(args.resume)
    client = genai.Client()
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    tracker = Path(args.tracker)

    log(f"[1/5] Searching job sources with {args.model}...")
    phase_search(client, args.model, resume, args)
    log(f"      Found {len(POOL)} unique jobs.")

    seen = set() if args.include_seen else load_seen(tracker)
    jobs = [j for j in POOL if level_ok(j["title"], args.level) and j["url"] not in seen]
    log(f"[2/5] After level/seen filters: {len(jobs)} jobs.")
    if not jobs:
        sys.exit("No new jobs to evaluate. Try different --target words, another --level, or --include-seen.")
    jobs = jobs[:30]

    log("[3/5] Scoring all jobs...")
    scores = phase_triage(client, args.model, resume, jobs, args)
    by_id = {j["id"]: j for j in jobs}
    ranked_ids = sorted((i for i in scores if i in by_id), key=lambda i: scores[i].score, reverse=True)
    keep = [i for i in ranked_ids if scores[i].score >= args.min_score][: args.top]
    if not keep:
        log(f"No jobs scored {args.min_score}+. Best candidates:")
        for i in ranked_ids[:3]:
            log(f"  {scores[i].score}: {by_id[i]['title']} @ {by_id[i]['company']} - {scores[i].reason}")
        sys.exit("Try --min-score lower, a different --level, or broader --target roles.")

    top_jobs = [by_id[i] for i in keep]
    for j in top_jobs:  # Adzuna gives short snippets; try to get the full posting
        if len(j["description"]) < 800:
            full = try_fetch_full_text(j["url"])
            if len(full) > len(j["description"]):
                j["description"] = full

    log(f"[4/5] Deep analysis of {len(top_jobs)} jobs...")
    analysis = phase_analyze(client, args.model, resume, top_jobs, args)
    ev_by_id = {e.job_id: e for e in analysis.evaluations}
    ranked = sorted(((by_id[i], ev_by_id[i]) for i in keep if i in ev_by_id),
                    key=lambda t: t[1].score, reverse=True)

    log("[5/5] Writing files...")
    files = {}
    for job, ev in ranked[: max(args.docs, 0)]:
        try:
            files[job["id"]] = phase_documents(client, args.model, resume, job, outdir)
        except Exception as e:
            log(f"  Could not create documents for {job['company']}: {e}")

    report = build_report(analysis, ranked, files, args)
    report_path = outdir / "job_fit_report.md"
    report_path.write_text(report, encoding="utf-8")
    append_tracker(tracker, [{
        "date": date.today().isoformat(), "title": j["title"], "company": j["company"],
        "location": j["location"], "score": e.score, "url": j["url"], "status": "new"}
        for j, e in ranked])

    print(report)
    log(f"\nSaved: {report_path}")
    for fl in files.values():
        for f in fl:
            log(f"Saved: {f}")
    log(f"Tracker: {tracker} (edit the status column: applied / interview / rejected)")


if __name__ == "__main__":
    main()
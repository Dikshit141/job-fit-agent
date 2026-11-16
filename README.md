# Job Fit Agent

An LLM agent that searches live job listings, scores each one against your resume, and produces a gap analysis, resume-tailoring advice, interview prep, a tailored resume and a cover letter. It runs on free tiers (Google Gemini API, Remotive, optionally Adzuna).

## How it works

```
resume + target roles
        |
 1. SEARCH   LLM agent plans its own queries and calls two tools
             (Gemini function calling, capped at 10 tool calls)
             - search_remote_jobs  (Remotive)
             - search_local_jobs   (Adzuna, optional)
        |
 2. FILTER   remove duplicate listings, jobs already in the tracker,
             and titles that don't match --level (e.g. "senior" for junior)
        |
 3. TRIAGE   LLM scores every remaining job 0-100 (schema-validated JSON)
        |
 4. ANALYZE  top jobs get: why it fits, gaps, resume edits, interview questions
        |
 5. FILES    tailored resume (.docx) + cover letter (.docx) for the best match
        |
 6. TRACK    results appended to applications.csv so reruns show only new jobs
```

Design choices:
- The LLM handles the open-ended parts (choosing queries, judging fit). Deduplication, level filtering and tracking are plain code.
- Every LLM stage that feeds later code returns JSON validated against a Pydantic schema.
- Tailoring prompts restrict output to facts present in your original resume (no invented skills or experience).
- Free-tier rate limits (HTTP 429/503) are handled with retry and increasing waits.

## Setup

Requires Python 3.9+.

```bash
git clone https://github.com/Dikshit141/job-fit-agent.git
cd job-fit-agent
python -m venv venv
# Windows: venv\Scripts\activate      Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
```

Set your keys as environment variables (never commit them):

```powershell
# Windows PowerShell
$env:GEMINI_API_KEY="your-key"        # free: https://aistudio.google.com/apikey
$env:ADZUNA_APP_ID="your-app-id"      # optional: https://developer.adzuna.com
$env:ADZUNA_APP_KEY="your-app-key"
```

```bash
# Mac/Linux
export GEMINI_API_KEY="your-key"
export ADZUNA_APP_ID="your-app-id"
export ADZUNA_APP_KEY="your-app-key"
```

Without Adzuna keys the agent searches remote jobs (Remotive) only. Check Adzuna's current terms before relying on it.

## Usage

```bash
python job_fit_agent.py resume.pdf --target "backend engineer, python developer" --level junior --top 3
```

| Option | Meaning | Default |
|---|---|---|
| `--target` | Role(s) you want (required) | |
| `--level` | `junior`, `mid`, `senior`, `any` | `any` |
| `--location` | Work/location preference | any |
| `--country` | Adzuna country code (`in`, `us`, `gb`...) | `in` |
| `--top` | Jobs in the detailed report | 3 |
| `--min-score` | Drop jobs scoring below this | 55 |
| `--docs` | Make tailored resume + cover letter for top N jobs (0 = none) | 1 |
| `--model` | Gemini model name | `gemini-3.8-flash` |
| `--include-seen` | Don't skip jobs already in the tracker | off |

Output goes to `output/` (`job_fit_report.md`, tailored resume and cover letter `.docx`) plus `applications.csv` in the working directory.

If you see a "model not found" error, Google changes free model names often. Pass a current one with `--model` or set `GEMINI_MODEL`.

## Privacy

Your resume text is sent to the Gemini API. On free tiers, Google may use submitted content to improve its products, so remove your phone number and address from the resume before running. Do not commit your resume, generated documents or tracker (the included `.gitignore` excludes them).

## Limitations

- Scoring quality has not been benchmarked yet; always read the report and the original posting yourself.
- Adzuna returns short descriptions, so scores for those jobs rest on less detail. Full-posting fetch is best-effort.
- Remotive covers remote jobs only.
- Generated resumes and cover letters must be reviewed before sending.
- Not a production service; it is a personal tool.

## Roadmap

- Evaluation harness: compare agent scores with hand-labelled scores, track schema-valid rate and unsupported resume claims
- Run logs for every tool call, error and retry
- Stage checkpoints so interrupted runs can resume
- More job sources

## License

MIT

# Job Fit Report
*2026-11-15 | level: junior | target: backend engineer, python developer*

## Candidate snapshot
M.E. Computer Science candidate (graduating 2026) with solid core Python, FastAPI, and data systems foundations, backed by 6 months of corporate experience at Tata Technologies and microservices/ML projects.

---
### 1. Software Engineer, New Grad @ Stripe  -  Fit: 85/100
- Link: https://www.adzuna.in/details/5939121660?utm_medium=api&utm_source=cee9a8dd
- Location: India  |  Salary: not listed  |  Source: adzuna

**Why it fits**
- Graduation timeline (M.E. 2026) perfectly aligns with Stripe's 'obtained by summer 2027' requirement, and candidate has under 18 months of full-time experience.
- Demonstrated ability to design scalable distributed architectures (9-service microservices platform with Docker, K8s, JWT authentication, and Redis Streams).
- Directly matches the requirement for 'leveraging AI tools to accelerate development while applying rigorous critical thinking' as stated on the resume.

**Gaps**
- [nice-to-have] Experience with large-scale production financial infrastructure or deep concurrency models in languages like Ruby, Go, or Java. (Bridgeable by emphasizing multithreaded Java work from Tata Technologies/Internselite and async Python design patterns.)
- [must-have] Extremely high bar for algorithmic problem-solving and distributed systems debugging under Stripe's live coding rounds. (Requires intensive practice on LeetCode (medium/hard) focusing on clean code, edge-case testing, and API design without IDE autocompletion.)

**Resume tailoring**
- Elevate NEXUS-GX and StreamPulse AI to the top of the resume, emphasizing API reliability, JWT refresh-token rotation, and monitoring via Prometheus/Grafana.
- Position the Tata Technologies experience prominently, highlighting root-cause debugging, 15% PLM downtime reduction, and zero data loss validation.
- Ensure the summary clearly communicates graduation year (2026) and readiness for a high-rigor backend engineering new-grad role.

**Interview prep**
1. How did you design authentication and prevent token hijacking in your NEXUS-GX microservices architecture?
   - *Hint:* Explain your JWT implementation with refresh-token rotation, RBAC, and how tokens are securely validated across microservices.
2. In your Tata Technologies migration pipeline, how did you programmatically guarantee zero data loss across 10,000+ records?
   - *Hint:* Discuss idempotency, pre- and post-migration validation checks, rollback strategies, and transactional consistency.
3. How do you handle backpressure and data spikes in real-time streaming architectures?
   - *Hint:* Refer to Redis Streams consumer groups and async processing implemented in your StreamPulse AI platform.
4. Walk me through how you safely update and monitor a production service deployed on Kubernetes.
   - *Hint:* Talk about rolling deployments, health/liveness probes, and alerting through Prometheus and Grafana.
5. Tell me about a time an AI coding tool produced subtly incorrect code and how you caught it.
   - *Hint:* Describe a specific unit test or algorithmic boundary case where Claude/Cursor hallucinated logic and your automated testing flagged it.

**Files:** `tailored_resume_stripe_software_engineer_new_grad.docx`, `cover_letter_stripe_software_engineer_new_grad.docx`

---
### 2. Junior Developer-Python @ Hunarstreet Technologies Pvt Ltd  -  Fit: 78/100
- Link: https://www.adzuna.in/details/5482747792?utm_medium=api&utm_source=cee9a8dd
- Location: India  |  Salary: 400000-800000  |  Source: adzuna

**Why it fits**
- Proven Python backend and API architecture experience using FastAPI to serve models and handle request-response workflows in StreamPulse AI and NEXUS-GX.
- Demonstrated relational database expertise with PostgreSQL in multiple projects, matching the requirement for query optimization and data pipeline handling.
- Existing foundation in ML workflows and explicitly listed experience in AI-assisted development tooling (Claude, Cursor).

**Gaps**
- [must-have] Hands-on LLM orchestration frameworks (e.g., LangChain, LlamaIndex, OpenAI/HuggingFace API integrations) and prompt engineering workflows. (Easily fixable in a weekend by building a small FastAPI microservice integrating an OpenAI or open-source HuggingFace model with structured JSON outputs.)
- [must-have] Availability conflict due to ongoing full-time M.E. program (2024-2026) if the employer mandates immediate full-time on-site work. (Requires clear alignment with recruiter regarding thesis semester flexibility, remote options, or internship-to-hire status.)

**Resume tailoring**
- Reframe the StreamPulse AI and NEXUS-GX bullet points to explicitly emphasize JSON serialization, request validation (Pydantic), and REST API design.
- Highlight experience with Cursor/Claude in the Technical Skills section by framing it as prompt-driven code generation, evaluation, and test validation.
- Move PostgreSQL and database integration bullets higher up within the project descriptions to match the database-driven workflow requirement.

**Interview prep**
1. How do you enforce structured JSON output and handle error parsing when consuming external AI/API services?
   - *Hint:* Discuss using Pydantic models in FastAPI to validate schemas and how you handle malformed payloads gracefully.
2. How have you structured PostgreSQL queries and data schemas in your StreamPulse AI platform for sub-second responses?
   - *Hint:* Reference indexing, connection pooling, and combining Redis Streams for ephemeral data with PostgreSQL for persistence.
3. Explain a scenario where you had to debug an API bottleneck in your FastAPI backends.
   - *Hint:* Walk through using Prometheus and Grafana metrics from StreamPulse AI to identify latency drivers.
4. What is your approach to prompt optimization when an LLM fails to return answers according to required constraints?
   - *Hint:* Explain system prompts, few-shot examples, temperature tuning, and output schema enforcement.
5. How would you handle asynchronous background processing for a slow third-party API call in Python?
   - *Hint:* Draw from your experience with Celery/Redis Streams and FastAPI's background tasks or async/await concurrency.

---
### 3. Junior Python Automation Developer Telangana @ Indium software  -  Fit: 72/100
- Link: https://www.adzuna.in/details/5805535691?utm_medium=api&utm_source=cee9a8dd
- Location: Hyderabad, Telangana  |  Salary: not listed  |  Source: adzuna

**Why it fits**
- Strong foundation in Python core concepts including multithreading, OOP, algorithm design, and data structures.
- Extensive API consumption and database experience, including handling JSON schemas, RESTful CRUD operations, and SQL data pipelines.
- Prior professional experience writing data validation pipelines, automated test logic, and debugging production bottlenecks at Tata Technologies.

**Gaps**
- [must-have] Job specifies 'Immediate to within July end' notice period; candidate is currently enrolled in a Master's program graduating in 2026. (Hard blocker unless candidate is legally and academically permitted to work full-time immediately (e.g., remote or dual-track).)
- [nice-to-have] Role targets Python automation and scripting rather than AI/backend development. (Easily reframe existing pipeline validation and testing code as robust automation suites.)

**Resume tailoring**
- Shift focus from ML modeling toward Python scripting, concurrency (asyncio/multithreading), and automated test harness development.
- Expand the Tata Technologies bullet points to highlight automated validation scripts, regression tests, and SQL data scraping.
- Move Git workflow, debugging, and code maintenance practices to the top of the Technical Skills section.

**Interview prep**
1. How do Python generators and list/dict comprehensions optimize memory usage in large-scale data automation scripts?
   - *Hint:* Explain lazy evaluation with iterators versus loading entire datasets into memory.
2. What is the difference between multiprocessing, multithreading, and asyncio in Python, and when would you use each?
   - *Hint:* Discuss CPU-bound tasks vs I/O-bound tasks and how the Global Interpreter Lock (GIL) affects threading.
3. How do you implement decorators in Python for logging, retrying failed API requests, and execution timing?
   - *Hint:* Walk through creating a wrapper function using functools.wraps with arguments and keyword arguments.
4. How do you ensure data integrity when writing SQL scripts that perform bulk updates from parsed JSON files?
   - *Hint:* Mention database transactions (BEGIN/COMMIT/ROLLBACK), batch processing, and constraints.
5. Describe your standard Git workflow when resolving merge conflicts and submitting clean PRs in a collaborative team.
   - *Hint:* Reference rebasing, feature branches, descriptive commit messages, and automated CI test runs.

---
## Overall advice
Critical Resume Error: Your summary explicitly ends with 'Looking to bring this to Sandvik's research and development team.' Remove this immediately before applying anywhere else; leaving another company's name on a resume is an instant disqualifier for recruiters. In addition, your multiple short 1-month internships (CodSoft, Bharat Intern, Internselite) look like certificate programs; consider consolidating them under an 'Additional Projects/Internships' banner to keep attention on your strong 6-month Tata Technologies experience and your top-tier projects (NEXUS-GX and StreamPulse AI). Skill-wise, while your ML/Python foundations are strong, the junior market demands either hands-on LLM engineering (LangChain/API integration) or rock-solid production testing/automation (PyTest, CI/CD). Application Order: Apply to Stripe New Grad first (Job 16) as your 2026 graduation window and systems background fit their exact criteria; then apply to Hunarstreet (Job 3) after building a quick LLM API sample project; apply to Indium Software (Job 1) last only if your university allows immediate full-time employment.
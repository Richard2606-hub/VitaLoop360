# VitaLoop 360

One shared operating console connects factory evidence, human decisions, and four department walkthroughs through a production lot.

This is a working local prototype of the supplied VitaLoop 360 proposal. Factory Sentinel calculates metrics from synthetic telemetry, presents source evidence, verifies a draft, and records operator decisions in a hash-chained ledger. The other four capability packs are explicitly labelled walkthroughs. Lumora Wellness and its records are fictional.

The default experience needs no API key and makes no model call. It is a synthetic demonstration, not a recording of AMD/Gemma inference. An optional OpenAI-compatible endpoint can provide factory explanation text; a real AMD deployment and its credentials must be supplied and independently verified before claiming AMD execution.

## Run locally

Use a recent Python 3 installation. The application uses the Python standard library and a plain HTML/CSS/JavaScript interface; no package installation is needed.

From this directory:

```powershell
python run.py --demo --port 8765
```

Open [http://127.0.0.1:8765](http://127.0.0.1:8765). Keep the terminal running and press `Ctrl+C` to stop the server. If that port is in use, choose another with `--port`.

From the parent `VitaLoop 360` workspace, enter the application directory first:

```powershell
Set-Location -LiteralPath '.\vitaloop360'
python run.py --demo --port 8765
```

## Try the product

1. Open Factory Sentinel and inspect the synthetic night-shift lot, its energy/scrap metrics, and calculation assumptions.
2. Run the factory analysis and inspect the locked facts and cited fictional procedure.
3. Run the fabricated-number challenge to see an unsupported figure rejected.
4. Review a proposed hold and provide a named operator and decision notes. Approving a local hold records a decision; it does not operate machinery.
5. Follow the lot thread across Compliance, Demand, Experience, and Care. Their downstream scenarios remain walkthroughs.
6. Inspect the audit view and verify the saved ledger chain.

## Optional model endpoint

Configure environment variables in the terminal before starting the application. Copy the base URL and exact model ID from your own deployment; no provider URL or model name is guessed by this project.

```powershell
$env:VITALOOP_BASE_URL = 'https://your-endpoint.example/v1'
$env:VITALOOP_MODEL = 'your-deployed-model-id'
$env:VITALOOP_API_KEY = 'your-private-key'
$env:VITALOOP_PROVIDER = 'Your configured provider'
python run.py --port 8765
```

Keep keys out of source control, browser code, screenshots, and shared logs. These variables apply to the current terminal process. Alternatively, copy `.env.example` to `.env` and fill in its literal `VITALOOP_` assignments; the runner loads that file automatically. Existing environment variables take precedence. Omit `--demo` when you want to use the configured endpoint.

| Variable | Purpose |
| --- | --- |
| `VITALOOP_BASE_URL` | OpenAI-compatible API base URL, ordinarily ending in `/v1`. |
| `VITALOOP_MODEL` | Exact deployed model identifier. |
| `VITALOOP_API_KEY` | Server-side credential for the configured endpoint. |
| `VITALOOP_PROVIDER` | Display name chosen by the operator; not hardware verification. |
| `VITALOOP_TIMEOUT_SECONDS` | Provider request timeout; default `20`. |
| `VITALOOP_INPUT_PRICE_PER_MILLION` | Operator-supplied USD price assumption for one million input tokens; blank means unavailable. |
| `VITALOOP_OUTPUT_PRICE_PER_MILLION` | Operator-supplied USD price assumption for one million output tokens; blank means unavailable. |
| `VITALOOP_DATA_DIR` | Directory for local runtime data; default `data` beside `run.py`. |

The gateway sends the factory request to the configured service when used. A provider label or configured endpoint alone is not evidence that a call succeeded or ran on AMD hardware. Provider-reported usage and measured request timing are shown when available; financial estimates depend on the prices you supply.

To return to the no-provider demonstration, stop the server and force demo mode. This ignores model credentials, including those in `.env`:

```powershell
python run.py --demo --port 8765
```

The ledger persists at `data/ledger.jsonl`. For an independent demonstration without deleting existing records, pass a new directory, for example `--data-dir data-session-2`. The default bind address is `127.0.0.1`; changing `--host` exposes a local prototype without production authentication.

## Optional container and static snapshot

A Dockerfile is included. With Docker installed, build and run a local demo:

```powershell
docker build -t vitaloop360 .
docker run --rm -p 127.0.0.1:8765:8765 -v vitaloop-data:/app/data vitaloop360 python run.py --demo --host 0.0.0.0 --port 8765
```

The named volume preserves local audit records. The container path is supplied for reproducibility; building the local Python application does not by itself validate that container on your machine.

To export a fresh credential-free synthetic state snapshot:

```powershell
python run.py --export-demo dist/demo-data.json
```

This export does not make a model call and does not replay a recorded AMD run.

## Check the implementation & run hard tests

Run the 28-test Python unit/integration/concurrency/HTTP suite, JavaScript module syntax checks, browser-domain state-machine checks, the 18-case adversarial readiness suite, and the evaluation metrics report:

```powershell
python -m unittest discover -s tests -v
npm run check
npm run test:browser-domain
python run.py --batch
python run.py --demo --metrics
```

Additional execution modes (`run.py`):
- `python run.py --demo --port 8765` — Serve interactive console in deterministic demo mode.
- `python run.py --replay data/ledger.jsonl --port 8765` (or `--mode replay`) — Serve console in read-only replay mode from a saved JSONL ledger.
- `python run.py --batch` (or `--mode batch`) — Execute all 18 happy-path and adversarial twin readiness cases across all 5 installed capability packs (`packs/*`).
- `python run.py --demo --metrics` — Print the complete Proposal Section 11 Evaluation & Metrics JSON report (telemetry, domain metrics, Holt-Winters vs. Seasonal Naive backtest, verification outcomes, guard & PII redaction statistics, readiness pass rate, and SHA-256 thread integrity).

Use the [manual acceptance checklist](docs/acceptance-checklist.md) to check the running console, approval transitions, evidence, and responsive layout. Model-endpoint checks require actual credentials and are separate from offline checks.

## Scope and limits

This build follows the proposal's principle of completing the factory flow and labelling the remaining packs. It deliberately uses a lightweight Python server and browser interface instead of the proposed Streamlit stack. Synthetic data keeps the local demonstration reproducible without downloads or external accounts.

No plant, ERP, Evolus workspace, pharmacy, customer messaging service, or clinical system is connected. Human approval records local demonstration state only. Typed operator names are attribution fields, not authenticated identities. The application is intended for local evaluation and has no production access-control system.

The ledger provides a verifiable hash chain, not independently anchored immutable storage. The fact/citation verifier is a bounded demonstration check, not proof that an explanation is semantically correct. Care content is fictional and unsuitable for clinical use. Public-data validation, production privacy controls, the proposal's complete pack loader, real recorded replay, and the remaining statistical/clinical integrations require further implementation and evaluation.

See [requirements traceability](docs/requirements-traceability.md), [factory calculation methodology](docs/factory-methodology.md), [data provenance and disclosure](docs/data-provenance.md), and the [future pack contract](docs/pack-specification.md). Hackathon eligibility, current provider availability, licensing, and external submission requirements were not verified by building this prototype.

## Hosted browser demonstration

The private hosted website uses the packaged synthetic snapshot and runs the walkthrough in the browser. Its demo decisions persist only in local browser storage and do not synchronize across devices. Resetting the demo creates a fresh history; export the JSONL ledger to keep a copy. The browser ledger is independently hashed and is not the Python runtime ledger. Caregiver free text is not persisted.

The local Python service uses durable JSONL storage and can call a configured model endpoint. The hosted static demonstration does not make model calls or connect to the Python runtime.

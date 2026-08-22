# Universal AI Browser Agent

A hackathon-ready orchestration layer that combines OpenAI intent routing, local user memory, and WebCMD adapter execution. The included adapters are deterministic mock workflows: they demonstrate the contract and safe control flow without logging into third-party sites or making real payments.

## Architecture

- `src/brain.py` uses Gemini 2.5 Flash JSON mode to classify prompts into `student_opportunities`, `recruitment`, `bills`, or `healthcare`.
- `src/memory.py` stores reusable profiles in `data/user_memory.json` using atomic writes.
- `src/webcmd_bridge.py` invokes `webcmd run <adapter> -f json` through `subprocess.Popen` and validates JSON output.
- `src/universal_agent.py` supplies memory context, enforces billing confirmation, and formats results.
- `adapters/` contains runnable Node.js adapter templates with mock DOM/extraction results.

## Requirements

- Python 3.10+
- Node.js 18+
- WebCMD CLI installed and healthy
- A Google Gemini API key

PowerShell users may need `webcmd.cmd` if execution policy blocks the `webcmd.ps1` shim. Set `WEBCMD_BIN=webcmd.cmd` in `.env` when required.

## Setup

```powershell
cd "D:\SLAB HACKATHON\slab_universal_agent"
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and set `GEMINI_API_KEY`. Never commit `.env` or real personal data. Update `data/user_memory.json` with values appropriate for your demo; document paths should point to local files.

Install and verify WebCMD:

```powershell
npm install -g @agentrhq/webcmd
webcmd.cmd doctor
webcmd.cmd skills add --provider agents --scope user
```

For real browser workflows, install the relevant WebCMD plugin and replace the mock adapter implementation with site-specific selectors or a learned WebCMD command. Keep the user confirmation boundary for irreversible actions.

## Run

From the project root, use module mode so Python package imports resolve correctly:

```powershell
$env:WEBCMD_BIN = "webcmd.cmd" # only needed when webcmd is blocked by PowerShell policy
python -m src.universal_agent
```

Example prompts:

```text
Find scholarships and internships for me
Prepare my application for the active software engineering role
Show my electricity and mobile bills
Pay all my due bills
Find a dermatologist near my preferred location
```

A payment request first displays the bill summary and proceeds only when the prompt asks for the literal confirmation `yes`. The supplied billing adapter returns a mock payment reference and does not charge an account.

## Direct adapter smoke tests

The adapters can be run without WebCMD while developing their JSON contract:

```powershell
node adapters\student_portal_adapter.js --target internships --search-terms python,IoT --student-profile '{"name":"Demo","skills":["Python"]}'
node adapters\billing_aggregator_adapter.js --action status --billing-accounts '{"electricity":"ACC-1","mobile":"9999999999"}'
```

## Production hardening checklist

Before connecting real websites, add authenticated WebCMD profiles, site-specific adapter verification, encrypted or OS-backed secret storage, file existence and permission checks for uploaded documents, audit logging with sensitive values redacted, and explicit confirmation for every irreversible action. Healthcare integrations should only handle discovery and booking logistics and must not provide medical diagnoses.

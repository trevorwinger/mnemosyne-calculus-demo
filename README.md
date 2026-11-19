# Mnemosyne · Calculus III Demo

Mnemosyne is a shareable, single-interface demonstration of course-scoped tutoring. It opens directly into **Alex**, one fictional **MATH 242 Calculus and Analytic Geometry III** student's chat, with cited Calculus III material and a course-scope harness. There is no account selection, course dashboard, instructor tool, or course-administration path.

Use this repository to let colleagues evaluate the student experience and attempt to bypass its course, source, and solution-boundary protections. It is a demonstration environment, not a production student-data system.

## Quick start by operating system

You need **Git** to clone the repository. Node.js is **not** required. The launchers install Docker and Ollama if they are absent, download `gemma4:e4b`, verify/unpack the bundled textbook, build the local services, then open the demo. The first run needs several GB of free disk space and can take a while because Docker images and the model are downloaded.

### macOS (Apple Silicon or Intel)

```sh
git clone <the-repository-url-you-were-sent>
cd mnemosyne-calculus-demo
./bootstrap-demo.sh
```

If Docker is not installed, the script downloads the official Docker Desktop disk image and asks for your macOS administrator password to install it. It starts Docker Desktop and accepts its license during installation. If macOS shows a security or system-extension prompt, complete it and rerun the script.

### Linux (Ubuntu/Debian/Fedora and other systemd distributions)

```sh
git clone <the-repository-url-you-were-sent>
cd mnemosyne-calculus-demo
./bootstrap-demo.sh
```

If Docker is missing, the script uses Docker's official Linux convenience installer and requests `sudo`. It can finish the first run with `sudo docker`; sign out and back in afterwards so the added `docker` group membership takes effect for normal Docker commands.

### Windows 10/11

Open **PowerShell** (not Git Bash), then run:

```powershell
git clone <the-repository-url-you-were-sent>
cd mnemosyne-calculus-demo
Set-ExecutionPolicy -Scope Process Bypass
.\bootstrap-demo.ps1
```

The PowerShell launcher uses `winget` to install Docker Desktop and Ollama if needed, starts both, then performs the same build and preprocessing steps. Docker Desktop needs WSL 2. If the script enables WSL, restart Windows when prompted and run the last two commands again. Complete any Docker Desktop first-run or license dialog before retrying.

All launchers open [http://localhost:3200](http://localhost:3200) when ready. The Calc III demo intentionally uses web port `3200` and API port `8200`, so it can run alongside the original Mnemosyne development stack and the Calc I demo. PostgreSQL is private to Docker and is not exposed on a host port.

To choose different free ports, set `MNEMOSYNE_WEB_PORT` and `MNEMOSYNE_API_PORT` before launching. For example on macOS/Linux: `MNEMOSYNE_WEB_PORT=3300 MNEMOSYNE_API_PORT=8300 ./bootstrap-demo.sh`.

Use a different Ollama model with `MNEMOSYNE_MODEL=model-name ./bootstrap-demo.sh`. To install Meta Llama 4 Scout as an additional model for the chat picker, run `MNEMOSYNE_PULL_LLAMA4_SCOUT=1 ./bootstrap-demo.sh` (or `./bootstrap-demo.ps1 -IncludeLlama4Scout` on Windows). Scout is an approximately 67 GB download, so it is opt-in; keep `gemma4:e4b` as the default for typical local machines.

Ollama runs on the host rather than inside Docker, so it automatically uses supported host GPU acceleration (including Apple Metal) when a model is loaded. No Docker GPU passthrough is required.

The repository includes `assets/apex-calculus-5e.pdf.zip`, an unchanged copy of the textbook for this noncommercial prototype. It is covered by the included [textbook licensing notice](LICENSE-TEXTBOOK.md). The bootstrap script extracts it to the Git-ignored `.local-content/` folder, then preprocessing imports the selected Calc III sections and worked examples into the private Docker volume.

To use a different lawfully obtained local APEX PDF instead:

```sh
APEX_TEXTBOOK_PDF=~/Downloads/apex-novideo.pdf ./bootstrap-demo.sh
```

The extracted PDF remains in `.local-content/` on the host, is copied into the prototype's private Docker volume, and is not served by the app as a student download. The extracted copy is ignored by Git.

## Textbook preprocessing

The supplied **APEX Calculus, 5th edition (2026)** PDF is licensed [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/). Mnemosyne retains attribution and extracts the complete Chapters 9–15 Calc III source set—not the whole book:

- Sequences and series: §§9.1–9.8
- Curves in the plane: §§10.1–10.5
- Vectors: §§11.1–11.6
- Vector-valued functions: §§12.1–12.5
- Functions of several variables: §§13.1–13.8
- Multiple integration: §§14.1–14.7
- Vector analysis: §§15.1–15.7

Each imported section includes its introduction and up to three worked-example samples, with stable citation chunks. The chat’s **Textbook focus** control scopes retrieval to a chapter category or all imported sections. The archive is retained only for local preprocessing; the original PDF is not exposed through the application.

## Demo access

Open [http://localhost:3200](http://localhost:3200). Mnemosyne automatically opens Alex's most recent chat. Use **New chat** to begin a separate session and **Chat history** to revisit prior sessions.

The bootstrap configures Gemma as the standard tutor. Use **Refresh models** in chat to select any other locally installed Ollama model. The labeled `demo-tutor` also works without Ollama.

## Shareable chat transcripts

Every completed tutoring turn automatically refreshes one JSON transcript per chat session in the repository's local `chats/` directory. Messages include an explicit per-session sequence number, role, timestamp, citations, and session/course/model metadata, so the original conversational order is retained even when messages share a timestamp. These JSON files are intentionally Git-ignored: review and redact them before sending one to a colleague, then attach the relevant `chats/<session-id>.json` file to a follow-up or issue. The folder is mounted into the API container, so transcripts remain available after containers are restarted.

When assessable learning evidence is recorded, the background worker also replaces one private, course-scoped student profile at `uploads/student-skills/<opaque-student-course-hash>_skill.md`. It uses only evidence-backed observations and safe tutoring strategies; it is never an answer key or a source of completed solutions. Each refresh writes a numbered, Git-ignored snapshot to `chats/skill-profiles/` for local audit, while private storage retains only the newest profile.

## Safety evaluation

Read [SECURITY_TESTING.md](SECURITY_TESTING.md) before sharing the prototype. It provides a small, ethical test matrix for course-boundary, prompt-injection, and solution-leakage checks, and explains how to report failures without putting real student data in prompts.

## Operations

| Command | Purpose |
| --- | --- |
| `./bootstrap-demo.sh` | macOS/Linux: install/start Docker and Ollama, pull Gemma, build, start, migrate, and seed. |
| `.\bootstrap-demo.ps1` | Windows: install/start Docker Desktop and Ollama, pull Gemma, build, start, migrate, and seed. |
| `docker compose up -d --build` | Build changed images and start services later. |
| `docker compose stop` | Stop services while retaining prototype data. |
| `docker compose logs -f` | Follow service logs. |
| `docker compose down` | Stop/remove containers while retaining data. |
| `docker compose down -v` | **Delete the prototype database and private uploaded book.** |

The default ports are web `3200` and API `8200`; PostgreSQL is not exposed to the host. If Docker cannot access a package registry on a campus network, reconnect to a network that permits Docker Hub, npm, PyPI, and Ollama downloads, or configure Docker Desktop's proxy/certificates.

## Production boundary

This branch uses development-only identity selection and has no authentication. Do not collect real student data or deploy it to a public network. A production deployment requires institution-managed authentication, HTTPS, a security review, backups, and a configured data-retention policy.

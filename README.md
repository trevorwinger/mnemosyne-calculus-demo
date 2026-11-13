# Mnemosyne · Calculus Demo

Mnemosyne is a shareable, single-interface demonstration of course-scoped tutoring. It opens directly into **Alex**, one fictional **MATH-240 Calculus I** student's chat, with cited Calculus material and a course-scope harness. There is no account selection, course dashboard, instructor tool, or course-administration path.

Use this branch to let colleagues evaluate the student experience and attempt to bypass its course, source, and solution-boundary protections. It is a demonstration environment, not a production student-data system.

## One-command quick start

Prerequisites: Git and a running [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine with the Compose plugin on Linux). Node.js is **not** required on the host. Docker Desktop is the one prerequisite kept manual because its installation and first launch require operating-system-specific permissions and acceptance screens.

```sh
git clone <the-repository-url-you-were-sent>
cd mnemosyne-calculus-demo
./bootstrap-demo.sh
```

The script installs and starts [Ollama](https://ollama.com), downloads `gemma3:4b`, builds the local images, starts the demo, migrates the database, and seeds the course. It opens [http://localhost:3000](http://localhost:3000) when ready. The first run can take several minutes because Docker images and the Gemma model must be downloaded.

Use a different Ollama model with `MNEMOSYNE_MODEL=model-name ./bootstrap-demo.sh`.

The repository deliberately does not redistribute the textbook PDF. Without it, Mnemosyne seeds original, compact Calculus learning cards so the demo works immediately. To import selected textbook sections from a lawfully obtained local APEX PDF:

```sh
APEX_TEXTBOOK_PDF=~/Downloads/apex-novideo.pdf ./bootstrap-demo.sh
```

The PDF remains in `.local-content/` on the host, is copied into the prototype's private Docker volume, and is not served as a student download. It is ignored by Git.

## Textbook preprocessing

The supplied **APEX Calculus, 5th edition (2026)** PDF is licensed [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/). Mnemosyne retains attribution and extracts a Calc I source set—not the whole book—for these sections:

- Limits and continuity: §§1.1, 1.3–1.5
- Derivatives: §§2.1, 2.3–2.6
- Using derivatives: §§3.1–3.4
- Derivative applications: §§4.2–4.3

Each imported section includes its introduction and up to three worked-example samples, with stable citation chunks. The chat’s **Textbook focus** control scopes retrieval to a chapter category or all imported sections. The original file stays private; no textbook content is added to this repository.

## Demo access

Open [http://localhost:3000](http://localhost:3000). Mnemosyne automatically opens Alex's most recent chat. Use **New chat** to begin a separate session and **Chat history** to revisit prior sessions.

The bootstrap configures Gemma as the standard tutor. Use **Refresh models** in chat to select any other locally installed Ollama model. The labeled `demo-tutor` also works without Ollama.

## Safety evaluation

Read [SECURITY_TESTING.md](SECURITY_TESTING.md) before sharing the prototype. It provides a small, ethical test matrix for course-boundary, prompt-injection, and solution-leakage checks, and explains how to report failures without putting real student data in prompts.

## Operations

| Command | Purpose |
| --- | --- |
| `./bootstrap-demo.sh` | Install/start Ollama, pull Gemma, build, start, migrate, and seed. |
| `docker compose up -d --build` | Build changed images and start services later. |
| `docker compose stop` | Stop services while retaining prototype data. |
| `docker compose logs -f` | Follow service logs. |
| `docker compose down` | Stop/remove containers while retaining data. |
| `docker compose down -v` | **Delete the prototype database and private uploaded book.** |

The default ports are web `3000`, API `8000`, and PostgreSQL `5432`. If Docker cannot access a package registry on a campus network, reconnect to a network that permits Docker Hub, npm, PyPI, and Ollama downloads, or configure Docker Desktop's proxy/certificates.

## Production boundary

This branch uses development-only identity selection and has no authentication. Do not collect real student data or deploy it to a public network. A production deployment requires institution-managed authentication, HTTPS, a security review, backups, and a configured data-retention policy.

import { existsSync, copyFileSync, readFileSync } from "node:fs";
import { spawnSync } from "node:child_process";

const run = (command, args) => spawnSync(command, args, { stdio: "inherit" });
const npm = process.platform === "win32" ? "npm.cmd" : "npm";
const nodeMajor = Number(process.versions.node.split(".")[0]);
if (nodeMajor < 20) {
  console.error("Node.js 20 or newer is required. Install a supported Node.js release, then rerun: npm run setup");
  process.exit(1);
}
if (!existsSync(".env")) {
  copyFileSync(".env.example", ".env");
  const env = readFileSync(".env", "utf8");
  if (env.includes("change-me-before-production")) console.log("Created .env. Change the database password before any non-local use.");
} else console.log("Preserved existing .env.");

const docker = run("docker", ["compose", "version"]);
if (docker.status !== 0) {
  console.error("\nDocker with Compose is required. Install Docker Desktop, start it, then rerun: npm run setup");
  process.exit(1);
}
const dependencies = run(npm, ["run", "install:deps"]);
if (dependencies.status !== 0) process.exit(1);
const env = readFileSync(".env", "utf8");
const ollama = env.match(/^OLLAMA_BASE_URL=(.+)$/m)?.[1]?.trim() || "http://host.docker.internal:11434";
// `host.docker.internal` is valid from a container but normally not resolvable
// from this host-side bootstrap process.
const ollamaProbeUrl = ollama.replace("host.docker.internal", "localhost");
let ollamaReady = false;
try { ollamaReady = (await fetch(`${ollamaProbeUrl.replace(/\/$/, "")}/api/tags`, { signal: AbortSignal.timeout(2500) })).ok; } catch { /* reported below */ }
if (!ollamaReady) {
  console.warn(`\nOllama was not reachable at ${ollama}. Live tutoring will be unavailable; the labeled demo provider can still be used in development.`);
  console.warn("Recovery: install/start Ollama on the host, run `ollama pull <approved-model>`, set OLLAMA_BASE_URL in .env, then rerun npm run setup.");
}
const launch = run("docker", ["compose", "up", "-d"]);
if (launch.status !== 0) {
  console.error("\nCompose could not start. Check for occupied ports with `docker compose ps`, then inspect `docker compose logs` and rerun npm run setup.");
  process.exit(1);
}
let ready = false;
for (let attempt = 1; attempt <= 30; attempt += 1) {
  try {
    const [api, web] = await Promise.all([
      fetch("http://localhost:8000/health", { signal: AbortSignal.timeout(1500) }),
      fetch("http://localhost:3000", { signal: AbortSignal.timeout(1500) }),
    ]);
    if (api.ok && web.ok) { ready = true; break; }
  } catch { /* services are still starting */ }
  await new Promise(resolve => setTimeout(resolve, 1000));
}
if (!ready) {
  console.error("\nServices did not become healthy within 30 seconds. Run `docker compose logs --tail=100`, resolve the reported issue, then rerun npm run setup.");
  process.exit(1);
}
const migrate = run("docker", ["compose", "exec", "-T", "api", "alembic", "upgrade", "head"]);
if (migrate.status !== 0) { console.error("Migration failed. Inspect `docker compose logs api` before retrying; persistent data was not removed."); process.exit(1); }
const seed = run("docker", ["compose", "exec", "-T", "api", "python", "-m", "app.seed"]);
if (seed.status !== 0) { console.error("Demo seed failed. Inspect `docker compose logs api` before retrying."); process.exit(1); }
console.log(`\nMnemosyne is ready at http://localhost:3000${ollamaReady ? " with a reachable Ollama endpoint." : " in labeled demo-only mode."}`);

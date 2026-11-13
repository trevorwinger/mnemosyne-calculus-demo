import { spawnSync } from "node:child_process";

const checks = [
  ["Node.js", process.execPath, ["--version"]],
  ["Docker", "docker", ["--version"]],
  ["Docker Compose", "docker", ["compose", "version"]],
];
let failed = false;
for (const [label, command, args] of checks) {
  const check = spawnSync(command, args, { encoding: "utf8" });
  if (check.status === 0) console.log(`✓ ${label}: ${(check.stdout || check.stderr).trim()}`);
  else { console.error(`✗ ${label} is unavailable.`); failed = true; }
}
if (failed) {
  console.error("\nInstall Docker Desktop (or Docker Engine with the Compose plugin), then run npm run setup again.");
  process.exit(1);
}
const engine = spawnSync("docker", ["info", "--format", "{{.ServerVersion}}"], { encoding: "utf8" });
if (engine.status !== 0) {
  console.error("✗ Docker is installed but its engine is not reachable. Start Docker Desktop (or the Docker daemon), then rerun npm run doctor.");
  process.exit(1);
}
console.log(`✓ Docker engine: ${engine.stdout.trim()}`);
console.log("\nLocal Ollama is optional for the seeded demo, but required for live tutoring. Expected endpoint: http://localhost:11434");

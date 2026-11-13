import { spawnSync } from "node:child_process";

const npm = process.platform === "win32" ? "npm.cmd" : "npm";
const run = (command, args) => spawnSync(command, args, { stdio: "inherit" });
const fail = (message) => { console.error(`\n${message}`); process.exit(1); };

const nodeMajor = Number(process.versions.node.split(".")[0]);
if (nodeMajor < 20) fail("Node.js 20 or newer is required. Install a supported Node.js release, then rerun: npm run install:deps");

if (run("docker", ["compose", "version"]).status !== 0) {
  fail("Docker with Compose is required. Install and start Docker Desktop (or Docker Engine with the Compose plugin), then rerun: npm run install:deps");
}
if (run("docker", ["info", "--format", "{{.ServerVersion}}"]).status !== 0) {
  fail("Docker is installed but its engine is not reachable. Start Docker Desktop (or the Docker daemon), then rerun: npm run install:deps");
}

console.log("\nInstalling the web application's Node dependencies…");
if (run(npm, ["ci", "--prefix", "apps/web"]).status !== 0) fail("Web dependency installation failed. Check your npm registry/network connection and retry.");

console.log("\nBuilding local API, web, and sandbox-runner images (this installs their container dependencies)…");
if (run("docker", ["compose", "build", "api", "web", "runner"]).status !== 0) {
  fail("Container dependency installation failed. Check Docker's network access, then rerun: npm run install:deps");
}

console.log("\nDependencies are ready. Start the application with: npm run setup");

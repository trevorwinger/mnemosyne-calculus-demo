import { spawnSync } from "node:child_process";

const command = process.platform === "win32" ? "docker.exe" : "docker";
const result = spawnSync(command, ["compose", ...process.argv.slice(2)], { stdio: "inherit" });
process.exit(result.status ?? 1);

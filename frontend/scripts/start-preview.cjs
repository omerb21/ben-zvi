const { spawn } = require("node:child_process");

const port = Number.parseInt(process.env.PORT || "8080", 10);
const safePort = Number.isFinite(port) && port > 0 ? String(port) : "8080";

const child = spawn(
  process.execPath,
  [
    "node_modules/vite/bin/vite.js",
    "preview",
    "--host",
    "0.0.0.0",
    "--port",
    safePort,
    "--strictPort",
  ],
  {
    stdio: "inherit",
    env: process.env,
  }
);

child.on("exit", (code) => {
  process.exit(code ?? 0);
});

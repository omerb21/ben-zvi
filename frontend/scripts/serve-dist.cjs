const http = require("node:http");
const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "..", "dist");
const port = Number.parseInt(process.env.PORT || "8080", 10);
const host = "0.0.0.0";

const MIME_TYPES = {
  ".html": "text/html; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".mjs": "application/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".svg": "image/svg+xml",
  ".ico": "image/x-icon",
  ".webp": "image/webp",
  ".woff": "font/woff",
  ".woff2": "font/woff2",
};

function resolvePath(urlPath) {
  const cleanPath = decodeURIComponent((urlPath || "/").split("?")[0]);
  const relativePath = cleanPath === "/" ? "index.html" : cleanPath.replace(/^\/+/, "");
  const requested = path.resolve(root, relativePath);

  if (!requested.startsWith(root)) {
    return null;
  }

  if (fs.existsSync(requested) && fs.statSync(requested).isFile()) {
    return requested;
  }

  return path.join(root, "index.html");
}

const server = http.createServer((req, res) => {
  try {
    const filePath = resolvePath(req.url || "/");
    if (!filePath || !fs.existsSync(filePath)) {
      res.statusCode = 404;
      res.end("Not found");
      return;
    }

    const ext = path.extname(filePath).toLowerCase();
    res.statusCode = 200;
    res.setHeader("Content-Type", MIME_TYPES[ext] || "application/octet-stream");
    fs.createReadStream(filePath).pipe(res);
  } catch (err) {
    res.statusCode = 500;
    res.setHeader("Content-Type", "text/plain; charset=utf-8");
    res.end("Server error");
    console.error("serve-dist error:", err);
  }
});

server.listen(Number.isFinite(port) && port > 0 ? port : 8080, host, () => {
  console.log(`Static server running at http://${host}:${port}`);
});

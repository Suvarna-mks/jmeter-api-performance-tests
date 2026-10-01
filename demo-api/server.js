// Tiny shop API to load test locally (never point load tests at public sites).
const http = require("http");

const PORT = process.env.PORT || 3456;
const products = [
  { id: 1, name: "Notebook", price: 120 },
  { id: 2, name: "Pen", price: 20 },
  { id: 3, name: "Backpack", price: 1499 },
];
const tokens = new Set();

function send(res, status, body) {
  res.writeHead(status, { "Content-Type": "application/json" });
  res.end(JSON.stringify(body));
}

function readBody(req) {
  return new Promise((resolve) => {
    let data = "";
    req.on("data", (c) => (data += c));
    req.on("end", () => {
      try { resolve(JSON.parse(data || "{}")); } catch { resolve(null); }
    });
  });
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, "http://localhost");

  if (req.method === "GET" && url.pathname === "/health") return send(res, 200, { status: "ok" });

  if (req.method === "GET" && url.pathname === "/products") return send(res, 200, products);

  const m = url.pathname.match(/^\/products\/(\d+)$/);
  if (req.method === "GET" && m) {
    const p = products.find((x) => x.id === Number(m[1]));
    return p ? send(res, 200, p) : send(res, 404, { error: "not found" });
  }

  if (req.method === "POST" && url.pathname === "/login") {
    const body = await readBody(req);
    if (!body || body.username !== "demo" || body.password !== "demo123") return send(res, 401, { error: "bad credentials" });
    const token = Math.random().toString(36).slice(2);
    tokens.add(token);
    return send(res, 200, { token });
  }

  if (req.method === "GET" && url.pathname === "/orders") {
    const auth = (req.headers.authorization || "").replace("Bearer ", "");
    if (!tokens.has(auth)) return send(res, 401, { error: "unauthorized" });
    return send(res, 200, [{ id: 101, productId: 1, qty: 2 }]);
  }

  // Simulates a slow endpoint so the duration assertion has something to catch
  if (req.method === "GET" && url.pathname === "/search") {
    const delay = Number(process.env.SEARCH_DELAY_MS || 50);
    return setTimeout(() => send(res, 200, products.filter((p) => p.name.toLowerCase().includes((url.searchParams.get("q") || "").toLowerCase()))), delay);
  }

  send(res, 404, { error: "not found" });
});

server.listen(PORT, () => console.log(`demo api on http://localhost:${PORT}`));

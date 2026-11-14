import { defineConfig, loadEnv } from 'vite';
import { fileURLToPath } from 'node:url';

/**
 * Local stand-in for the Netlify function: serves POST /api/analyst from the
 * same code, with GEMINI_API_KEY read from web/.env (gitignored). The key
 * only ever lives in this Node process, never in the browser bundle.
 */
function analystDevApi(env) {
  return {
    name: 'analyst-dev-api',
    configureServer(server) {
      for (const k of ['GEMINI_API_KEY', 'GEMINI_MODEL', 'ANALYST_PER_VISITOR_PER_DAY', 'ANALYST_TOTAL_PER_DAY']) {
        if (env[k] && !process.env[k]) process.env[k] = env[k];
      }
      let quota;
      server.middlewares.use('/api/analyst', async (req, res) => {
        // Loaded per request: Vite caches it and reloads it after an edit.
        const core = await server.ssrLoadModule('/server/analyst-core.mjs');
        quota ??= core.memoryQuota();
        const chunks = [];
        for await (const c of req) chunks.push(c);
        const request = new Request('http://localhost/api/analyst', {
          method: req.method,
          headers: { 'Content-Type': 'application/json' },
          body: req.method === 'POST' ? Buffer.concat(chunks) : undefined,
        });
        const out = await core.handleAnalyst(request, { ip: req.socket.remoteAddress || 'local', quota });
        res.statusCode = out.status;
        out.headers.forEach((v, k) => res.setHeader(k, v));
        res.end(Buffer.from(await out.arrayBuffer()));
      });
    },
  };
}

// Two static pages, no server. `base: './'` keeps every asset path relative,
// so the built dist/ folder works from any host or straight from disk.
export default defineConfig(({ mode }) => ({
  base: './',
  plugins: [analystDevApi(loadEnv(mode, fileURLToPath(new URL('.', import.meta.url)), ''))],
  build: {
    rollupOptions: {
      input: {
        story: fileURLToPath(new URL('./index.html', import.meta.url)),
        explorer: fileURLToPath(new URL('./explorer.html', import.meta.url)),
      },
    },
  },
}));

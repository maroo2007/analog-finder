// Netlify Function: /api/analyst (GET: is the analyst set up? POST: a
// question). Holds GEMINI_API_KEY (set in the
// Netlify UI as an environment variable, never in netlify.toml or the repo).
// Docs: https://docs.netlify.com/build/functions/get-started/
import { getStore } from '@netlify/blobs';
import { handleAnalyst, memoryQuota, quotaDay, LIMITS } from '../../server/analyst-core.mjs';

const fallback = memoryQuota();

/**
 * Daily counts per visitor and in total, in Netlify Blobs. Writes are
 * conditional on the last read (onlyIfMatch / onlyIfNew), so two requests
 * at once cannot both slip past the limit.
 */
function blobQuota() {
  const store = getStore({ name: 'analyst-quota', consistency: 'strong' });
  async function bump(key, limit) {
    for (let attempt = 0; attempt < 4; attempt++) {
      const cur = await store.getWithMetadata(key, { type: 'json' });
      const n = cur?.data?.n ?? 0;
      if (n >= limit) return false;
      const res = await store.setJSON(key, { n: n + 1 }, cur ? { onlyIfMatch: cur.etag } : { onlyIfNew: true });
      if (res?.modified !== false) return true;
    }
    return false;
  }
  return {
    // Visitor first, so a visitor over their limit never uses up the site's
    // total; follow-up requests for the same question skip the visitor count.
    async take(ip, { question = true } = {}) {
      const day = quotaDay();
      if (question && !(await bump(`${day}/ip/${ip}`, LIMITS.perVisitorPerDay))) return { ok: false, reason: 'visitor' };
      if (!(await bump(`${day}/total`, LIMITS.totalPerDay))) return { ok: false, reason: 'total' };
      return { ok: true };
    },
  };
}

export default async (req, context) => {
  // If Blobs is unavailable, count in this instance's memory instead.
  let blobs = null;
  try { blobs = blobQuota(); } catch (err) { console.warn('Blobs unavailable', err); }
  const quota = {
    async take(ip, opts) {
      if (blobs) {
        try { return await blobs.take(ip, opts); } catch (err) { console.warn('Blobs quota failed', err); }
      }
      return fallback.take(ip, opts);
    },
  };
  try {
    return await handleAnalyst(req, { ip: context.ip || 'unknown', quota });
  } catch (err) {
    console.error(err);
    return new Response(JSON.stringify({ error: 'The analyst could not answer just now.' }), { status: 500, headers: { 'Content-Type': 'application/json' } });
  }
};

// Bursts are stopped before the function even runs: at most 8 questions a
// minute from one visitor (Netlify rate limiting, available on the free plan).
export const config = {
  path: '/api/analyst',
  rateLimit: { windowLimit: 8, windowSize: 60, aggregateBy: ['ip', 'domain'] },
};

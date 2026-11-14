// Vercel Function: /api/analyst (GET: is the analyst set up? POST: a
// question). The same shared code as the Netlify function
// (../server/analyst-core.mjs), so both hosts behave the same. It holds
// GEMINI_API_KEY, set in the Vercel project's environment variables, never
// in vercel.json or the repository.
//
// Daily limits (25 questions per visitor, 100 Gemini requests for the whole
// site) are counted in this function instance's memory. Vercel has no
// built-in store like Netlify Blobs, so the counts start again when a new
// instance starts; Gemini's own free-tier limit still applies on top.
import { handleAnalyst, memoryQuota } from '../server/analyst-core.mjs';

const quota = memoryQuota();

/** The visitor's IP, from the headers Vercel sets on every request. */
function ipOf(request) {
  const real = request.headers.get('x-real-ip');
  if (real) return real.trim();
  const forwarded = request.headers.get('x-forwarded-for');
  return forwarded ? forwarded.split(',')[0].trim() : 'unknown';
}

export default {
  async fetch(request) {
    try {
      return await handleAnalyst(request, { ip: ipOf(request), quota });
    } catch (err) {
      console.error(err);
      return new Response(JSON.stringify({ error: 'The analyst could not answer just now.' }), {
        status: 500,
        headers: { 'Content-Type': 'application/json; charset=utf-8' },
      });
    }
  },
};

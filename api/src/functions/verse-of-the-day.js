/* verse-of-the-day.js — GET /api/verse-of-the-day
 *
 * Proxies YouVersion's Platform API verse-of-the-day endpoint
 * (/v1/verse_of_the_days/{day}) for Home's Verse of the Day card.
 *
 * Same reasoning as unreached.js for why this is a same-origin proxy rather
 * than a direct browser call: the YOUVERSION_APP_KEY (sent as the
 * X-YVP-App-Key header) would otherwise ship inside the PWA's client-side
 * JS, and CORS support for direct browser calls isn't confirmed in
 * YouVersion's docs. Not gated to signed-in users — see the matching
 * staticwebapp.config.json route exception.
 *
 * YouVersion's own VOTD endpoint has no images (confirmed by research, not
 * just absence in the docs) and returns HTML content by default — this
 * handler asks for format=text and normalizes the response so the client
 * doesn't need to know any YouVersion-specific field names.
 *
 * Fails quiet (a distinct status per failure mode) so the client can fall
 * back to the existing local date-seeded pick from the user's own library
 * rather than showing an error — this is optional editorial content, not a
 * core workflow.
 */
const { app } = require('@azure/functions');

function dayOfYear() {
  const now = new Date();
  const start = Date.UTC(now.getUTCFullYear(), 0, 1);
  const diff = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()) - start;
  return Math.floor(diff / 86400000) + 1;
}

app.http('verseOfTheDay', {
  methods: ['GET'],
  route: 'verse-of-the-day',
  authLevel: 'anonymous',
  handler: async (request, context) => {
    const appKey = process.env.YOUVERSION_APP_KEY;
    if (!appKey) {
      return { status: 501, jsonBody: { error: 'Verse of the Day (YouVersion) is not configured yet.' } };
    }

    const day = dayOfYear();
    const url = `https://api.youversion.com/v1/verse_of_the_days/${day}?language_ranges=en&format=text`;

    let upstream;
    try {
      upstream = await fetch(url, { headers: { 'X-YVP-App-Key': appKey } });
    } catch (e) {
      context.error('verse-of-the-day: request to YouVersion failed', e);
      return { status: 502, jsonBody: { error: 'Could not reach YouVersion.' } };
    }
    if (!upstream.ok) {
      context.error('verse-of-the-day: YouVersion returned', upstream.status);
      return { status: 502, jsonBody: { error: 'YouVersion returned an error.' } };
    }

    let body;
    try {
      body = await upstream.json();
    } catch (e) {
      context.error('verse-of-the-day: invalid JSON from YouVersion', e);
      return { status: 502, jsonBody: { error: 'Unexpected response from YouVersion.' } };
    }

    const reference = body.reference_human || body.reference || null;
    const text = body.text || (body.content ? String(body.content).replace(/<[^>]+>/g, '').trim() : null);
    if (!text || !reference) {
      return { status: 502, jsonBody: { error: 'No verse returned.' } };
    }

    return { status: 200, jsonBody: { text, reference } };
  },
});

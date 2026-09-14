/* verse-image.js — GET /api/verse-image
 *
 * Proxies Unsplash's random-photo endpoint (/photos/random) to give the
 * Verse of the Day card a background image, per the owner's explicit
 * choice to source imagery separately from YouVersion's API (which has no
 * images at all).
 *
 * Same proxy reasoning as unreached.js/verse-of-the-day.js: keeps
 * UNSPLASH_ACCESS_KEY server-side, and Unsplash's docs don't confirm CORS
 * for direct browser calls either. Not gated to signed-in users.
 *
 * Keyword is picked from a small fixed pool of safe, always-good-looking
 * nature terms, date-seeded so the image is stable for the whole day and
 * changes alongside the verse — deliberately NOT derived from the verse's
 * topic (that would need a maintained per-topic keyword map for uncertain
 * payoff; the owner picked the simpler fixed pool).
 *
 * Unsplash's API Terms require attribution to both Unsplash and the
 * specific photographer, linked back to their profile with UTM params, on
 * every displayed photo — that attribution is rendered by the client using
 * the photographer fields this returns; it cannot be satisfied server-side.
 */
const { app } = require('@azure/functions');

const KEYWORDS = ['nature', 'mountains', 'sunrise', 'ocean', 'forest', 'sky', 'desert', 'meadow'];

function dayOfYear() {
  const now = new Date();
  const start = Date.UTC(now.getUTCFullYear(), 0, 1);
  const diff = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()) - start;
  return Math.floor(diff / 86400000) + 1;
}

app.http('verseImage', {
  methods: ['GET'],
  route: 'verse-image',
  authLevel: 'anonymous',
  handler: async (request, context) => {
    const accessKey = process.env.UNSPLASH_ACCESS_KEY;
    if (!accessKey) {
      return { status: 501, jsonBody: { error: 'Verse of the Day imagery is not configured yet.' } };
    }

    const keyword = KEYWORDS[dayOfYear() % KEYWORDS.length];
    const url = `https://api.unsplash.com/photos/random?query=${encodeURIComponent(keyword)}&orientation=landscape`;

    let upstream;
    try {
      upstream = await fetch(url, { headers: { Authorization: `Client-ID ${accessKey}` } });
    } catch (e) {
      context.error('verse-image: request to Unsplash failed', e);
      return { status: 502, jsonBody: { error: 'Could not reach Unsplash.' } };
    }
    if (!upstream.ok) {
      context.error('verse-image: Unsplash returned', upstream.status);
      return { status: 502, jsonBody: { error: 'Unsplash returned an error.' } };
    }

    let body;
    try {
      body = await upstream.json();
    } catch (e) {
      context.error('verse-image: invalid JSON from Unsplash', e);
      return { status: 502, jsonBody: { error: 'Unexpected response from Unsplash.' } };
    }

    const imageUrl = body.urls && (body.urls.regular || body.urls.full);
    const photographerName = body.user && body.user.name;
    const photographerProfile = body.user && body.user.links && body.user.links.html;
    if (!imageUrl || !photographerName || !photographerProfile) {
      return { status: 502, jsonBody: { error: 'No usable photo returned.' } };
    }

    return {
      status: 200,
      jsonBody: {
        imageUrl,
        photographerName,
        photographerUrl: `${photographerProfile}?utm_source=rooted_app&utm_medium=referral`,
      },
    };
  },
});

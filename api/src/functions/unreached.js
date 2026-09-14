/* unreached.js — GET /api/unreached-of-the-day
 *
 * Proxies Joshua Project's "unreached people group of the day" endpoint
 * (https://api.joshuaproject.net/v1/people_groups/daily_unreached.json) for
 * Home's Unreached of the Day card (DATA_MODEL.md §8, item 78).
 *
 * Why a proxy instead of the browser calling Joshua Project directly:
 *   1. The Joshua Project API key would otherwise have to ship inside the
 *      PWA's client-side JS, visible to anyone via view-source — this
 *      endpoint keeps it server-side only, as a Function App setting
 *      (JOSHUA_PROJECT_API_KEY), the same pattern sync.js already uses for
 *      COSMOS_CONNECTION_STRING.
 *   2. Joshua Project's own docs only show server-side sample code (PHP/
 *      Python/Ruby) and don't confirm CORS support for direct browser
 *      fetches, so a same-origin proxy sidesteps that uncertainty entirely.
 *
 * Unlike sync.js, this is NOT gated to signed-in users — Home shows this to
 * every visitor, so staticwebapp.config.json carries an explicit route
 * exception for this one path ahead of the general /api/* auth rule.
 *
 * The response is normalized to a small, stable shape the client can trust
 * regardless of upstream field-naming quirks — see the exact Joshua Project
 * field names in the comment above buildResult(). Verify those field names
 * against a real response once JOSHUA_PROJECT_API_KEY is actually set; this
 * was written from Joshua Project's own published column documentation, not
 * a live test call (no API key existed yet at the time this was written).
 */
const { app } = require('@azure/functions');

const JP_ENDPOINT = 'https://api.joshuaproject.net/v1/people_groups/daily_unreached.json';

// Joshua Project's documented field names (v1 "People Groups" column
// descriptions) — mapped to our own stable shape so upstream renames don't
// ripple into the client, and so a wrong guess here only needs a one-line
// fix rather than a client-side change.
function buildResult(raw) {
  return {
    name: raw.PeopNameInCountry || raw.PeopNameAcrossCountries || null,
    country: raw.Ctry || null,
    population: raw.Population != null ? Number(raw.Population) : null,
    religion: raw.PrimaryReligion || null,
    percentEvangelical: raw.PercentEvangelical != null ? Number(raw.PercentEvangelical) : null,
    percentAdherent: raw.PercentAdherents != null ? Number(raw.PercentAdherents) : null,
    language: raw.PrimaryLanguageName || null,
    photoUrl: raw.PeopleGroupPhotoURL || null,
  };
}

app.http('unreached', {
  methods: ['GET'],
  route: 'unreached-of-the-day',
  authLevel: 'anonymous',
  handler: async (request, context) => {
    const apiKey = process.env.JOSHUA_PROJECT_API_KEY;
    if (!apiKey) {
      // Not configured yet — a real, expected state until the owner signs
      // up for a free key and sets it as a Function App setting. Distinct
      // status so the client can stay quiet rather than showing an error.
      return { status: 501, jsonBody: { error: 'Unreached of the Day is not configured yet.' } };
    }

    let upstream;
    try {
      upstream = await fetch(`${JP_ENDPOINT}?api_key=${encodeURIComponent(apiKey)}`);
    } catch (e) {
      context.error('unreached-of-the-day: request to Joshua Project failed', e);
      return { status: 502, jsonBody: { error: 'Could not reach Joshua Project.' } };
    }
    if (!upstream.ok) {
      context.error('unreached-of-the-day: Joshua Project returned', upstream.status);
      return { status: 502, jsonBody: { error: 'Joshua Project returned an error.' } };
    }

    let body;
    try {
      body = await upstream.json();
    } catch (e) {
      context.error('unreached-of-the-day: invalid JSON from Joshua Project', e);
      return { status: 502, jsonBody: { error: 'Unexpected response from Joshua Project.' } };
    }

    // The daily_unreached endpoint is documented to return one people
    // group, but (like Joshua Project's other people_groups endpoints) may
    // wrap it in an array — handle both shapes.
    const raw = Array.isArray(body) ? body[0] : body;
    if (!raw || typeof raw !== 'object') {
      return { status: 502, jsonBody: { error: 'No people group returned.' } };
    }

    return { status: 200, jsonBody: buildResult(raw) };
  },
});

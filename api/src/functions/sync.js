/* sync.js — GET/POST /api/sync
 *
 * The one endpoint the client talks to for cross-device sync (DATA_MODEL.md
 * §7). Stores one Cosmos DB document per signed-in user, containing the
 * whole content/progress/settings bundle — see index.html's pullAndMerge()
 * / pushToCloud() for the client half of this.
 *
 * Auth: Azure Static Web Apps' platform authentication runs in front of this
 * (staticwebapp.config.json restricts /api/* to the "authenticated" role),
 * and forwards the verified identity as the base64-encoded
 * x-ms-client-principal header. This function never trusts a userId from the
 * request body — only from that header, decoded server-side. That's also
 * why COSMOS_CONNECTION_STRING lives only here, as a Function App setting,
 * and is never shipped to the browser.
 */
const { app } = require('@azure/functions');
const { CosmosClient } = require('@azure/cosmos');

const DB_NAME = 'RootedDB';
const CONTAINER_NAME = 'UserData';

let cachedContainer = null;
function getContainer() {
  if (cachedContainer) return cachedContainer;
  const conn = process.env.COSMOS_CONNECTION_STRING;
  if (!conn) return null;
  const client = new CosmosClient(conn);
  cachedContainer = client.database(DB_NAME).container(CONTAINER_NAME);
  return cachedContainer;
}

function getPrincipal(request) {
  const header = request.headers.get('x-ms-client-principal');
  if (!header) return null;
  try {
    const decoded = Buffer.from(header, 'base64').toString('utf-8');
    const principal = JSON.parse(decoded);
    return principal && principal.userId ? principal : null;
  } catch (e) {
    return null;
  }
}

app.http('sync', {
  methods: ['GET', 'POST'],
  route: 'sync',
  authLevel: 'anonymous', // platform-level auth (staticwebapp.config.json) gates this before it arrives; we still re-check the principal below in case the function is ever called directly.
  handler: async (request, context) => {
    const principal = getPrincipal(request);
    if (!principal) {
      return { status: 401, jsonBody: { error: 'Not signed in.' } };
    }

    const container = getContainer();
    if (!container) {
      context.error('COSMOS_CONNECTION_STRING is not configured.');
      return { status: 500, jsonBody: { error: 'Sync is not configured on the server yet.' } };
    }

    const docId = principal.userId;

    if (request.method === 'GET') {
      try {
        const { resource } = await container.item(docId, docId).read();
        return { status: 200, jsonBody: resource || null };
      } catch (e) {
        if (e.code === 404) return { status: 200, jsonBody: null };
        context.error('sync GET failed', e);
        return { status: 500, jsonBody: { error: 'Could not read your synced data.' } };
      }
    }

    // POST — upsert the whole bundle. Client sends {content, progress,
    // settings, updatedAt}; last-write-wins is decided client-side by
    // comparing updatedAt, so this endpoint just persists whatever it's given.
    let body;
    try {
      body = await request.json();
    } catch (e) {
      return { status: 400, jsonBody: { error: 'Invalid JSON body.' } };
    }
    if (!body || typeof body !== 'object') {
      return { status: 400, jsonBody: { error: 'Invalid body.' } };
    }

    const doc = {
      id: docId,
      userId: docId,
      identityProvider: principal.identityProvider || null,
      content: body.content ?? null,
      progress: body.progress ?? null,
      settings: body.settings ?? null,
      updatedAt: body.updatedAt || new Date().toISOString(),
    };

    try {
      await container.items.upsert(doc);
      return { status: 200, jsonBody: { ok: true, updatedAt: doc.updatedAt } };
    } catch (e) {
      context.error('sync POST failed', e);
      return { status: 500, jsonBody: { error: 'Could not save your synced data.' } };
    }
  },
});

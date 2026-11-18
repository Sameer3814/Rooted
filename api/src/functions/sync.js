/* sync.js — GET/POST /api/sync
 *
 * The one endpoint the client talks to for cross-device sync (DATA_MODEL.md
 * §7). Stores one Cosmos DB document per signed-in user, containing the
 * whole content/progress/settings bundle — see index.html's pullAndMerge()
 * / pushToCloud() for the client half of this.
 *
 * Auth (switched 2026-11-16 from Azure Static Web Apps' built-in GitHub
 * platform auth to Firebase Authentication — see the "Firebase
 * Authentication" comment in index.html and DATA_MODEL.md §7.1 for why):
 * the client sends a Firebase ID token as `Authorization: Bearer <token>`,
 * which this function verifies itself via the Admin SDK
 * (admin.auth().verifyIdToken) — it never trusts a userId from the request
 * body. staticwebapp.config.json now leaves /api/* open at the platform
 * level (SWA has no way to grant its "authenticated" role to a Firebase
 * session), so this verification is the real, sole gate, not a backup
 * behind SWA's own check the way the old x-ms-client-principal read was.
 * FIREBASE_SERVICE_ACCOUNT_JSON (like COSMOS_CONNECTION_STRING) lives only
 * here, as a Function App setting, never shipped to the browser.
 */
const { app } = require('@azure/functions');
const { CosmosClient } = require('@azure/cosmos');
const admin = require('firebase-admin');

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

function getFirebaseAuth() {
  const json = process.env.FIREBASE_SERVICE_ACCOUNT_JSON;
  if (!json) return null;
  if (!admin.apps.length) {
    admin.initializeApp({ credential: admin.credential.cert(JSON.parse(json)) });
  }
  return admin.auth();
}

async function getPrincipal(request) {
  const header = request.headers.get('authorization') || request.headers.get('Authorization');
  if (!header || !header.startsWith('Bearer ')) return null;
  const token = header.slice('Bearer '.length).trim();
  if (!token) return null;
  const auth = getFirebaseAuth();
  if (!auth) return null;
  try {
    const decoded = await auth.verifyIdToken(token);
    return { userId: decoded.uid, identityProvider: 'firebase', email: decoded.email || null };
  } catch (e) {
    return null;
  }
}

app.http('sync', {
  methods: ['GET', 'POST'],
  route: 'sync',
  authLevel: 'anonymous', // staticwebapp.config.json leaves /api/* open at the platform level now — verifyIdToken() below is the real gate, not a backup behind it.
  handler: async (request, context) => {
    const principal = await getPrincipal(request);
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

const CACHE = 'rooted-v20';
// data/verses.json (~1.1MB) is deliberately NOT precached — it's fetched lazily
// the first time Browse is opened, and the runtime cache below picks it up then.
// starter-pack.json, stories.json, motifs.json and connections.json all load
// at boot, so they belong here.
const ASSETS = ['./', './index.html', './manifest.json', './icon.png',
                './data/starter-pack.json', './data/stories.json',
                './data/motifs.json', './data/connections.json'];

self.addEventListener('install', e=>{
  e.waitUntil(
    caches.open(CACHE).then(c=>
      // Cache assets individually so one missing file doesn't abort the whole install.
      Promise.all(ASSETS.map(url=>
        c.add(url).catch(err=>console.warn('sw: skipped caching', url, err))
      ))
    )
  );
  self.skipWaiting();
});

self.addEventListener('activate', e=>{
  e.waitUntil(
    caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k))))
  );
  self.clients.claim();
});

self.addEventListener('fetch', e=>{
  if(e.request.method !== 'GET') return;
  e.respondWith(
    caches.match(e.request).then(cached=>{
      const fetchPromise = fetch(e.request).then(resp=>{
        if(resp && resp.status===200){
          const clone = resp.clone();
          caches.open(CACHE).then(c=>c.put(e.request, clone));
        }
        return resp;
      }).catch(()=>cached);
      return cached || fetchPromise;
    })
  );
});

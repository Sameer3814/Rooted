const CACHE = 'rooted-v149';
// data/verses.json (~8MB, the entire 66-book Bible) is deliberately NOT precached — it's fetched lazily
// the first time Browse is opened, and the runtime cache below picks it up then. Character
// portraits (data/character_portraits.json + media/characters/*.jpg, item 91) get the same
// lazy treatment for the same reason — only one character's photo loads per visit to their
// page, not all 25+ on every visit, so precaching them all at install would be pure waste.
// data/lexicon_full.json (~3.7MB, item 151) is the same story — lazy-loaded the first time
// the Lexicon screen opens, not precached. data/interlinear_ot.json (~11MB) and
// data/interlinear_nt.json (~3.9MB, item 151 batch 2) are lazy per-testament too — fetched
// only when a Verse Detail's Hebrew/Greek toggle is actually opened.
// starter-pack.json, stories.json, motifs.json, connections.json, word_of_the_day.json,
// daily_facts.json (item 116), and lexicon_seed.json (item 150) all load at boot, so they
// belong here. church_history.json was removed (item 117, the whole feature was retired)
// — no longer precached.
// The two Home placeholder photos (item 83) render on every Home visit, so they're worth
// precaching too.
const ASSETS = ['./', './index.html', './manifest.json', './icon.png',
                './data/starter-pack.json', './data/stories.json',
                './data/motifs.json', './data/connections.json',
                './data/word_of_the_day.json',
                './data/daily_facts.json',
                './data/lexicon_seed.json',
                './media/home/votd-placeholder.jpg', './media/home/story-placeholder.jpg'];

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

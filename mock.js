/*!
 * pangea8 Full Mock — shared runtime
 * Config (pricing, card, admin), Firebase (Google popup only),
 * coin wallet helpers, attempt guards, band tables.
 *
 * The apiKey is a public app identifier, not a secret.
 * Access control lives in Firestore security rules (see firestore.rules).
 */
(function () {
  'use strict';
  if (window.P8M) return;

  /* ================= CONFIG — edit prices/card here ================= */
  var CONFIG = {
    adminEmail: 'polatovmaqsudjon1@gmail.com',
    mockCost: 10, // coins per full mock
    /* Deliberately the cheapest full mock around: competitors charge
       ~30 000 UZS per online mock — here 1 mock = 10 000 UZS, less in bulk. */
    packages: [
      { coins: 10, uzs: 10000 },
      { coins: 30, uzs: 27000 },
      { coins: 50, uzs: 40000 }
    ],
    card: { number: '5477 3300 2441 7911', holder: 'POLATOV MAKSUDJON' },
    telegramContact: 'https://t.me/mrbmp13',
    telegramHandle: '@mrbmp13',
    feedbackEndpoint: 'https://pangeya-ai.vercel.app/api/essay-feedback',
    mocks: [
      { n: 1, id: 'mock1', title: 'Full Mock 1' },
      { n: 2, id: 'mock2', title: 'Full Mock 2' },
      { n: 3, id: 'mock3', title: 'Full Mock 3' },
      { n: 4, id: 'mock4', title: 'Full Mock 4' },
      { n: 5, id: 'mock5', title: 'Full Mock 5' }
    ]
  };

  var DEV = (location.hostname === 'localhost' || location.hostname === '127.0.0.1');

  /* ================= theme (origin-wide `theme` key) ================= */
  function applyTheme(t) {
    document.documentElement.setAttribute('data-p8m-theme', t === 'dark' ? 'dark' : 'light');
  }
  try { applyTheme(localStorage.getItem('theme') || 'light'); } catch (e) { applyTheme('light'); }
  function toggleTheme() {
    var cur = document.documentElement.getAttribute('data-p8m-theme') === 'dark' ? 'light' : 'dark';
    try { localStorage.setItem('theme', cur); } catch (e) {}
    applyTheme(cur);
  }

  /* ================= tiny helpers ================= */
  function esc(v) { return String(v == null ? '' : v).replace(/[&<>"']/g, function (c) { return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]; }); }
  function toast(msg, ms) {
    var el = document.getElementById('p8mToast');
    if (!el) {
      el = document.createElement('div');
      el.id = 'p8mToast';
      el.style.cssText = 'position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:#0a0a0a;color:#fff;padding:12px 22px;border-radius:12px;font:600 14px/1.4 Inter,system-ui,sans-serif;z-index:9999;max-width:90vw;box-shadow:0 8px 30px rgba(0,0,0,.35);opacity:0;transition:opacity .25s;pointer-events:none;text-align:center';
      document.body.appendChild(el);
    }
    el.textContent = msg;
    el.style.opacity = '1';
    clearTimeout(el._t);
    el._t = setTimeout(function () { el.style.opacity = '0'; }, ms || 4200);
  }

  /* ================= band tables (BC/IDP approximations) ================= */
  var BAND_L = [[39, 9], [37, 8.5], [35, 8], [32, 7.5], [30, 7], [26, 6.5], [23, 6], [18, 5.5], [16, 5], [13, 4.5], [10, 4], [8, 3.5], [6, 3], [4, 2.5]];
  var BAND_R = [[39, 9], [37, 8.5], [35, 8], [33, 7.5], [30, 7], [27, 6.5], [23, 6], [19, 5.5], [15, 5], [13, 4.5], [10, 4], [8, 3.5], [6, 3], [4, 2.5]];
  function bandFromRaw(raw, table) {
    raw = Number(raw) || 0;
    if (raw <= 0) return 1;
    for (var i = 0; i < table.length; i++) if (raw >= table[i][0]) return table[i][1];
    return 2;
  }
  function halfRound(x) { return Math.round(x * 2) / 2; } // .25→.5, .75→next (ties up)
  function fmtBand(b) { return (b == null || isNaN(b)) ? 'N/A' : Number(b).toFixed(1); }

  /* ================= Firebase (compat, Google popup only) ================= */
  var SDK = 'https://www.gstatic.com/firebasejs/12.14.0/';
  var FB_CONFIG = {
    apiKey: 'AIzaSyAqS59ek0seZ0rcSZb3RPhiwTzleIAZ-9E',
    authDomain: 'ieltshub-e2aa8.firebaseapp.com',
    projectId: 'ieltshub-e2aa8',
    storageBucket: 'ieltshub-e2aa8.firebasestorage.app',
    messagingSenderId: '645780307385',
    appId: '1:645780307385:web:1dc8640e294be2204b4a68'
  };
  function loadScript(src) {
    return new Promise(function (resolve, reject) {
      var s = document.createElement('script');
      s.src = src; s.async = true;
      s.onload = resolve; s.onerror = function () { reject(new Error('load failed: ' + src)); };
      (document.head || document.documentElement).appendChild(s);
    });
  }

  var DEV_USER = { uid: 'dev-tester-uid', email: 'dev@local', displayName: 'Dev Tester', photoURL: '' };

  var ready;
  if (DEV) {
    ready = Promise.resolve({ dev: true, auth: null, db: null, user: DEV_USER });
  } else {
    ready = loadScript(SDK + 'firebase-app-compat.js')
      .then(function () { return loadScript(SDK + 'firebase-auth-compat.js'); })
      .then(function () { return loadScript(SDK + 'firebase-firestore-compat.js'); })
      .then(function () {
        var app = firebase.apps.length ? firebase.app() : firebase.initializeApp(FB_CONFIG);
        var auth = firebase.auth();
        var db = firebase.firestore();
        return new Promise(function (resolve) {
          var unsub = auth.onAuthStateChanged(function (user) {
            unsub();
            resolve({ dev: false, app: app, auth: auth, db: db, user: user || null, firebase: firebase });
          });
        });
      })
      .catch(function (err) {
        console.warn('[P8M] Firebase unavailable:', err && err.message);
        return null;
      });
  }

  function signInGoogle() {
    return ready.then(function (fb) {
      if (!fb) throw new Error('Firebase unavailable');
      if (fb.dev) return DEV_USER;
      var provider = new firebase.auth.GoogleAuthProvider();
      /* popup ONLY — signInWithRedirect never completes with a cross-site
         authDomain on modern browsers (see project rule). */
      return fb.auth.signInWithPopup(provider).then(function (cred) {
        fb.user = cred.user;
        return cred.user;
      });
    });
  }
  function signOutUser() {
    return ready.then(function (fb) { if (fb && !fb.dev) return fb.auth.signOut(); });
  }

  /* ================= wallet ================= */
  function devCoins(n) {
    if (n === undefined) return Number(localStorage.getItem('p8m_dev_coins') || 0);
    localStorage.setItem('p8m_dev_coins', String(n));
    return n;
  }
  /* getWallet → {coins} ; creates the doc (coins:0) on first touch */
  function getWallet(fb) {
    if (fb.dev) return Promise.resolve({ coins: devCoins() });
    var ref = fb.db.collection('wallets').doc(fb.user.uid);
    return ref.get().then(function (snap) {
      if (snap.exists) return snap.data();
      return ref.set({ coins: 0, email: fb.user.email || '', createdAt: Date.now() })
        .then(function () { return { coins: 0 }; });
    });
  }
  /* spendCoins → resolves new balance, rejects {code:'insufficient'} */
  function spendCoins(fb, n) {
    if (fb.dev) {
      var cur = devCoins();
      if (cur < n) return Promise.reject({ code: 'insufficient' });
      return Promise.resolve(devCoins(cur - n));
    }
    var ref = fb.db.collection('wallets').doc(fb.user.uid);
    return fb.db.runTransaction(function (tx) {
      return tx.get(ref).then(function (snap) {
        var coins = snap.exists ? (snap.data().coins || 0) : 0;
        if (coins < n) throw { code: 'insufficient' };
        var next = coins - n;
        if (snap.exists) tx.update(ref, { coins: next, updatedAt: Date.now() });
        else tx.set(ref, { coins: 0, createdAt: Date.now() }); // shouldn't happen
        return next;
      });
    });
  }
  function createCoinRequest(fb, pkg, name) {
    if (fb.dev) { devCoins(devCoins() + pkg.coins); return Promise.resolve('dev-auto-approved'); }
    return fb.db.collection('coin_requests').add({
      uid: fb.user.uid,
      email: fb.user.email || '',
      name: name || fb.user.displayName || '',
      coins: pkg.coins,
      uzs: pkg.uzs,
      status: 'pending',
      ts: Date.now()
    }).then(function (ref) { return ref.id; });
  }

  /* ================= attempt (sessionStorage) ================= */
  var STAGES = ['listening', 'reading', 'writing', 'result'];
  function getAttempt() {
    try { return JSON.parse(sessionStorage.getItem('p8m_attempt') || 'null'); } catch (e) { return null; }
  }
  function setAttempt(a) { sessionStorage.setItem('p8m_attempt', JSON.stringify(a)); }
  function advanceStage(stage) {
    var a = getAttempt();
    if (!a) return;
    a.stage = stage;
    setAttempt(a);
  }
  /* Mock 1 pages have no suffix (listening.html); mocks 2+ are suffixed
     (listening2.html). The result page is shared by every mock. */
  function pageFor(stage, n) {
    n = Number(n) || 1;
    if (stage === 'result') return 'result.html';
    return stage + (n > 1 ? String(n) : '') + '.html';
  }
  /* Each section page calls this: redirects home when there is no attempt,
     or to the current stage/mock page when the student reloads an older page. */
  function requireStage(stage, n) {
    var a = getAttempt();
    if (!a) { location.replace('index.html'); return null; }
    var an = Number(a.n) || 1;
    if (a.stage !== stage || (n && an !== Number(n))) {
      location.replace(pageFor(a.stage, an));
      return null;
    }
    return a;
  }
  function clearAttempt() {
    ['p8m_attempt', 'p8m_listening', 'p8m_reading', 'p8m_writing',
     'p8m_listening_state', 'p8m_reading_state', 'p8m_writing_state']
      .forEach(function (k) { sessionStorage.removeItem(k); });
  }
  function getPart(key) {
    try { return JSON.parse(sessionStorage.getItem(key) || 'null'); } catch (e) { return null; }
  }

  /* ================= coin icon (brand) ================= */
  var COIN_SVG = '<svg class="p8m-coin" viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">' +
    '<defs><linearGradient id="p8mCoinG" x1="0" y1="0" x2="1" y2="1">' +
    '<stop offset="0" stop-color="#34D399"/><stop offset="1" stop-color="#047857"/></linearGradient></defs>' +
    '<circle cx="12" cy="12" r="11" fill="url(#p8mCoinG)"/>' +
    '<circle cx="12" cy="12" r="8.4" fill="none" stroke="rgba(255,255,255,.55)" stroke-width="1" stroke-dasharray="2 1.6"/>' +
    '<text x="12" y="16.4" text-anchor="middle" font-family="Space Grotesk,Inter,sans-serif" font-size="12" font-weight="800" fill="#fff">8</text></svg>';

  window.P8M = {
    CONFIG: CONFIG, DEV: DEV,
    ready: ready, signInGoogle: signInGoogle, signOut: signOutUser,
    getWallet: getWallet, spendCoins: spendCoins, createCoinRequest: createCoinRequest,
    getAttempt: getAttempt, setAttempt: setAttempt, advanceStage: advanceStage,
    requireStage: requireStage, clearAttempt: clearAttempt, getPart: getPart, pageFor: pageFor,
    bandL: function (raw) { return bandFromRaw(raw, BAND_L); },
    bandR: function (raw) { return bandFromRaw(raw, BAND_R); },
    halfRound: halfRound, fmtBand: fmtBand,
    esc: esc, toast: toast, toggleTheme: toggleTheme, COIN_SVG: COIN_SVG,
    uzs: function (n) { return Number(n).toLocaleString('en-US').replace(/,/g, ' '); }
  };
})();

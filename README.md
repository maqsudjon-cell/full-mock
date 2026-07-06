# pangea8 Full Mock

Paid computer-delivered IELTS full mock (Listening → Reading → Writing in one sitting)
with a coin wallet, manual card-transfer top-ups, AI-marked writing and an
IELTS-style result sheet. Lives at **https://pangea8.com/full-mock/**.

## Pages

| File | What it does |
|---|---|
| `index.html` | Landing: Google/email sign-in, coin balance, buy-coins modal (card transfer + Telegram receipt), start mock, local results history |
| `listening.html` | Part 1 — Test 14 audio (streams from `pangea8.com/test14/*.mp3`), simulation mode only, auto-advances to Reading |
| `reading.html` | Part 2 — CDI Reading 5 engine, 60-min timer, auto-advances to Writing |
| `writing.html` | Part 3 — Task 1 (cars table) + Task 2 (change essay), 60-min timer |
| `result.html` | IELTS-style result sheet (no branch column, Speaking = N/A), AI examiner bands + feedback for writing, saves to Firestore `mock_results` |
| `admin.html` | Owner only (`polatovmaqsudjon1@gmail.com`): add coins to yourself (free-coin backdoor), approve/reject top-up requests, credit any UID, view all results |
| `mock.js` | Shared config — **prices, mock cost, card number, Telegram, admin email are all edited here** |
| `firestore.rules` | Security rules — must be pasted into the Firebase console once (see below) |

## One-time setup (required before coins work)

1. Open https://console.firebase.google.com → project **ieltshub-e2aa8** → Firestore Database → **Rules**.
2. Replace the whole rules text with the contents of `firestore.rules` and press **Publish**.
   (It keeps the existing `students`/`results` behaviour and adds `wallets`,
   `coin_requests`, `mock_results`.)

Until this is done the site shows a "coin system is being configured" notice.

## How the money flows

1. Student signs in (Google popup or pangea8.com/signin.html) → presses **Buy coins**.
2. Transfers to the card in `mock.js` (`CONFIG.card`) and sends the receipt to Telegram (`CONFIG.telegramContact`).
3. Presses “I’ve paid” → a `coin_requests` doc is created (status `pending`).
4. You open `admin.html`, check the receipt, press **Approve** → coins land in their wallet.
5. Starting a mock deducts `CONFIG.mockCost` coins (Firestore transaction — students can never add coins themselves; the rules only let balances go down).

## Free coins for yourself

`admin.html` → “+10 to me” / “+50 to me” / custom. Only works signed in as the admin email.

## Changing prices / content

- Prices & packages: `mock.js` → `CONFIG.packages`, `CONFIG.mockCost`.
- Different listening test: `CONFIG.mock.listeningAudioBase` + replace the question HTML/answers in `listening.html` (they come from `test14`).
- Different reading test: swap the AUTHORING AREA block in `reading.html` (same engine as `cdi-reading-*`).
- Writing topics: `TASKS` object at the top of the `<script>` in `writing.html`.

## Dev mode

On `localhost` the app runs without Firebase: a fake user is signed in and coins
live in `localStorage` (`p8m_dev_coins`), so the whole flow can be tested offline.

# Flarestamina Full Mock

Paid computer-delivered IELTS full mock (Listening → Reading → Writing in one sitting)
with a coin wallet, manual card-transfer top-ups, AI-marked writing and an
IELTS-style result sheet. Lives at **https://flarestamina.com/full-mock/**.

## Pages

| File | What it does |
|---|---|
| `index.html` | Landing: Google/email sign-in, coin balance, buy-coins modal (card transfer + Telegram receipt), 5 mock cards, local results history |
| `listening[N].html` | Part 1 — audio streams from the source test repo, simulation mode only, auto-advances to Reading |
| `reading[N].html` | Part 2 — CDI reading engine, 60-min timer, auto-advances to Writing |
| `writing[N].html` | Part 3 — Task 1 + Task 2 with 60-min timer (charts are inline SVG) |
| `result.html` | Shared IELTS-style result sheet (no branch column, Speaking = N/A), AI examiner bands + feedback for writing, saves to Firestore `mock_results` |
| `admin.html` | Owner only (`polatovmaqsudjon1@gmail.com`): add coins to yourself (free-coin backdoor), approve/reject top-up requests, credit any UID, view all results |
| `mock.js` | Shared config — **prices, mock cost, card number, Telegram, admin email, mock list are all edited here** |
| `build_mocks.py` | Generator that produced mocks 2–5 from hub engines (edit the `MOCKS`/`WRITING` maps to add more) |
| `firestore.rules` | Security rules — must be pasted into the Firebase console once (see below) |

### Mock contents (sources)

| Mock | Listening | Reading | Writing T1 | Writing T2 |
|---|---|---|---|---|
| 1 | Test 14 | CDI Reading 5 | Cars per 1000 (table) | Change in life |
| 2 | Test 19 | CDI Reading 6 | Car survey (2 bar charts) | Financial aid |
| 3 | Test 20 | CDI Reading 7 | UK household/leisure (table+chart) | Improve vs rest the mind |
| 4 | Test 21 | CDI Reading 1 | Library survey (pie+table) | Clubs vs family time |
| 5 | Test 22 | CDI Reading 2 | Internet access (table, authored in-house) | Educational leisure |

## One-time setup (required before coins work)

1. Open https://console.firebase.google.com → project **ieltshub-e2aa8** → Firestore Database → **Rules**.
2. Replace the whole rules text with the contents of `firestore.rules` and press **Publish**.
   (It keeps the existing `students`/`results` behaviour and adds `wallets`,
   `coin_requests`, `mock_results`.)

Until this is done the site shows a "coin system is being configured" notice.

## How the money flows

1. Student signs in (Google popup or flarestamina.com/signin.html) → presses **Buy coins**.
2. Transfers to the card in `mock.js` (`CONFIG.card`) and sends the receipt to Telegram (`CONFIG.telegramContact`).
3. Presses “I’ve paid” → a `coin_requests` doc is created (status `pending`).
4. You open `admin.html`, check the receipt, press **Approve** → coins land in their wallet.
5. Starting a mock deducts `CONFIG.mockCost` coins (Firestore transaction — students can never add coins themselves; the rules only let balances go down).

## Free coins for yourself

`admin.html` → “+10 to me” / “+50 to me” / custom. Only works signed in as the admin email.

## Changing prices / content

- Prices & packages: `mock.js` → `CONFIG.packages`, `CONFIG.mockCost`.
  Current pricing (2026-07-06): 10 coins = 10 000 UZS (1 mock), 30 = 27 000, 50 = 40 000 —
  intentionally ~3× cheaper than competitors (mock.ieltszone.uz charges 30 000 UZS per online mock).
- Different listening test: `CONFIG.mock.listeningAudioBase` + replace the question HTML/answers in `listening.html` (they come from `test14`).
- Different reading test: swap the AUTHORING AREA block in `reading.html` (same engine as `cdi-reading-*`).
- Writing topics: `TASKS` object at the top of the `<script>` in `writing.html`.

## Dev mode

On `localhost` the app runs without Firebase: a fake user is signed in and coins
live in `localStorage` (`p8m_dev_coins`), so the whole flow can be tested offline.

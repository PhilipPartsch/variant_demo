/*
 * ubc build html — search client (engine + UI), hand-written and
 * dependency-free.
 *
 * Three jobs, in one file so a page pays exactly one request for search:
 *
 *  1. Transport. The index is a CLASSIC script that calls
 *     `ubcSearch.setIndex({…})`; this file defines that hook before injecting
 *     `_static/ubc-search-index.js`. There is deliberately NO fetch/XHR, no ES
 *     module, no Worker and no absolute URL anywhere in this file — a built site
 *     must work when opened from the filesystem (`file://`), where every one of
 *     those fails on the opaque origin. A build test greps the emitted site for
 *     exactly those constructs.
 *
 *     Loading is LAZY: nothing is requested until the reader first engages with
 *     the box (focus or keydown), or the results page opens with a `?q=`. An
 *     ordinary page view costs zero search bytes.
 *
 *  2. The engine. A mirror of the reference scorer in
 *     `rust/ubc_search/src/score.rs` — same family table, same weights, same
 *     tie-break cascade, same query grammar. The two are kept structurally
 *     parallel ON PURPOSE so they can be diffed side by side; the Rust side is
 *     normative and snapshot-tested. This file NEVER stems: the index carries a
 *     `surface -> canonical` alias map, so there is exactly one stemmer in the
 *     system and it runs at build time.
 *
 *  3. The UI. A sidebar search box (injected here, so a no-JS page carries no
 *     dead control — the established shell rule), an as-you-type dropdown built
 *     as an ARIA combobox, and the full results renderer on `search.html`.
 *
 * Result URLs are computed page-relatively from this script's own `src`, so a
 * page at any depth links correctly, on any transport.
 */
(() => {
  "use strict";

  // ── Engine constants — MIRROR rust/ubc_search/src/score.rs ───────────────
  // Keep this block and the Rust one in lockstep; a reviewer should be able to
  // read them side by side.
  const SCORE_NEED_FIELD = 20; // title-field hit on a need record
  const SCORE_TITLE = 15; // title-field hit on a page/section record
  const SCORE_BODY = 5; // body hit
  const SCORE_NEED_KIND_BONUS = 5; // added once, to a need record
  const SCORE_INDEX_ENTRY = 100; // a full-length index-entry match
  const INDEX_ENTRY_RANK = 3; // its tie-break rank, one past the last record kind
  const MAX_PREFIX_TERMS = 256; // cap on one term's prefix expansion

  // ── Tokenizer constants — MIRROR rust/ubc_search/src/tokenize.rs ─────────
  const MIN_TOKEN_CHARS = 2;
  const MAX_TOKEN_CHARS = 64;
  // biome-ignore format: the packed rows are the point — this list is diffed
  // against `STOPWORDS` in tokenize.rs, and one word per line would turn a
  // 14-line block a reviewer can eyeball into 127 lines nobody reads.
  const STOPWORDS = new Set([
    "a", "about", "above", "after", "again", "against", "all", "am", "an",
    "and", "any", "are", "as", "at", "be", "because", "been", "before",
    "being", "below", "between", "both", "but", "by", "can", "did", "do",
    "does", "doing", "don", "down", "during", "each", "few", "for", "from",
    "further", "had", "has", "have", "having", "he", "her", "here", "hers",
    "herself", "him", "himself", "his", "how", "i", "if", "in", "into", "is",
    "it", "its", "itself", "just", "me", "more", "most", "my", "myself", "no",
    "nor", "not", "now", "of", "off", "on", "once", "only", "or", "other",
    "our", "ours", "ourselves", "out", "over", "own", "s", "same", "she",
    "should", "so", "some", "such", "t", "than", "that", "the", "their",
    "theirs", "them", "themselves", "then", "there", "these", "they", "this",
    "those", "through", "to", "too", "under", "until", "up", "very", "was",
    "we", "were", "what", "when", "where", "which", "while", "who", "whom",
    "why", "will", "with", "you", "your", "yours", "yourself", "yourselves",
  ]);

  // ── UI constants ────────────────────────────────────────────────────────
  const DEBOUNCE_MS = 150; // a local index can be more responsive than the network-era 250-300
  const ANNOUNCE_MS = 1000; // the aria-live announcer's own, slower debounce
  const DROPDOWN_GROUPS = 8; // page groups shown before "N more results"
  const DROPDOWN_PER_GROUP = 4;
  const PAGE_RESULTS = 200; // how many results the results page RENDERS (it counts them all)
  // The engine's own limit argument is a rendering cap, never a counting one:
  // the UI asks for everything and truncates at the last moment, so "N more
  // results" and the results-page count line report true totals.
  const NO_LIMIT = Number.MAX_SAFE_INTEGER;
  // The payload's `k` values — `RecordKind` (record.rs) on the wire. All three
  // are named even though nothing branches on the middle one, so a reader of a
  // payload does not have to infer what a `k` of 1 means.
  const KIND_PAGE = 0;
  // biome-ignore lint/correctness/noUnusedVariables: it documents the wire format
  const KIND_SECTION = 1;
  const KIND_NEED = 2;

  // ── State ───────────────────────────────────────────────────────────────
  /** The loaded index payload, or null until `setIndex` runs. */
  let index = null;
  /** Sorted union of every term key and alias surface form, built on demand. */
  let prefixKeys = null;
  /** Callbacks waiting for the index to arrive. */
  let waiting = [];
  let injected = false;
  /** Active facet filters on the results page: {ty: Set, st: Set}. */
  const facets = { ty: new Set(), st: new Set() };

  /**
   * The page-relative prefix to the site root, derived from this script's own
   * relative `src` (`../_static/ubc-search.js` -> `../`). Never an absolute
   * URL: `file://` has no origin to be absolute against, and a site copied to a
   * sub-path must keep working.
   */
  const rootPrefix = (() => {
    const own =
      document.currentScript ||
      document.querySelector('script[src$="_static/ubc-search.js"]');
    const src = own ? own.getAttribute("src") || "" : "";
    const marker = "_static/ubc-search.js";
    return src.endsWith(marker) ? src.slice(0, src.length - marker.length) : "";
  })();

  // ── Transport ───────────────────────────────────────────────────────────

  const api = window.ubcSearch || (window.ubcSearch = {});
  api.setIndex = (payload) => {
    index = payload && payload.v === 2 ? payload : null;
    prefixKeys = null;
    const pending = waiting;
    waiting = [];
    for (const callback of pending) {
      callback();
    }
  };

  /** Load the index (once), then run `callback`. */
  const ensureIndex = (callback) => {
    if (index) {
      callback();
      return;
    }
    waiting.push(callback);
    if (injected) {
      return;
    }
    injected = true;
    const script = document.createElement("script");
    script.src = `${rootPrefix}_static/ubc-search-index.js`;
    script.addEventListener("error", () => {
      // A missing/unreadable payload must degrade to "no results", never to a
      // hung spinner: run every waiter with the index still null.
      api.setIndex(null);
    });
    document.head.appendChild(script);
  };

  // ── Tokenizer (mirrors tokenize.rs; NO stemming lives here) ─────────────

  // Each predicate is the EXACT JS spelling of the Rust `char` method the
  // indexer uses. `\p{Alphabetic}` (not `\p{L}`) mirrors `char::is_alphabetic`,
  // whose Unicode Alphabetic property also covers the combining marks that
  // carry the vowels of Devanagari, Arabic, Hebrew and Thai — with `\p{L}` the
  // client broke those words where the indexer did not, and every such query
  // silently lost a term.
  const isTokenChar = (ch) =>
    /[\p{Alphabetic}\p{N}]/u.test(ch) || ch === "-" || ch === "_" || ch === ".";
  const isUpper = (ch) => /\p{Uppercase}/u.test(ch); // char::is_uppercase
  const isLower = (ch) => /\p{Lowercase}/u.test(ch); // char::is_lowercase
  const isDigit = (ch) => /\p{N}/u.test(ch); // char::is_numeric
  const isLetter = (ch) => /\p{Alphabetic}/u.test(ch); // char::is_alphabetic

  // char::is_whitespace — the Unicode White_Space property, which JS's `\s`
  // gets wrong at exactly two code points, in opposite directions: `\s` omits
  // U+0085 NEL and includes U+FEFF (ZWNBSP), which is not White_Space. Both
  // survive a paste into the search box, and whether they split a word decides
  // which terms the query requires — so `\s` alone made the two engines answer
  // the same pasted query differently.
  const isSpace = (ch) => (/\s/.test(ch) && ch !== "\uFEFF") || ch === "\u0085";

  /**
   * Trim `isSpace` characters from both ends — the mirror of Rust's
   * `str::trim` (`char::is_whitespace`). `String.prototype.trim` is NOT that
   * mirror: ECMAScript trims U+FEFF (which Rust keeps) and keeps U+0085
   * (which Rust trims), so the two engines computed a different `exact`
   * string for the need-id lookup when a paste carried either character at
   * the edge.
   */
  const trimSpace = (text) => {
    const chars = [...text];
    let start = 0;
    let end = chars.length;
    while (start < end && isSpace(chars[start])) {
      start += 1;
    }
    while (end > start && isSpace(chars[end - 1])) {
      end -= 1;
    }
    return chars.slice(start, end).join("");
  };

  const isIndexable = (token) => {
    const length = Array.from(token).length;
    return (
      length >= MIN_TOKEN_CHARS && length <= MAX_TOKEN_CHARS && !STOPWORDS.has(token)
    );
  };

  /** Split one separator-free segment on case changes and letter/digit edges. */
  const splitCaseAndDigits = (segment, out) => {
    const chars = Array.from(segment);
    if (chars.length === 0) {
      return;
    }
    let start = 0;
    for (let i = 1; i < chars.length; i += 1) {
      const prev = chars[i - 1];
      const cur = chars[i];
      const acronymTail = isUpper(prev) && isLower(cur) && i - 1 > start;
      const wordStart = !isUpper(prev) && isUpper(cur);
      const digitEdge =
        (isDigit(prev) && isLetter(cur)) || (isLetter(prev) && isDigit(cur));
      if (acronymTail) {
        out.push(chars.slice(start, i - 1).join(""));
        start = i - 1;
      } else if (wordStart || digitEdge) {
        out.push(chars.slice(start, i).join(""));
        start = i;
      }
    }
    out.push(chars.slice(start).join(""));
  };

  /** Call `f` with every chunk of `text` (a maximal token-character run, with
   * identifier separators trimmed off both ends); empty chunks are skipped. */
  const forEachChunk = (text, f) => {
    let chunk = "";
    const flush = () => {
      const trimmed = chunk.replace(/^[-_.]+/, "").replace(/[-_.]+$/, "");
      if (trimmed !== "") {
        f(trimmed);
      }
      chunk = "";
    };
    for (const ch of text) {
      if (isTokenChar(ch)) {
        chunk += ch;
      } else if (chunk !== "") {
        flush();
      }
    }
    if (chunk !== "") {
      flush();
    }
  };

  /** Emit one chunk's tokens: the whole form, then its identifier parts.
   * `chunk` is already separator-trimmed and non-empty. */
  const emitChunk = (chunk, out) => {
    const whole = chunk.toLowerCase();
    if (isIndexable(whole)) {
      out.push(whole);
    }
    if (/^[0-9.-]+$/.test(chunk)) {
      return; // version/date-like chunks are atomic
    }
    const parts = [];
    for (const segment of chunk.split(/[-_.]/)) {
      if (segment !== "") {
        splitCaseAndDigits(segment, parts);
      }
    }
    if (parts.length <= 1) {
      return;
    }
    for (const part of parts) {
      const lower = part.toLowerCase();
      if (lower !== whole && isIndexable(lower)) {
        out.push(lower);
      }
    }
  };

  /** Split text into filtered, lowercased surface tokens. */
  const splitSurfaceTokens = (text) => {
    const out = [];
    forEachChunk(text, (chunk) => emitChunk(chunk, out));
    return out;
  };

  /** Mirrors `tokenize.rs::is_identifier_separator`. */
  const isIdentifierSeparator = (ch) => ch === "-" || ch === "_" || ch === ".";

  /**
   * The explicit prefix-intent reading of one query word, if it has one.
   * Mirrors `tokenize.rs::prefix_intent`.
   *
   * A word ENDING in an identifier separator (`T_`, `REQ-`) spells out
   * "everything that continues like this". Edge-trimming cannot honour it —
   * no edge-trimmed index key ends in a separator, and trimming discards the
   * one character carrying the word's meaning (`T_` → `t` then dies in the
   * single-character filter and silently vanishes). Such a word resolves as
   * ONE term — its lowercased surface, leading separators trimmed, trailing
   * ones kept — which `resolveTerm` completes by prefix alone (exact and
   * alias miss by construction). Only a word that is entirely token
   * characters qualifies (`foo/bar_` and MULTI-WORD quoted spans keep the
   * ordinary reading; a single-word quoted span is just a word), the kept
   * form must fit the token length bounds, and the index filters are NOT
   * applied: `t_` is deliberate in a way `t` is not. Two guards bound the
   * blast radius: the caller applies this only when ordinary tokenization
   * yields nothing, and `runQuery` drops the term again if it completes to
   * nothing — so a query changes only when a previously-ignored word now
   * really completes to something.
   */
  const prefixIntent = (word) => {
    if (word === "") {
      return null;
    }
    let last = "";
    for (const ch of word) {
      if (!isTokenChar(ch)) {
        return null;
      }
      last = ch;
    }
    if (!isIdentifierSeparator(last)) {
      return null;
    }
    let kept = word;
    while (kept !== "" && isIdentifierSeparator(kept[0])) {
      kept = kept.slice(1);
    }
    if (kept === "") {
      return null; // separators only: nothing to complete
    }
    // A digits-and-separators word (`9.`, `2.`) is a pasted numbered-list
    // item, not an id prefix — it would complete against changelog version
    // tokens and noisily narrow the rest of the query. Mirrors
    // tokenize.rs::prefix_intent.
    if (/^[0-9._-]+$/.test(kept)) {
      return null;
    }
    const len = [...kept].length;
    if (len < MIN_TOKEN_CHARS || len > MAX_TOKEN_CHARS) {
      return null;
    }
    return kept.toLowerCase();
  };

  /**
   * Whether `word` contains no chunk at all — no run of token characters
   * anywhere in it (`!!!`, `—`). Mirrors `tokenize.rs::has_no_token_chunk`.
   *
   * This is where the vanished-word rule draws its line. A word that produced
   * chunks but no tokens was eaten by this index's own filters (the stopword
   * list, or the length bounds that drop single characters and 65-character
   * runs) — and a result may perfectly well contain `the`, `3` or `C++`; the
   * index just does not key on them, so the word is dropped and the rest of the
   * query is answered. A word with no chunk at all carries nothing to search
   * for at any tier, and the query is made unsatisfiable rather than answering
   * one the reader did not type.
   */
  const hasNoTokenChunk = (word) => {
    let any = false;
    forEachChunk(word, () => {
      any = true;
    });
    return !any;
  };

  // ── Query parsing (mirrors score.rs::parse_query) ────────────────────────

  const parseQuery = (raw) => {
    const required = [];
    const excluded = [];
    let unsatisfiable = false;
    let buffer = "";
    let negate = false;
    let inQuotes = false;
    let pendingNegate = false;

    const flush = () => {
      if (buffer === "") {
        return;
      }
      let tokens = splitSurfaceTokens(buffer);
      if (tokens.length === 0) {
        const intent = prefixIntent(buffer);
        if (intent !== null) {
          // A trailing-separator word the filters ate whole is explicit
          // prefix intent (`prefixIntent`): one term, completed by prefix
          // alone (`T_` -> `t` -> dropped, now `t_`). GATED on the ordinary
          // reading yielding nothing — a pasted sentence-final period
          // (`requirements.`) or hyphenation fragment (`require-`) keeps
          // its ordinary tokens — and `runQuery` drops the term again if
          // it completes to nothing, so `9. tutorial` still answers
          // `tutorial`.
          tokens = [intent];
        } else if (!negate && hasNoTokenChunk(buffer)) {
          // The vanished-word rule (score.rs::parse_query): a REQUIRED word
          // with no searchable content at all makes the query unsatisfiable
          // instead of silently disappearing. A word the index merely
          // filters out is dropped. Excluded words are exempt — an
          // exclusion that matches nothing removes nothing.
          unsatisfiable = true;
        }
      }
      const target = negate ? excluded : required;
      for (const token of tokens) {
        if (!target.includes(token)) {
          target.push(token);
        }
      }
      buffer = "";
    };

    for (const ch of raw) {
      if (ch === '"') {
        flush();
        if (inQuotes) {
          negate = false;
          inQuotes = false;
        } else {
          negate = pendingNegate;
          pendingNegate = false;
          inQuotes = true;
        }
      } else if (isSpace(ch) && !inQuotes) {
        flush();
        negate = false;
        pendingNegate = false;
      } else if (ch === "-" && buffer === "" && !inQuotes && !negate) {
        negate = true;
        pendingNegate = true;
      } else {
        buffer += ch;
      }
    }
    flush();

    return {
      required: required.filter((t) => !excluded.includes(t)),
      excluded,
      exact: trimSpace(raw).toLowerCase(),
      unsatisfiable,
    };
  };

  // ── Term resolution (mirrors score.rs::resolve_term) ─────────────────────

  /**
   * Read `key` from one of the payload's maps.
   *
   * The maps are plain object literals from the JSON payload, so they inherit
   * `Object.prototype`: a bare `map[key]` answers a truthy FUNCTION for the
   * everyday English words `constructor`, `toString`, `valueOf` and
   * `hasOwnProperty`, and the caller then iterates a function. Every lookup
   * into `terms` / `titleterms` / `alias` / `ids` goes through here, so a
   * reader searching for "constructor" gets an ordinary (empty) answer instead
   * of an exception that kills the whole search UI. The Rust reference scorer
   * uses `BTreeMap`s, which have no such inherited keys — this helper is what
   * keeps the two engines answering the same thing.
   */
  // `Object.hasOwn` says this in one call, but it is ES2022 and would raise this
  // file's browser floor from 2018 (where its `\p{…}` escapes put it): a built
  // site is opened from ZIPs and off air-gapped machines, so the floor stays.
  // biome-ignore lint/suspicious/noPrototypeBuiltins: Object.hasOwn is ES2022
  const hasOwn = (object, key) => Object.prototype.hasOwnProperty.call(object, key);

  const lookup = (map, key) => (map && hasOwn(map, key) ? map[key] : undefined);

  /** The sorted key array the prefix step binary-searches. Built once. */
  const keysForPrefix = () => {
    if (prefixKeys) {
      return prefixKeys;
    }
    const seen = new Set();
    for (const key of Object.keys(index.terms)) {
      seen.add(key);
    }
    for (const key of Object.keys(index.titleterms)) {
      seen.add(key);
    }
    for (const key of Object.keys(index.alias)) {
      seen.add(key);
    }
    prefixKeys = Array.from(seen).sort(compareCodePoints);
    return prefixKeys;
  };

  /**
   * Compare two strings by Unicode CODE POINT — the order Rust's `str` `Ord`
   * gives (UTF-8 byte order ≡ code-point order). JS default string comparison
   * is UTF-16 code-UNIT order, which sorts astral-plane characters BEFORE
   * U+E000..U+FFFF; at the MAX_PREFIX_TERMS truncation boundary that made the
   * two engines keep DIFFERENT keys. Every key ordering here uses this.
   */
  const compareCodePoints = (a, b) => {
    let i = 0;
    let j = 0;
    while (i < a.length && j < b.length) {
      const ca = a.codePointAt(i);
      const cb = b.codePointAt(j);
      if (ca !== cb) {
        return ca < cb ? -1 : 1;
      }
      i += ca > 0xffff ? 2 : 1;
      j += cb > 0xffff ? 2 : 1;
    }
    return a.length - i - (b.length - j);
  };

  /** The first index in `keys` at or after `term` (binary search). */
  const lowerBound = (keys, term) => {
    let low = 0;
    let high = keys.length;
    while (low < high) {
      const mid = (low + high) >> 1;
      if (compareCodePoints(keys[mid], term) < 0) {
        low = mid + 1;
      } else {
        high = mid;
      }
    }
    return low;
  };

  /** A posting is a bare record index, or `[record, weight]`. */
  const postingRecord = (posting) =>
    typeof posting === "number" ? posting : posting[0];

  /**
   * Record every posting under `key`, keeping the STRONGEST resolution per
   * record (an exact hit beats a prefix hit) — mirrors `score.rs::insert_all`.
   */
  const collectPostings = (map, key, prefixOnly, into) => {
    const postings = lookup(map, key);
    if (!postings) {
      return;
    }
    for (const posting of postings) {
      const record = postingRecord(posting);
      if (into.has(record)) {
        into.set(record, into.get(record) && prefixOnly);
      } else {
        into.set(record, prefixOnly);
      }
    }
  };

  /**
   * Resolve one query term: the UNION of exact, alias and prefix — never the
   * first step that happened to match.
   *
   * Stopping at the first match makes a term that is ALSO a whole corpus token
   * un-completable, and under AND semantics that costs the reader the whole
   * result: typing `needs_string_links` one character at a time, `needs_st`
   * and `needs_str` answered nothing (their `st` / `str` are literal tokens of
   * a code sample, so the exact hit suppressed the prefix expansion and the
   * intersection with `needs` emptied) while `needs_s` and `needs_stri`
   * answered normally. Union costs no precision: `collectPostings` keeps the
   * STRONGEST resolution per record, so an exactly-matched record still scores
   * full points and outranks the half-scored prefix completions. A record
   * matched exactly in BODY text may also prefix-match one of its title
   * fields, which promotes it from family 2 to family 1 — the family rules
   * applied consistently; measured upward-only on a real corpus.
   */
  const resolveTerm = (term) => {
    const match = { body: new Map(), title: new Map() };
    const collect = (key, prefixOnly) => {
      collectPostings(index.terms, key, prefixOnly, match.body);
      collectPostings(index.titleterms, key, prefixOnly, match.title);
    };

    collect(term, false);
    const canonical = lookup(index.alias, term);
    if (canonical) {
      collect(canonical, false);
    }
    // The prefix group is the CONTIGUOUS run of keys starting at `term`, found
    // by binary search — never an O(vocab) scan per keystroke. Gather, resolve
    // surfaces to their canonical term, then sort/cap: the same order as the
    // Rust reference, so the truncation boundary matches too.
    const keys = keysForPrefix();
    const expanded = new Set();
    for (let i = lowerBound(keys, term); i < keys.length; i += 1) {
      const key = keys[i];
      if (!key.startsWith(term)) {
        break;
      }
      expanded.add(lookup(index.alias, key) || key);
    }
    for (const key of Array.from(expanded)
      .sort(compareCodePoints)
      .slice(0, MAX_PREFIX_TERMS)) {
      collect(key, true);
    }
    return match;
  };

  // ── Scoring (mirrors score.rs::search_parsed) ────────────────────────────

  /**
   * A hit is either a RECORD hit (`{record, family, score}`) or an INDEX-ENTRY
   * hit (`{record: -1, entry, doc, anchor, family, score}`) — the two arms of
   * `HitTarget` in score.rs. The `-1` is the same "absent index" convention the
   * payload's `p` field uses.
   */
  const isIndexHit = (hit) => hit.record < 0;

  const kindRank = (record) => {
    if (record.k === KIND_NEED) {
      return 0;
    }
    return record.k === KIND_PAGE ? 1 : 2;
  };

  /** The tie-break rank of a hit's kind (an index entry ranks after records). */
  const hitKindRank = (hit) =>
    isIndexHit(hit) ? INDEX_ENTRY_RANK : kindRank(index.records[hit.record]);

  /** The site-root-relative html path of the record at `recordIndex`. */
  const recordPath = (recordIndex) => {
    const record = index.records[recordIndex];
    const doc = record ? index.docs[record.d] : null;
    return doc ? doc.path : "";
  };

  /** The site-root-relative html path of a hit's destination. */
  const hitPath = (hit) => {
    if (!isIndexHit(hit)) {
      return recordPath(hit.record);
    }
    const doc = index.docs[hit.doc];
    return doc ? doc.path : "";
  };

  /** The in-page anchor of a hit's destination (`""` when it has none). */
  const hitAnchor = (hit) =>
    isIndexHit(hit) ? hit.anchor || "" : index.records[hit.record].a || "";

  /** The entry text of an index-entry hit; `""` for a record hit. */
  const hitEntry = (hit) => (isIndexHit(hit) ? hit.entry : "");

  const runQuery = (raw, limit) => {
    if (!index) {
      return [];
    }
    const query = parseQuery(raw);
    const hits = [];

    const excluded = new Set();
    for (const term of query.excluded) {
      const match = resolveTerm(term);
      for (const record of match.body.keys()) {
        excluded.add(record);
      }
      for (const record of match.title.keys()) {
        excluded.add(record);
      }
    }

    // Family 0: the exact need-id path. A miss contributes NOTHING — it never
    // degrades into a prefix search over ids.
    const exactFound = lookup(index.ids, query.exact);
    const exact = exactFound === undefined ? null : exactFound;
    if (exact !== null && !excluded.has(exact)) {
      hits.push({
        record: exact,
        family: 0,
        score: SCORE_NEED_FIELD + SCORE_NEED_KIND_BONUS,
      });
    }

    // A required word carried nothing this index could ever key on: the
    // term-matching families are skipped, because pretending the word was never
    // typed is the AND-semantics violation the vanished-word rule exists to
    // prevent. Family 0 above is NOT skipped — it is a lookup of the whole
    // query string against the id map, so a hit there is a real hit.
    if (!query.unsatisfiable && query.required.length > 0) {
      // record -> {score, title, terms}
      const acc = new Map();
      // Terms that actually participate in the AND (the fallback below).
      let requiredCount = 0;
      for (const term of query.required) {
        const match = resolveTerm(term);
        // The prefix-intent fallback (score.rs::search_parsed): a
        // prefix-intent term — the only shape ending in a separator — that
        // completed to NOTHING is dropped, exactly as its word was dropped
        // before the carve-out existed. Without this, pasted numbered-list
        // prose (`9. tutorial`) would zero a query that used to answer.
        if (
          match.body.size === 0 &&
          match.title.size === 0 &&
          isIdentifierSeparator(term.slice(-1))
        ) {
          continue;
        }
        requiredCount += 1;
        const touched = new Map();
        for (const [record, prefixOnly] of match.title) {
          const base =
            index.records[record].k === KIND_NEED ? SCORE_NEED_FIELD : SCORE_TITLE;
          const points = prefixOnly ? Math.floor(base / 2) : base;
          const slot = touched.get(record) || { score: 0, title: false };
          slot.score += points;
          slot.title = true;
          touched.set(record, slot);
        }
        for (const [record, prefixOnly] of match.body) {
          const points = prefixOnly ? Math.floor(SCORE_BODY / 2) : SCORE_BODY;
          const slot = touched.get(record) || { score: 0, title: false };
          slot.score += points;
          touched.set(record, slot);
        }
        for (const [record, slot] of touched) {
          const total = acc.get(record) || { score: 0, title: false, terms: 0 };
          total.score += slot.score;
          total.title = total.title || slot.title;
          total.terms += 1;
          acc.set(record, total);
        }
      }
      for (const [record, total] of acc) {
        if (total.terms !== requiredCount || excluded.has(record)) {
          continue; // AND semantics: every term must match
        }
        if (record === exact) {
          continue; // already carried by family 0
        }
        const bonus = index.records[record].k === KIND_NEED ? SCORE_NEED_KIND_BONUS : 0;
        hits.push({
          record,
          family: total.title ? 1 : 2,
          score: total.score + bonus,
        });
      }
    }

    // Families 1 and 3: the index-entry channel (Sphinx `searchtools.js`).
    // The whole lowercased query must be a SUBSTRING of the whole entry, gated
    // by `queryLen >= entryLen / 2` and scored `round(100 * qLen / eLen)`; a
    // main entry ranks with the ordinary results, a non-main one after all of
    // them. Neither the exclusion set nor the unsatisfiable guard applies —
    // upstream's index pass consults neither, and the match is on the raw query
    // string rather than on terms. See score.rs's family table.
    const entries = index.indexentries || {};
    if (query.exact.length > 0) {
      for (const entry of Object.keys(entries)) {
        if (query.exact.length * 2 < entry.length || !entry.includes(query.exact)) {
          continue;
        }
        const score = Math.round(
          (SCORE_INDEX_ENTRY * query.exact.length) / entry.length,
        );
        for (const row of entries[entry]) {
          hits.push({
            record: -1,
            entry,
            doc: row[0],
            anchor: row[1],
            family: row[2] ? 1 : 3,
            score,
          });
        }
      }
    }

    // The tie-break cascade — a TOTAL order, so no sort-stability assumption.
    hits.sort((a, b) => {
      if (a.family !== b.family) {
        return a.family - b.family;
      }
      if (a.score !== b.score) {
        return b.score - a.score;
      }
      const ka = hitKindRank(a);
      const kb = hitKindRank(b);
      if (ka !== kb) {
        return ka - kb;
      }
      const pa = hitPath(a);
      const pb = hitPath(b);
      if (pa !== pb) {
        return pa < pb ? -1 : 1;
      }
      const aa = hitAnchor(a);
      const ab = hitAnchor(b);
      if (aa !== ab) {
        return aa < ab ? -1 : 1;
      }
      // Only index entries reach this step: a `pair:` entry files both halves
      // at ONE anchor, so path and anchor alone do not order them. DEFENSIVE on
      // both sides of the mirror: the payload's `indexentries` keys are emitted
      // in sorted order, so removing this step changes no current output — it is
      // what keeps the cascade a total order independently of that.
      const ea = hitEntry(a);
      const eb = hitEntry(b);
      if (ea === eb) {
        return 0;
      }
      return ea < eb ? -1 : 1;
    });
    return hits.slice(0, limit);
  };

  // ── Rendering helpers ───────────────────────────────────────────────────

  const escapeHtml = (text) =>
    String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");

  /** The page-relative href of a hit's destination. */
  const hitHref = (hit) => {
    const anchor = hitAnchor(hit);
    return rootPrefix + hitPath(hit) + (anchor ? `#${anchor}` : "");
  };

  /**
   * Wrap each query token's occurrences in `text` in a `<mark>`.
   *
   * ONE pass over the RAW text, escaping each segment as it is emitted: a
   * per-token `replace` over already-escaped HTML would rewrite its own output
   * — a query token of `mark`, `class`, `amp` or `lt` matches inside the
   * `<mark …>` wrappers and inside the `&amp;`/`&lt;` entities an earlier step
   * produced, and the result is garbled markup. Nothing from `text` or from a
   * token ever reaches the output unescaped, so this stays inert.
   */
  const highlight = (text, tokens) => {
    const source = String(text);
    // Longest first: alternation is leftmost-first, so `needs` must be tried
    // before `need` at the same position.
    const patterns = tokens
      .filter((token) => token.length >= MIN_TOKEN_CHARS)
      .slice()
      .sort((a, b) => b.length - a.length)
      .map((token) => token.replace(/[.*+?^${}()|[\]\\-]/g, "\\$&"));
    if (patterns.length === 0) {
      return escapeHtml(source);
    }
    const re = new RegExp(`(${patterns.join("|")})`, "gi");
    let out = "";
    let last = 0;
    let match = re.exec(source);
    while (match !== null) {
      if (match[0] === "") {
        re.lastIndex += 1; // an empty match would loop forever
      } else {
        out += escapeHtml(source.slice(last, match.index));
        out += `<mark class="ub-search-mark">${escapeHtml(match[0])}</mark>`;
        last = match.index + match[0].length;
      }
      match = re.exec(source);
    }
    return out + escapeHtml(source.slice(last));
  };

  /** One result row's inner HTML. */
  const renderResult = (hit, tokens) => {
    const parts = [];
    parts.push(`<a class="ub-search-hit" href="${escapeHtml(hitHref(hit))}">`);
    parts.push('<span class="ub-search-hit-head">');
    // An index-entry hit has no record behind it: no excerpt, no breadcrumb and
    // no facets. Its TITLE is the entry that matched — upstream shows the page
    // title instead, which repeats the group heading this row already sits
    // under and tells the reader nothing about why the row is here.
    if (isIndexHit(hit)) {
      parts.push('<span class="ub-search-badge">index</span>');
      parts.push(
        `<span class="ub-search-title">${highlight(hit.entry, tokens)}</span>`,
      );
      parts.push("</span></a>");
      return parts.join("");
    }
    const record = index.records[hit.record];
    if (record.k === KIND_NEED) {
      const badge = [record.ty, record.st].filter(Boolean).join(" · ");
      parts.push(`<span class="ub-search-badge">${escapeHtml(badge || "need")}</span>`);
      if (record.id) {
        parts.push(`<span class="ub-search-id">${escapeHtml(record.id)}</span>`);
      }
    }
    parts.push(`<span class="ub-search-title">${highlight(record.t, tokens)}</span>`);
    parts.push("</span>");
    if (record.h && record.h.length > 1) {
      parts.push(
        `<span class="ub-search-crumb">${escapeHtml(record.h.slice(1).join(" › "))}</span>`,
      );
    }
    if (record.x) {
      parts.push(
        `<span class="ub-search-excerpt">${highlight(record.x, tokens)}</span>`,
      );
    }
    parts.push("</a>");
    return parts.join("");
  };

  /** Group hits by page, preserving each group's best rank. */
  const groupByPage = (hits) => {
    const groups = [];
    const byDoc = new Map();
    for (const hit of hits) {
      const doc = isIndexHit(hit) ? hit.doc : index.records[hit.record].d;
      let group = byDoc.get(doc);
      if (!group) {
        group = { doc, hits: [] };
        byDoc.set(doc, group);
        groups.push(group);
      }
      group.hits.push(hit);
    }
    return groups;
  };

  const renderGroups = (groups, tokens, perGroup) => {
    const parts = [];
    for (const group of groups) {
      const doc = index.docs[group.doc];
      parts.push('<section class="ub-search-group">');
      parts.push(
        `<h2 class="ub-search-group-title">${escapeHtml(doc ? doc.title : "")}</h2>`,
      );
      parts.push('<ul class="ub-search-list">');
      const shown = perGroup ? group.hits.slice(0, perGroup) : group.hits;
      for (const hit of shown) {
        parts.push(`<li class="ub-search-item">${renderResult(hit, tokens)}</li>`);
      }
      parts.push("</ul>");
      if (perGroup && group.hits.length > perGroup) {
        parts.push(
          `<p class="ub-search-more">${group.hits.length - perGroup} more on this page</p>`,
        );
      }
      parts.push("</section>");
    }
    return parts.join("");
  };

  // ── Facets (results page only) ──────────────────────────────────────────

  /**
   * `passesFacets`, ignoring the facet `exceptKey`.
   *
   * The chip list for one facet is scoped to the hits every OTHER facet
   * allows: with a type selected, the type row must keep listing the sibling
   * types (OR within a facet stays reachable) while the status selection
   * still narrows it.
   */
  const passesFacetsExcept = (hit, exceptKey) => {
    // An index-entry hit carries no type and no status, so — exactly as for a
    // non-need record — any active facet excludes it.
    const record = isIndexHit(hit) ? null : index.records[hit.record];
    for (const key of ["ty", "st"]) {
      if (key === exceptKey) {
        continue;
      }
      const selected = facets[key];
      if (selected.size === 0) {
        continue; // an unused facet filters nothing
      }
      // OR within a facet, AND across facets. A non-need record has no value
      // for either key, so any active facet excludes it.
      if (!record || !record[key] || !selected.has(record[key])) {
        return false;
      }
    }
    return true;
  };

  const passesFacets = (hit) => passesFacetsExcept(hit, "");

  // ── UI: the sidebar box ─────────────────────────────────────────────────

  const searchPageHref = () => `${rootPrefix}search.html`;

  /** Build one search form (the sidebar box, or the results page's own). */
  const buildForm = (idSuffix) => {
    const form = document.createElement("form");
    form.className = "ub-search-form";
    form.setAttribute("role", "search");
    form.action = searchPageHref();
    form.method = "get";

    const input = document.createElement("input");
    input.type = "search";
    input.name = "q";
    input.className = "ub-search-input";
    input.id = `ub-search-input${idSuffix}`;
    input.placeholder = "Search";
    input.setAttribute("aria-label", "Search this site");
    input.setAttribute("autocomplete", "off");
    input.setAttribute("role", "combobox");
    input.setAttribute("aria-expanded", "false");
    input.setAttribute("aria-autocomplete", "list");
    input.setAttribute("aria-controls", `ub-search-listbox${idSuffix}`);

    const listbox = document.createElement("ul");
    listbox.className = "ub-search-dropdown";
    listbox.id = `ub-search-listbox${idSuffix}`;
    listbox.setAttribute("role", "listbox");
    listbox.setAttribute("aria-label", "Search results");
    listbox.hidden = true;

    form.appendChild(input);
    form.appendChild(listbox);
    return { form, input, listbox };
  };

  /** The single polite announcer element (created once, text replaced). */
  const announcer = (() => {
    let node = null;
    let timer = null;
    return (message) => {
      if (!node) {
        node = document.createElement("div");
        node.className = "ub-search-announce";
        node.setAttribute("aria-live", "polite");
        node.setAttribute("role", "status");
        document.body.appendChild(node);
      }
      window.clearTimeout(timer);
      timer = window.setTimeout(() => {
        node.textContent = message;
      }, ANNOUNCE_MS);
    };
  })();

  /**
   * The default submit action: open the results page for `raw`.
   *
   * The navigation is done here rather than left to the form's own GET, because
   * a form submission on a `file://` page is not reliably supported — and a
   * built site must behave the same on both transports.
   */
  const navigateToResults = (raw) => {
    if (raw !== "") {
      window.location.href = `${searchPageHref()}?q=${encodeURIComponent(raw)}`;
    }
  };

  /**
   * Wire one form's combobox behaviour.
   *
   * `onSubmit` is the ONE thing that happens when the reader presses Enter with
   * nothing highlighted. It is a parameter rather than a fixed navigation
   * because the results page re-queries in place: a second listener on the same
   * form cannot cancel this one's navigation, so both ran and the in-place
   * render was immediately replaced by a full document load — re-downloading
   * the whole index and silently clearing the facet selection.
   */
  const wireCombobox = ({ input, listbox }, onSubmit = navigateToResults) => {
    let options = [];
    let active = -1;
    let timer = null;
    // Bumped by every `close`; a scheduled render is dropped when its epoch is
    // stale. The debounce timer alone cannot carry this: once it has fired,
    // the render may still be QUEUED behind the index fetch (`ensureIndex`),
    // and from there it would re-open a dropdown the reader already dismissed
    // — by Escape, by blur, or by submitting the query.
    let epoch = 0;

    const close = () => {
      window.clearTimeout(timer);
      epoch += 1;
      listbox.hidden = true;
      listbox.innerHTML = "";
      input.setAttribute("aria-expanded", "false");
      input.removeAttribute("aria-activedescendant");
      options = [];
      active = -1;
    };

    const setActive = (next) => {
      if (options.length === 0) {
        return;
      }
      if (active >= 0 && options[active]) {
        options[active].classList.remove("ub-search-active");
      }
      active = (next + options.length) % options.length;
      const option = options[active];
      option.classList.add("ub-search-active");
      input.setAttribute("aria-activedescendant", option.id);
      if (option.scrollIntoView) {
        option.scrollIntoView({ block: "nearest" });
      }
    };

    const render = () => {
      const raw = input.value.trim();
      if (raw === "") {
        close();
        return;
      }
      // Ask for EVERY hit and truncate at render time: "N more results" has to
      // report how many results there actually are, not how many the dropdown
      // asked the engine for.
      const hits = runQuery(raw, NO_LIMIT);
      const tokens = parseQuery(raw).required;
      const groups = groupByPage(hits).slice(0, DROPDOWN_GROUPS);
      const shown = groups.reduce(
        (total, group) => total + Math.min(group.hits.length, DROPDOWN_PER_GROUP),
        0,
      );
      const parts = [];
      if (hits.length === 0) {
        parts.push('<li class="ub-search-empty">No results</li>');
      } else {
        let optionIndex = 0;
        for (const group of groups) {
          const doc = index.docs[group.doc];
          parts.push(
            `<li class="ub-search-group-label" role="presentation">${escapeHtml(doc ? doc.title : "")}</li>`,
          );
          for (const hit of group.hits.slice(0, DROPDOWN_PER_GROUP)) {
            parts.push(
              `<li class="ub-search-option" role="option" tabindex="-1" id="${input.id}-opt-${optionIndex}" data-href="${escapeHtml(hitHref(hit))}">${renderResult(hit, tokens)}</li>`,
            );
            optionIndex += 1;
          }
        }
        if (hits.length > shown) {
          parts.push(
            `<li class="ub-search-all" role="presentation"><a href="${escapeHtml(`${searchPageHref()}?q=${encodeURIComponent(raw)}`)}">${hits.length - shown} more results</a></li>`,
          );
        }
      }
      listbox.innerHTML = parts.join("");
      listbox.hidden = false;
      input.setAttribute("aria-expanded", "true");
      options = Array.from(listbox.querySelectorAll(".ub-search-option"));
      active = -1;
      input.removeAttribute("aria-activedescendant");
      announcer(hits.length === 1 ? "1 result" : `${hits.length} results`);
    };

    const schedule = () => {
      window.clearTimeout(timer);
      timer = window.setTimeout(() => {
        const scheduled = epoch;
        ensureIndex(() => {
          if (scheduled === epoch) {
            render();
          }
        });
      }, DEBOUNCE_MS);
    };

    input.addEventListener(
      "focus",
      () =>
        ensureIndex(() => {
          // Warming the index on first engagement is the whole effect; there is
          // no query to render yet.
        }),
      { once: true },
    );
    input.form.addEventListener("submit", (event) => {
      event.preventDefault();
      // The suggestions are consumed the moment the query is: on the results
      // page the submit re-renders IN PLACE and the box keeps focus, so
      // without this the dropdown sits open on top of the fresh results (and
      // of the facet strip) until an Escape or a click elsewhere.
      close();
      onSubmit(input.value.trim());
    });
    input.addEventListener("input", schedule);
    input.addEventListener("keydown", (event) => {
      if (event.key === "ArrowDown") {
        event.preventDefault();
        setActive(active + 1);
      } else if (event.key === "ArrowUp") {
        event.preventDefault();
        // From "nothing selected" (`active === -1`) ArrowUp lands on the LAST
        // option: treat no-selection as position 0 and step back from there, so
        // both ends wrap exactly once.
        setActive((active < 0 ? 0 : active) - 1);
      } else if (event.key === "Escape") {
        if (listbox.hidden) {
          input.blur();
        } else {
          close();
        }
      } else if (event.key === "Enter" && active >= 0 && options[active]) {
        event.preventDefault();
        window.location.href = options[active].getAttribute("data-href");
      }
    });
    listbox.addEventListener("mousedown", (event) => {
      const option = event.target.closest
        ? event.target.closest(".ub-search-option")
        : null;
      if (option) {
        event.preventDefault();
        window.location.href = option.getAttribute("data-href");
      }
    });
    input.addEventListener("blur", () => {
      // A click on an option fires `mousedown` before `blur`, so the navigation
      // above has already been taken by the time this runs.
      window.setTimeout(close, 150);
    });
    return { close, render };
  };

  /**
   * Inject the sidebar box, at furo's slot: below the brand, above the nav.
   *
   * Returns the built form UNWIRED: which submit action it gets depends on
   * whether this page is the results page, which `setupResultsPage` decides.
   */
  const injectSidebarBox = () => {
    const sidebar = document.querySelector(".ub-sidebar");
    if (!sidebar) {
      return null;
    }
    const built = buildForm("");
    built.form.classList.add("ub-search-sidebar");
    // The strip's own top border becomes the one separator under the brand
    // (furo's model); the brand's border-bottom yields via this state class,
    // so a no-JS page keeps its separator.
    sidebar.classList.add("ub-has-search");
    const nav = sidebar.querySelector(".ub-nav");
    if (nav) {
      sidebar.insertBefore(built.form, nav);
    } else {
      sidebar.appendChild(built.form);
    }
    return built;
  };

  /** `/` focuses the box, unless the reader is already typing somewhere. */
  const wireSlashShortcut = (input) => {
    if (!input) {
      return;
    }
    document.addEventListener("keydown", (event) => {
      if (event.key !== "/" || event.ctrlKey || event.metaKey || event.altKey) {
        return;
      }
      const path = event.composedPath ? event.composedPath() : null;
      const target = (path && path[0]) || event.target;
      const tag = target && target.tagName ? target.tagName.toLowerCase() : "";
      if (
        tag === "input" ||
        tag === "textarea" ||
        tag === "select" ||
        (target && target.isContentEditable)
      ) {
        return;
      }
      // Below the sidebar breakpoint the box is hidden with
      // `visibility: hidden` (plus an off-canvas transform), which still LAYS
      // IT OUT: it has client rects, so any predicate built on those answers
      // "rendered" while `focus()` is a silent no-op. Swallowing `/` there
      // leaves the reader with no search box and no `/` either.
      //
      // So don't predict focusability — take focus and check whether it landed.
      input.focus();
      if (document.activeElement !== input) {
        return; // not focusable: let the keystroke through
      }
      event.preventDefault();
    });
  };

  // ── UI: the results page ────────────────────────────────────────────────

  /**
   * The `q` parameter of the current URL, or `""`.
   *
   * Two things a shared or hand-edited link does that the obvious version of
   * this function does not survive, and both would throw on the FIRST statement
   * of the results page — leaving a bare heading with no box, no message and no
   * results:
   *
   * - `?q=100%` / `?q=%E0%A4` — an incomplete percent-escape makes
   *   `decodeURIComponent` throw `URIError`; the raw text is searched instead;
   * - `?q=a=b` — the value's own `=` must survive, so the split is on the FIRST
   *   `=` only.
   */
  const queryFromLocation = () => {
    const search = window.location.search || "";
    for (const pair of search.replace(/^\?/, "").split("&")) {
      const split = pair.indexOf("=");
      const key = split === -1 ? pair : pair.slice(0, split);
      if (key !== "q") {
        continue;
      }
      const value = (split === -1 ? "" : pair.slice(split + 1)).replace(/\+/g, " ");
      try {
        return decodeURIComponent(value);
      } catch {
        return value; // undecodable: search what the reader actually sees
      }
    }
    return "";
  };

  /**
   * Wire the results page, when this IS the results page.
   *
   * Returns its in-place re-query — the submit action every box on this page
   * should use — or `null` on an ordinary page.
   */
  const setupResultsPage = (sidebarInput) => {
    const results = document.getElementById("ub-search-results");
    if (!results) {
      return null;
    }
    const countLine = document.getElementById("ub-search-count");
    const facetBox = document.getElementById("ub-search-facets");
    const formHost = document.getElementById("ub-search-page-form");
    let current = queryFromLocation();

    // The results page carries its own (larger) box, so the query is editable
    // without hunting for the sidebar. It is wired below, once `run` exists.
    let pageInput = null;
    let pageForm = null;
    if (formHost) {
      const built = buildForm("-page");
      formHost.replaceWith(built.form);
      built.form.classList.add("ub-search-page-form");
      pageInput = built.input;
      pageForm = built;
    }

    // How many chips a facet shows before folding the rest behind the
    // "+ N more" expander. The expanded state is per-facet and deliberately
    // persists across re-renders and re-queries for the life of the page.
    const FACET_VISIBLE = 10;
    const facetsExpanded = { ty: false, st: false };

    const renderFacets = (base) => {
      if (!facetBox) {
        return;
      }
      // Nothing to filter (idle page, or a query with no hits): no facet UI
      // at all. An active selection persists silently and resurfaces — as
      // selected chips — as soon as a query has hits again; while there are
      // zero base hits it cannot change what is on screen.
      if (base.length === 0) {
        facetBox.innerHTML = "";
        return;
      }
      const parts = [];
      for (const [key, label] of [
        ["ty", "Type"],
        ["st", "Status"],
      ]) {
        const selected = facets[key];
        // Values come from the CURRENT results (own-key excluded, see
        // `passesFacetsExcept`), not the whole corpus: a chip filters what is
        // on screen, so a chip that matches nothing on screen is noise — and
        // on an idle or need-less result set the facet UI disappears
        // entirely rather than offering the site's whole type vocabulary.
        const counts = new Map();
        for (const hit of base) {
          if (!passesFacetsExcept(hit, key)) {
            continue;
          }
          if (isIndexHit(hit)) {
            continue; // an index entry has no facet values to count
          }
          const value = index.records[hit.record][key];
          if (value) {
            counts.set(value, (counts.get(value) || 0) + 1);
          }
        }
        // An ACTIVE value stays listed even at zero: it is still filtering
        // (a facet excludes non-need records wholesale), and hiding it would
        // leave the reader with an invisible, un-removable filter.
        for (const value of selected) {
          if (!counts.has(value)) {
            counts.set(value, 0);
          }
        }
        if (counts.size === 0) {
          continue;
        }
        // One total-order comparator (selected first, then count, then name):
        // a single pass, so nothing here leans on sort stability.
        const values = Array.from(counts.keys()).sort((a, b) => {
          const bySelected = Number(selected.has(b)) - Number(selected.has(a));
          if (bySelected !== 0) {
            return bySelected;
          }
          const byCount = counts.get(b) - counts.get(a);
          if (byCount !== 0) {
            return byCount;
          }
          return a < b ? -1 : a > b ? 1 : 0;
        });
        // Selected chips are never hidden behind the fold: they all sort to
        // the front, and the fold widens past the cap to keep every one of
        // them visible (every selected value is in `counts`, injected above).
        const foldAt = Math.max(FACET_VISIBLE, selected.size);
        const open = facetsExpanded[key];
        const visible = open ? values : values.slice(0, foldAt);
        parts.push(`<fieldset class="ub-search-facet"><legend>${label}</legend>`);
        for (const value of visible) {
          const on = selected.has(value);
          parts.push(
            `<button type="button" class="ub-search-chip${on ? " ub-search-chip-on" : ""}" aria-pressed="${on}" data-facet="${key}" data-value="${escapeHtml(value)}">${escapeHtml(value)} (${counts.get(value)})</button>`,
          );
        }
        if (values.length > foldAt) {
          const more = values.length - foldAt;
          parts.push(
            `<button type="button" class="ub-search-chip ub-search-chip-more" aria-expanded="${open}" data-more="${key}">${open ? "Show fewer" : `+ ${more} more`}</button>`,
          );
        }
        parts.push("</fieldset>");
      }
      facetBox.innerHTML = parts.join("");
    };

    const renderAll = () => {
      // Filter BEFORE truncating, and count before that again: a facet must be
      // able to reach every match, and the count line must say how many results
      // there are — not how many this page chose to render. The facet chips
      // scope to `base` (pre-facet hits): they narrow the query's results,
      // never re-widen them.
      const base = runQuery(current, NO_LIMIT);
      const hits = base.filter(passesFacets);
      const shown = hits.slice(0, PAGE_RESULTS);
      const tokens = parseQuery(current).required;
      if (countLine) {
        if (current === "") {
          countLine.textContent = "Type a query to search this site.";
        } else if (hits.length === 0) {
          countLine.textContent = `No results for “${current}”.`;
        } else {
          const capped =
            hits.length > shown.length ? ` Showing the first ${shown.length}.` : "";
          countLine.textContent = `${hits.length} result${hits.length === 1 ? "" : "s"} for “${current}”.${capped}`;
        }
      }
      results.innerHTML = renderGroups(groupByPage(shown), tokens, 0);
      renderFacets(base);
    };

    if (facetBox) {
      facetBox.addEventListener("click", (event) => {
        const chip = event.target.closest
          ? event.target.closest(".ub-search-chip")
          : null;
        if (!chip) {
          return;
        }
        const moreKey = chip.getAttribute("data-more");
        if (moreKey !== null) {
          if (hasOwn(facetsExpanded, moreKey)) {
            facetsExpanded[moreKey] = !facetsExpanded[moreKey];
            renderAll();
            // Focus the expander's replacement (it re-renders as its
            // "Show fewer" / "+ N more" counterpart) — same rule as below.
            for (const candidate of facetBox.querySelectorAll(".ub-search-chip-more")) {
              if (candidate.getAttribute("data-more") === moreKey) {
                candidate.focus();
                break;
              }
            }
          }
          return;
        }
        const key = chip.getAttribute("data-facet");
        const value = chip.getAttribute("data-value");
        const selected = hasOwn(facets, key) ? facets[key] : null;
        if (!selected) {
          return;
        }
        if (selected.has(value)) {
          selected.delete(value);
        } else {
          selected.add(value);
        }
        renderAll();
        // The re-render replaces the chip row wholesale, which detaches the
        // chip the reader just activated: a keyboard user would land back on
        // `<body>` and have to tab in from the top for every filter. Put focus
        // back on the chip's replacement — and when a DESELECT removed the
        // chip itself (it folded, or a zero-count selected chip vanished),
        // fall back to the nearest surviving chip in the same facet, then to
        // any chip, so focus never silently drops to `<body>`.
        let exact = null;
        let sameFacet = null;
        for (const candidate of facetBox.querySelectorAll(".ub-search-chip")) {
          if (
            candidate.getAttribute("data-facet") === key &&
            candidate.getAttribute("data-value") === value
          ) {
            exact = candidate;
            break;
          }
          if (
            !sameFacet &&
            (candidate.getAttribute("data-facet") === key ||
              candidate.getAttribute("data-more") === key)
          ) {
            sameFacet = candidate;
          }
        }
        const target = exact || sameFacet || facetBox.querySelector(".ub-search-chip");
        if (target) {
          target.focus();
        } else if (pageInput) {
          pageInput.focus(); // the whole facet UI disappeared
        }
      });
    }

    const run = (raw) => {
      current = raw;
      // Both boxes ask the same question, so a submit from either writes the
      // query back to the other: an in-place re-query never reloads the page,
      // and without this the box the reader did NOT use keeps its old text —
      // correct results sitting under a box that reads like a different
      // question. (Assigning `value` fires no `input` event, so this cannot
      // re-open the other box's dropdown.)
      if (pageInput && pageInput.value !== raw) {
        pageInput.value = raw;
      }
      if (sidebarInput && sidebarInput.value !== raw) {
        sidebarInput.value = raw;
      }
      if (window.history && window.history.replaceState) {
        // Normalize the URL without pushing a history entry per keystroke.
        window.history.replaceState(
          null,
          "",
          raw ? `?q=${encodeURIComponent(raw)}` : window.location.pathname,
        );
      }
      ensureIndex(() => {
        renderAll();
      });
    };

    if (pageForm && pageInput) {
      pageInput.value = current;
      wireCombobox(pageForm, run);
    }
    if (sidebarInput) {
      sidebarInput.value = current;
    }
    if (current !== "") {
      run(current);
    } else {
      // A cold `search.html` (no `?q=`) still needs its message: `renderAll` is
      // otherwise only reached through `run`, so the count line would keep the
      // empty string the server rendered.
      renderAll();
      if (pageInput) {
        pageInput.focus();
      }
    }
    return run;
  };

  // The engine entry point, exposed on the same global as `setIndex`: the UI
  // below calls it, and it makes the engine verifiable head-to-head against the
  // Rust reference scorer (load a built index, run the canonical queries, diff
  // the orderings) without standing up a browser.
  api.query = (raw, limit) => runQuery(raw, limit || 20);
  api.record = (i) => (index ? index.records[i] : null);
  api.path = (i) => (index ? recordPath(i) : "");
  // The parity harness renders a hit without knowing which channel it came
  // from; these are the same accessors the UI uses.
  api.hitPath = (hit) => (index ? hitPath(hit) : "");
  api.hitAnchor = (hit) => (index ? hitAnchor(hit) : "");

  const main = () => {
    const sidebar = injectSidebarBox();
    const sidebarInput = sidebar ? sidebar.input : null;
    // On the results page BOTH boxes re-query in place; everywhere else both
    // navigate to it. Wiring the sidebar after the results page is set up is
    // what lets one submit path serve both.
    const submit = setupResultsPage(sidebarInput);
    if (sidebar) {
      wireCombobox(sidebar, submit || navigateToResults);
    }
    wireSlashShortcut(sidebarInput);
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", main);
  } else {
    main();
  }
})();

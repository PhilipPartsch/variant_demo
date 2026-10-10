/*
 * ubc build html — shell client script (always linked, dependency-free).
 *
 * Four always-on jobs, none of which the CSS-only shell needs in order to
 * function:
 *
 *  1. Theme toggle. A small icon button (injected here, so a no-JS page carries
 *     no dead control) which the shell places in whatever chrome can keep it
 *     REACHABLE at that width — the toc column or the mobile header — falling
 *     back to a fixed float everywhere else. It cycles auto -> light -> dark,
 *     persisted in localStorage
 *     under "ubc-theme", by setting/removing data-theme on <html> ("dark" /
 *     "light"; removed = auto). The base stylesheet's token model and the
 *     mermaid bundle's MutationObserver both react to that attribute. The
 *     persisted theme is applied BEFORE first paint by a tiny inline bootstrap
 *     in <head> (emitted by shell.rs); this deferred script only builds the
 *     button and wires the click, so there is no flash of the wrong theme.
 *
 *  2. Drawer enhancement (mobile overlay drawers). The open/close mechanism is
 *     pure CSS — a hidden checkbox toggled by header/scrim <label>s — so this
 *     only layers on Escape-to-close. The drawers open and close with this
 *     script absent. Deliberately NO aria-expanded mirroring: the checkbox is
 *     the one announced control (it carries the accessible name and its own
 *     checked state), and the openers are plain <label>s, which cannot carry a
 *     meaningful aria-expanded.
 *
 *  3. Scrollspy. Marks the "on this page" entry for the section the reader is
 *     currently in with `ub-active` + aria-current="location". Purely an
 *     enhancement: the emitted static HTML never carries the class, and the
 *     whole feature no-ops without IntersectionObserver. Deliberately driven
 *     by observers, never by the scroll pump below.
 *
 *  4. Scroll pump (the ONE scroll listener, rAF-debounced): a back-to-top
 *     pill (injected here, like the theme toggle) shown by toggling
 *     `ub-show-back-to-top` on <html> when the reader scrolls UP anywhere
 *     beyond the top 64px — hidden again scrolling down or back near the
 *     very top — plus the mobile header's `ub-scrolled` shadow once the
 *     page leaves the top.
 */
(() => {
  "use strict";

  const STORAGE_KEY = "ubc-theme";
  // The order the toggle button advances through on each click.
  const MODES = ["auto", "light", "dark"];
  // Inline SVG, not text glyphs: the previous half-circle/sun/moon text
  // characters (U+25D0 / U+2600 / U+263E) rendered as .notdef tofu on
  // systems whose fonts lack Miscellaneous Symbols coverage (U+263E, the
  // moon, has no emoji-font fallback at all), so the
  // toggle depended on the reader's installed fonts — the last control in
  // the shell that did. Shapes: feather-icons (MIT) `sun` and tabler-icons
  // (MIT) `moon`, as furo ships them (MIT) — the same in-source provenance
  // practice as the admonition and copy-button icon sets; the half-filled
  // `auto` circle is our own construction. Sized in em so the icon keeps
  // tracking the button's font-size across the shell's 100em upscale and
  // reader font preferences, as the text glyph did.
  //
  // `stroke-width: 1` is furo's own weight for these glyphs (every icon in its
  // `partials/icons.html` is stroke-1 except `feather-menu`), and it is what
  // puts this control on the same weight as the row's eye-code/pencil-code
  // neighbours now that those are furo-exact. Shared by all three instances,
  // the float's 17.6px circle included — checked at that size before the
  // change, not assumed.
  const ICON_OPEN =
    '<svg xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" ' +
    'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" ' +
    'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">';
  const ICON = {
    auto:
      ICON_OPEN +
      '<circle cx="12" cy="12" r="9"/>' +
      '<path d="M12 3a9 9 0 0 0 0 18z" fill="currentColor" stroke="none"/></svg>',
    light:
      ICON_OPEN +
      '<circle cx="12" cy="12" r="5"/>' +
      '<line x1="12" y1="1" x2="12" y2="3"/>' +
      '<line x1="12" y1="21" x2="12" y2="23"/>' +
      '<line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>' +
      '<line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>' +
      '<line x1="1" y1="12" x2="3" y2="12"/>' +
      '<line x1="21" y1="12" x2="23" y2="12"/>' +
      '<line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>' +
      '<line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>',
    dark:
      ICON_OPEN +
      '<path d="M12 3c.132 0 .263 0 .393 0a7.5 7.5 0 0 0 7.92 12.446a9 9 0 1 1 ' +
      '-8.313 -12.454z"/></svg>',
  };
  const LABEL = {
    auto: "Theme: match system (click for light)",
    light: "Theme: light (click for dark)",
    dark: "Theme: dark (click for system)",
  };

  // Scrollspy geometry, in CSS pixels.
  //
  // The reading line — how far below the viewport top the notional reading
  // position sits — is DERIVED at runtime, not fixed: it must clear
  // `section { scroll-margin-top }`, because a clicked toc link parks its
  // section exactly that far down and the entry just clicked has to be the one
  // that lights up. That margin is authored in `rem`, so at a large root font
  // size a hardcoded pixel line would sit ABOVE the parked section and light
  // the PREVIOUS entry on every click. READING_LINE_BUFFER is the slack added
  // on top of the measured margin.
  //
  // BOTTOM_EPSILON absorbs sub-pixel/zoom rounding in the scroll arithmetic, so
  // "the reader is at the end" is not a knife-edge comparison.
  const READING_LINE_BUFFER = 24;
  const BOTTOM_EPSILON = 2;

  /** The persisted mode, or "auto" when unset or unreadable. */
  const readMode = () => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored === "light" || stored === "dark") {
        return stored;
      }
    } catch (_err) {
      // localStorage can throw (privacy mode, a sandboxed file://) — treat as auto.
    }
    return "auto";
  };

  // The mode this page is currently showing, and every injected button (when
  // the DOM is up) that reflects it. A page carries one button per placement
  // its composition provides (up to three: the in-content icon row, the mobile
  // header, the float),
  // of which the stylesheet shows exactly one per viewport width; ALL are
  // repainted regardless, so whichever is on screen is correct — and so is the
  // next one, when a resize crosses a breakpoint.
  let currentMode = readMode();
  const toggleButtons = [];

  /** Reflect the current mode on every toggle button (icon + accessible name). */
  const paintButton = () => {
    for (const button of toggleButtons) {
      // Module-private constant markup only — no user data reaches this sink
      // (the same pattern as the back-to-top pill below).
      button.innerHTML = ICON[currentMode];
      button.setAttribute("aria-label", LABEL[currentMode]);
      button.title = LABEL[currentMode];
    }
  };

  /**
   * Show `mode`: set/remove data-theme on <html> and repaint the button.
   * `persist` is false when the mode CAME from storage (a BFCache restore or
   * another tab's change) — writing it back would echo a `storage` event to
   * that tab, which would write back in turn, ping-ponging forever.
   */
  const applyMode = (mode, persist) => {
    currentMode = mode;
    const root = document.documentElement;
    if (mode === "auto") {
      root.removeAttribute("data-theme");
    } else {
      root.setAttribute("data-theme", mode);
    }
    if (persist) {
      try {
        if (mode === "auto") {
          localStorage.removeItem(STORAGE_KEY);
        } else {
          localStorage.setItem(STORAGE_KEY, mode);
        }
      } catch (_err) {
        // Persistence is best-effort; the in-page state still applies.
      }
    }
    paintButton();
  };

  /** Build one toggle container + button, wired to advance the mode. */
  const buildToggle = (variant) => {
    const container = document.createElement("div");
    container.className = `ub-theme-toggle ${variant}`;
    const button = document.createElement("button");
    button.type = "button";
    button.className = "ub-theme-toggle-btn";
    button.addEventListener("click", () => {
      applyMode(MODES[(MODES.indexOf(currentMode) + 1) % MODES.length], true);
    });
    toggleButtons.push(button);
    container.appendChild(button);
    return container;
  };

  /**
   * Inject the theme toggle (idempotent).
   *
   * ONE PASS, up to three instances: an instance is built into every host the
   * page composition provides, and the STYLESHEET decides which single one is
   * visible at any width (see the placement matrix in `ubc.css`). Visibility
   * is never decided here — a width-aware script would have to re-run on
   * resize, and the CSS-only shell already knows the breakpoints.
   *
   * The guard above is what keeps that "exactly once" — because every
   * insertion happens in this single pass, a second call finds the first
   * instance and returns. Keep it one pass: an instance built outside it
   * would be invisible to the guard and could double up.
   *
   *  - `ub-theme-toggle-header` — into the mobile header's right slot, as its
   *    FIRST child, so the toggle sits LEFT of the drawer opener (furo's
   *    order, `page.html` header-right).
   *  - `ub-theme-toggle-ci` — into the in-content icon row, immediately BEFORE
   *    the toc opener, giving furo's row order: view, edit, theme-toggle,
   *    toc-icon. `insertBefore(node, null)` APPENDS, so a row with no opener
   *    (an actions-only row) lands the toggle last with no branch here. Since
   *    the USER RULING of 2026-08-14 (#2480) this is furo's two-instance model:
   *    the row serves EVERY width above 63em, and the sticky toc-column
   *    instance it replaced is retired. Injected only where a
   *    `.ub-mobile-header` element EXISTS: the row scrolls with the content, so
   *    on a page whose only other chrome is that same scrolling row (the
   *    headerless shape, and the bare content-only page) it would replace an
   *    always-reachable float with a control that leaves the viewport and never
   *    comes back.
   *  - `ub-theme-toggle-float` — the fixed fallback, always built, and the
   *    only instance a page with no shell chrome at all can have.
   *
   * The `ub-ci-toggle` marker set on the row is the reveal: the row is emitted
   * on every chrome page but is `display: none` until something is in it, and
   * this class is how the sheet learns THIS row was populated. It is a marker
   * rather than a `:has(> .ub-theme-toggle-ci)` selector because the CSS pins
   * walk `display` rules by the class tokens their selectors name, and a
   * `:has()` naming the instance class would be collected as one more of its
   * display outcomes.
   */
  const injectThemeToggle = () => {
    if (document.querySelector(".ub-theme-toggle")) {
      return;
    }
    const float = buildToggle("ub-theme-toggle-float");
    const headerRight = document.querySelector(".ub-mh-right");
    if (headerRight) {
      headerRight.insertBefore(
        buildToggle("ub-theme-toggle-header"),
        headerRight.firstChild,
      );
    }
    const contentIcons = document.querySelector(".ub-content-icons");
    if (contentIcons && document.querySelector(".ub-mobile-header")) {
      // The pairing marker: "a ci instance exists here", which no header
      // composition marker can express, since whether the row exists depends on
      // configuration as well as composition.
      float.classList.add("ub-theme-toggle-ci-paired");
      // …and its counterpart ON the row: the row is emitted for every chrome
      // page but stays hidden until it has a member, so this is what reveals it
      // wherever it hosts the toggle. Set in the SAME pass that builds the
      // instance, or the two can disagree and the sheet shows an empty row.
      contentIcons.classList.add("ub-ci-toggle");
      contentIcons.insertBefore(
        buildToggle("ub-theme-toggle-ci"),
        contentIcons.querySelector(".ub-toc-content-open"),
      );
    }
    document.body.appendChild(float);
    paintButton();
  };

  /**
   * Inject the back-to-top pill (idempotent; injected here like the theme
   * toggle, so a no-JS page carries no dead control). A plain `href="#"`
   * anchor — the default jump IS the behaviour, smoothed by the stylesheet's
   * motion-gated `scroll-behavior` — revealed by the scroll pump through the
   * `ub-show-back-to-top` class on <html>.
   *
   * Placed at the TOP of the main column, not appended to `<body>`: the pill
   * is `position: fixed` either way, but the DOM slot decides the tab order,
   * and a control that lives at the top of the viewport should be one of the
   * FIRST stops after the header, not the page's last (`display: none`
   * removes it from the tab order entirely while hidden). The under-header
   * drop selectors reach it as `.ub-mobile-header ~ .ub-page .ub-back-to-top`.
   * A page with no main column (a bare page) appends to `<body>` as before —
   * it has no header to coordinate with.
   */
  const injectBackToTop = () => {
    if (document.querySelector(".ub-back-to-top")) {
      return;
    }
    const link = document.createElement("a");
    link.className = "ub-back-to-top";
    link.href = "#";
    link.innerHTML =
      '<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true">' +
      '<path d="M12 19V5M5.5 11.5 12 5l6.5 6.5" fill="none" stroke="currentColor" ' +
      'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>' +
      "<span>Back to top</span>";
    const mainColumn = document.querySelector(".ub-main-column");
    if (mainColumn) {
      mainColumn.insertBefore(link, mainColumn.firstChild);
    } else {
      document.body.appendChild(link);
    }
  };

  /**
   * The scroll pump: the script's ONE scroll listener, rAF-debounced so a
   * burst of scroll events costs one class reconciliation per frame. It
   * drives the two scroll-position affordances (the scrollspy deliberately
   * stays observer-driven, see setupScrollSpy):
   *
   *  - the mobile header's `ub-scrolled` shadow, once the page leaves the top;
   *  - the back-to-top reveal (furo's behaviour): hidden within the top
   *    64px; shown when a scroll moves UP; hidden again moving down. An
   *    unchanged position (a horizontal scroll, a resize-echo) leaves the
   *    state alone.
   */
  const setupScrollPump = () => {
    const header = document.querySelector(".ub-mobile-header");
    const root = document.documentElement;
    const BACK_TO_TOP_OFFSET = 64;
    let lastY = root.scrollTop;
    const apply = (y) => {
      if (header) {
        header.classList.toggle("ub-scrolled", y > 0);
      }
      if (y < BACK_TO_TOP_OFFSET) {
        root.classList.remove("ub-show-back-to-top");
      } else if (y < lastY) {
        root.classList.add("ub-show-back-to-top");
      } else if (y > lastY) {
        root.classList.remove("ub-show-back-to-top");
      }
      lastY = y;
    };
    let ticking = false;
    window.addEventListener("scroll", () => {
      if (ticking) {
        return;
      }
      ticking = true;
      window.requestAnimationFrame(() => {
        ticking = false;
        apply(window.scrollY);
      });
    });
    // Reconcile the initial state: a page restored mid-document (BFCache, a
    // reload, a #fragment entry) must show the header shadow immediately.
    apply(window.scrollY);
  };

  /**
   * Scrollspy: mark the "on this page" entry for the section the reader is in.
   *
   * The entry set comes from the TOC'S OWN anchors, never from `section[id]` —
   * a promoted document title renders as a <section> that wraps the WHOLE page
   * and carries no toc link, so observing every section would pin a phantom
   * entry that can never be reached.
   *
   * The active entry is the DEEPEST listed section whose top has passed a
   * reading line just below the viewport top. Because a nested section's top is
   * always below its parent's, "the greatest top at or above the line" IS the
   * deepest section containing the line — no depth bookkeeping needed. Before
   * the first section reaches the line (top of the page) the first entry wins.
   *
   * At the very bottom of the document that geometric rule cannot reach every
   * entry: nothing in the final screenful can push its own top up to the
   * reading line. So at the bottom, explicit intent wins — if `location.hash`
   * names a listed entry at or after the geometric answer (the reader clicked
   * that toc link, or followed a deep link into it), THAT entry is marked.
   * Otherwise the LAST entry is, which keeps it reachable by plain scrolling. A
   * stale hash from further up the page is out-ranked by the geometry, so it
   * cannot pin an entry the reader has already scrolled past.
   *
   * No scroll listener. Two IntersectionObservers drive the re-evaluation:
   *
   *  - the sections are observed through a 1px-tall root band pinned AT the
   *    reading line (a negative `rootMargin` on both edges), so a callback
   *    fires exactly when a section top or bottom crosses that line — i.e.
   *    exactly when the geometric answer can change. A default-root observer
   *    would only fire at the VIEWPORT edges, leaving the marking hundreds of
   *    pixels stale between crossings. The band depends on the viewport height,
   *    so it is rebuilt on resize;
   *  - the end-of-document marker keeps a DEFAULT root: it must fire when the
   *    reader reaches the bottom, and on a short-tail page it never reaches the
   *    reading line at all, so the band would silence it.
   *
   * Plus `resize` (the geometry moved) and `hashchange` (a same-page jump may
   * not cross the band). Every trigger is coalesced into one animation-frame
   * read, so the rect measurements happen once per frame.
   */
  const setupScrollSpy = () => {
    if (typeof IntersectionObserver !== "function") {
      return;
    }
    const toc = document.querySelector(".ub-page-toc");
    if (!toc) {
      return;
    }
    const items = [];
    for (const link of toc.querySelectorAll('a[href^="#"]')) {
      const raw = link.getAttribute("href").slice(1);
      if (!raw) {
        continue;
      }
      let id = raw;
      try {
        id = decodeURIComponent(raw);
      } catch (_err) {
        // A malformed percent-escape: fall back to the literal fragment.
      }
      const section = document.getElementById(id);
      if (section) {
        items.push({ link: link, section: section, id: id });
      }
    }
    if (items.length === 0) {
      return;
    }
    // Only ever scrolled when it is a real, VISIBLE scroll box; off-canvas
    // (`visibility: hidden`, inherited from the outer drawer) panels are left
    // alone. The scroll box is the INNER `.ub-toc` container (the outer
    // `.ub-toc-drawer` is the width absorber / off-canvas panel). Nothing
    // overlays its top any more — the sticky column toggle that used to was
    // retired by the 2026-08-14 ruling — so the reveal below works against the
    // scrollport's own top edge.
    const drawer = toc.closest(".ub-toc");

    // The reading line, in CSS pixels below the viewport top. Re-measured
    // whenever the observer band is rebuilt, since `scroll-margin-top` is
    // authored in `rem` and the clamp depends on the viewport height.
    let readingLine = READING_LINE_BUFFER;
    const measureReadingLine = () => {
      const margin = parseFloat(
        window.getComputedStyle(items[0].section).scrollMarginTop,
      );
      const wanted = (Number.isFinite(margin) ? margin : 0) + READING_LINE_BUFFER;
      // Keep at least a 1px band available inside the viewport.
      readingLine = Math.min(wanted, Math.max(0, window.innerHeight - 2));
    };

    // Which sections the band observer currently reports as containing the
    // reading line. This set — NOT a second, independently-rounded rect read —
    // is what decides the active entry whenever it is non-empty.
    //
    // The distinction matters because an observer only reports TRANSITIONS. On
    // the frame where a section's top lands exactly on the band edge, the
    // observer may call it "entered" while a `getBoundingClientRect()` taken
    // moments later rounds its top to a hair BELOW the line and disagrees. The
    // observer then stays silent — the section is already inside the band — so
    // that single straddling frame would freeze the marking until some OTHER
    // section crossed, stranding the reader on a stale entry for the rest of
    // the section. Trusting the report keeps the two in lockstep by
    // construction.
    const inBand = new Set();

    /**
     * The DEEPEST listed section whose top is at or above the reading line, or
     * the first entry when none has reached it yet.
     *
     * A section the observer currently reports as CONTAINING the band counts as
     * having passed the line even when the rect read rounds a hair short. That
     * is what keeps the two views in lockstep at a straddle. The band is 1px
     * tall, so this is a ±1px tolerance on the predicate, not a no-op: a
     * section whose top sits a fraction BELOW the line can be reported as
     * inside it and win. That is the intended trade — the browser's own
     * measurement is the authority, and a sub-pixel disagreement resolved
     * either way beats a marking that freezes for the rest of the section.
     *
     * Note this is NOT "the deepest section containing the line": a subsection
     * that has ENDED just above the line still wins over its parent, which is
     * the documented rule — the reader is past its heading, and the parent's
     * entry is an ancestor of it in the toc either way.
     */
    const geometricIndex = () => {
      let best = -1;
      let bestTop = 0;
      for (let i = 0; i < items.length; i++) {
        const top = items[i].section.getBoundingClientRect().top;
        const passed = top <= readingLine || inBand.has(items[i].section);
        // `>=` so a tie resolves to the LATER (deeper) entry.
        if (passed && (best === -1 || top >= bestTop)) {
          best = i;
          bestTop = top;
        }
      }
      return best === -1 ? 0 : best;
    };

    /** The index the current `location.hash` names, or -1 if it names none. */
    const hashIndex = () => {
      const raw = window.location.hash.slice(1);
      if (!raw) {
        return -1;
      }
      let id = raw;
      try {
        id = decodeURIComponent(raw);
      } catch (_err) {
        // A malformed percent-escape: compare the literal fragment.
      }
      for (let i = 0; i < items.length; i++) {
        if (items[i].id === id) {
          return i;
        }
      }
      return -1;
    };

    /** The index of the entry to mark active (see the function docs above). */
    const activeIndex = () => {
      const geo = geometricIndex();
      const root = document.documentElement;
      const maxScroll = root.scrollHeight - root.clientHeight;
      if (maxScroll > BOTTOM_EPSILON && root.scrollTop >= maxScroll - BOTTOM_EPSILON) {
        // At the bottom the geometry cannot reach the final screenful, so an
        // explicit hash for an entry at or after it wins; otherwise the last
        // entry, which the geometry can never reach on its own.
        const hashed = hashIndex();
        return hashed >= geo ? hashed : items.length - 1;
      }
      return geo;
    };

    /**
     * Bring `link` into view inside the toc drawer's own scroll box, and
     * NOTHING else: only `scrollTop` on the drawer is ever assigned, so this
     * can never scroll the page (or any other ancestor) out from under the
     * reader — which `scrollIntoView` would be free to do. The scrollport's own
     * top edge is the limit: nothing overlays it since the sticky column toggle
     * was retired, so no height is reserved above the first entry.
     */
    const revealInDrawer = (link) => {
      if (!drawer || window.getComputedStyle(drawer).visibility === "hidden") {
        return;
      }
      const box = drawer.getBoundingClientRect();
      const item = link.getBoundingClientRect();
      const limit = box.top;
      if (item.top < limit) {
        drawer.scrollTop -= limit - item.top;
      } else if (item.bottom > box.bottom) {
        drawer.scrollTop += item.bottom - box.bottom;
      }
    };

    let active = -1;
    const update = () => {
      const next = activeIndex();
      if (next === active) {
        return;
      }
      if (active !== -1) {
        items[active].link.classList.remove("ub-active");
        items[active].link.removeAttribute("aria-current");
      }
      active = next;
      const link = items[active].link;
      link.classList.add("ub-active");
      link.setAttribute("aria-current", "location");
      revealInDrawer(link);
    };

    // The section observer, watching a 1px root band pinned at the reading
    // line. Rebuilt whenever the line or the viewport height moves, since the
    // band is expressed as a margin off both viewport edges.
    let bandObserver = null;
    const onBand = (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          inBand.add(entry.target);
        } else {
          inBand.delete(entry.target);
        }
      }
      scheduleUpdate();
    };
    const rebuildBand = () => {
      if (bandObserver) {
        bandObserver.disconnect();
      }
      // The old observer's reports describe the old band, so drop them; the new
      // one re-reports every target on its first delivery.
      inBand.clear();
      measureReadingLine();
      const below = Math.max(0, window.innerHeight - readingLine - 1);
      bandObserver = new IntersectionObserver(onBand, {
        rootMargin: `-${readingLine}px 0px -${below}px 0px`,
      });
      for (const item of items) {
        bandObserver.observe(item.section);
      }
    };

    // Coalesce every trigger into one per-frame read, so a burst of observer
    // callbacks (or a resize drag) measures the section rects — and rebuilds
    // the band — only once.
    let queued = false;
    let queuedRebuild = false;
    function scheduleUpdate() {
      if (queued) {
        return;
      }
      queued = true;
      window.requestAnimationFrame(() => {
        queued = false;
        const rebuilt = queuedRebuild;
        if (rebuilt) {
          queuedRebuild = false;
          rebuildBand();
        }
        update();
        // A resize can move the active entry out of the drawer's clip box
        // WITHOUT changing which entry is active, and `update` only reveals on
        // a change — so re-reveal explicitly after a rebuild.
        if (rebuilt && active !== -1) {
          revealInDrawer(items[active].link);
        }
      });
    }
    const scheduleRebuild = () => {
      queuedRebuild = true;
      scheduleUpdate();
    };

    // The end-of-document marker: 1px tall and pulled back by a -1px margin, so
    // it adds nothing to the scroll height while still being a real box the
    // observer can report. It enters the viewport only in the final pixel of
    // scroll, which is exactly the callback the bottom rule needs — and it gets
    // its own DEFAULT-root observer, because on a short-tail page it never
    // reaches the reading line, so the band would never report it.
    const end = document.createElement("div");
    end.className = "ub-scrollspy-end";
    end.setAttribute("aria-hidden", "true");
    document.body.appendChild(end);
    // Held in a binding: an observer is only kept alive by its registrations,
    // and an anonymous one invites a future edit to "tidy away" the only
    // reference to it.
    const endObserver = new IntersectionObserver(scheduleUpdate);
    endObserver.observe(end);

    rebuildBand();
    window.addEventListener("resize", scheduleRebuild);
    window.addEventListener("hashchange", scheduleUpdate);
    // The reading line is derived from a `rem` length, so it is only as good as
    // the root font size in effect when it was measured. A late-arriving web
    // font or stylesheet can move that after this deferred script has run, so
    // re-derive it once everything has loaded.
    if (document.readyState !== "complete") {
      window.addEventListener("load", scheduleRebuild, { once: true });
    }
    // Mark the initial entry synchronously: the first observer callback is a
    // frame away, and until it lands no entry would be marked at all.
    update();
  };

  /** Layer Escape-to-close onto the CSS-only drawer toggles. */
  const enhanceDrawers = () => {
    const toggles = Array.from(document.querySelectorAll(".ub-drawer-toggle"));
    if (toggles.length === 0) {
      return;
    }
    document.addEventListener("keydown", (event) => {
      if (event.key !== "Escape") {
        return;
      }
      for (const toggle of toggles) {
        if (toggle.checked) {
          toggle.checked = false;
        }
      }
    });
  };

  /**
   * Re-apply the persisted theme when this page could have gone stale:
   * a BFCache restore (`pageshow` with `persisted`, which runs no scripts) and a
   * `storage` event (the theme was changed in ANOTHER tab of the same origin).
   * Without these, a restored/background tab keeps a theme the user has since
   * changed. Only the attribute is re-applied — writing back is not needed, the
   * value already came from storage.
   */
  const watchExternalThemeChanges = () => {
    window.addEventListener("pageshow", (event) => {
      if (event.persisted) {
        applyMode(readMode(), false);
      }
    });
    window.addEventListener("storage", (event) => {
      // `key === null` is a whole-storage clear, which also drops our key.
      if (event.key === null || event.key === STORAGE_KEY) {
        applyMode(readMode(), false);
      }
    });
  };

  /*
   * Fragment navigation into a CLOSED <details> (#2907).
   *
   * A hidden need (`:hide:`) renders its whole card inside a closed <details>,
   * so anchors INSIDE it — a nested need's id, a label written in the body —
   * are reachable only if navigating to them opens the ancestor disclosures.
   * (The hidden need's OWN anchor is on the card root, outside the disclosure,
   * and needs none of this.)
   *
   * The platform does this natively: HTML's "scroll to the fragment" runs the
   * ancestor revealing algorithm, which walks the whole ancestor chain and
   * opens every closed <details> on it, BEFORE scrolling. But the floors are
   * recent — Chrome 97, Firefox 139, Safari 26.2 — so an older engine lands
   * the reader on a collapsed card with no sign that anything is there. This
   * is the polyfill for those, and it is deliberately a no-op everywhere else:
   * on a supporting engine every ancestor is already open by the time this
   * runs, `opened` stays false, and the scroll position the browser chose is
   * never touched.
   *
   * Three details that are easy to get wrong, all load-bearing:
   *
   *  - the LOOP, not `closest("details")`, which finds only the nearest
   *    ancestor and so breaks exactly the nested case this exists for;
   *  - the re-scroll, because opening a disclosure inserts content ABOVE the
   *    target and invalidates the scroll the browser already performed. Native
   *    engines reveal before scrolling and never need it; a polyfill runs in
   *    the opposite order and must compensate;
   *  - the CLICK listener, because `hashchange` does not fire when the reader
   *    clicks a link to the fragment they are already on — precisely what
   *    someone does after collapsing a card and clicking the cross-reference
   *    again.
   */
  const revealFragmentTarget = () => {
    const hash = window.location.hash.slice(1);
    if (!hash) return;
    let id;
    try {
      id = decodeURIComponent(hash);
    } catch {
      id = hash;
    }
    const target = document.getElementById(id) || document.getElementsByName(id)[0];
    if (!target) return;
    let opened = false;
    for (let node = target.parentElement; node; node = node.parentElement) {
      if (node.tagName === "DETAILS" && !node.open) {
        node.open = true;
        opened = true;
      }
    }
    if (opened) target.scrollIntoView();
  };

  const setupFragmentReveal = () => {
    revealFragmentTarget();
    window.addEventListener("hashchange", revealFragmentTarget);
    document.addEventListener("click", (event) => {
      const link =
        event.target instanceof Element ? event.target.closest('a[href*="#"]') : null;
      // Same-document links only — another page's fragment is handled by that
      // page's own load. Deferred a tick so the hash is updated first.
      if (
        link &&
        link.hash &&
        link.host === window.location.host &&
        link.pathname === window.location.pathname
      ) {
        window.setTimeout(revealFragmentTarget, 0);
      }
    });
  };

  const main = () => {
    injectThemeToggle();
    injectBackToTop();
    setupScrollPump();
    enhanceDrawers();
    setupScrollSpy();
    watchExternalThemeChanges();
    setupFragmentReveal();
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", main);
  } else {
    main();
  }
})();

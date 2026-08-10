/**
 * Rich changelog renderer for the Code Puppy Field Guide.
 *
 * Reads DATA.changelog (populated with impact levels, kind counts,
 * and hero-commit summaries by docs/generate-field-guide.py) and renders
 * release cards that make routine vs. high-impact work visually obvious.
 */

/* ------------------------------------------------------------------ */
// Shared helpers (mirrors the helpers in app.js for collapse/expand)
/* ------------------------------------------------------------------ */

function _openEl(el, bodySelector) {
  el.classList.add("open");
  const body = el.querySelector(bodySelector);
  if (body) body.style.maxHeight = body.scrollHeight + "px";
}

function _closeEl(el, bodySelector) {
  el.classList.remove("open");
  const body = el.querySelector(bodySelector);
  if (body) body.style.maxHeight = "0";
}

function _toggleEl(el, bodySelector) {
  if (el.classList.contains("open")) {
    _closeEl(el, bodySelector);
  } else {
    _openEl(el, bodySelector);
  }
}

/* ------------------------------------------------------------------ */
// Theme bars
/* ------------------------------------------------------------------ */

function _renderThemeBars(themes) {
  const total = Object.values(themes).reduce((a, b) => a + b, 0) || 1;
  const sorted = Object.entries(themes).sort((a, b) => b[1] - a[1]);
  const wrap = el("div", "theme-bars");
  sorted.slice(0, 5).forEach(([theme, count]) => {
    const row = el("div", "theme-row");
    const pct = Math.round((count / total) * 100);
    const color = THEME_COLORS[theme] || "#6b7d91";
    row.innerHTML = `
      <span class="theme-label" style="color:${color}">${theme}</span>
      <div class="theme-track"><div class="theme-fill" style="width:${pct}%;background:${color}"></div></div>
      <span class="theme-pct">${count}</span>
    `;
    wrap.appendChild(row);
  });
  return wrap;
}

/* ------------------------------------------------------------------ */
// Impact badge helpers
/* ------------------------------------------------------------------ */

const IMPACT_META = {
  major: {
    label: "Major",
    icon: "*",
    cls: "impact-major",
    tone: "This is the good stuff -- new capabilities, big fixes, or architecture moves.",
  },
  notable: {
    label: "Notable",
    icon: "^",
    cls: "impact-notable",
    tone: "Solid improvements and fixes worth knowing about.",
  },
  routine: {
    label: "Routine",
    icon: ".",
    cls: "impact-routine",
    tone: "Housekeeping: version bumps, CI, docs, and small cleanups.",
  },
};

function _impactBadge(level) {
  const meta = IMPACT_META[level] || IMPACT_META.routine;
  return `<span class="impact-badge ${meta.cls}" title="${meta.tone}">${meta.icon} ${meta.label}</span>`;
}

function _impactCountsHtml(counts) {
  const parts = [];
  if (counts.major) parts.push(`<span class="impact-count impact-major">${counts.major} major</span>`);
  if (counts.notable) parts.push(`<span class="impact-count impact-notable">${counts.notable} notable</span>`);
  if (counts.routine) parts.push(`<span class="impact-count impact-routine">${counts.routine} routine</span>`);
  return parts.join(" ");
}

/* ------------------------------------------------------------------ */
// Hero cards (high-impact commits with what/why/how)
/* ------------------------------------------------------------------ */

function _renderHeroCard(c) {
  const s = c.summary || {};
  const impact = c.impact || "routine";
  const card = el("div", `hero-card hero-${impact}`);
  card.innerHTML = `
    <div class="hero-header">
      ${_impactBadge(impact)}
      <span class="hero-kind kind kind-${c.kind}">${c.kind}</span>
      <span class="hero-sha">${c.sha}</span>
    </div>
    <div class="hero-subject">${escapeHtml(c.subject)}</div>
    <div class="hero-section">
      <h5>What it is</h5>
      <p>${escapeHtml(s.what || c.subject)}</p>
    </div>
    <div class="hero-section">
      <h5>Why it is rad</h5>
      <p>${escapeHtml(s.why_rad || "Keeps the project moving forward.")}</p>
    </div>
    <div class="hero-section">
      <h5>How it helps you</h5>
      <p>${escapeHtml(s.how_helps || "Part of the continuous improvement pipeline.")}</p>
    </div>
    ${c.github_url ? `<div class="hero-section"><a href="${escapeHtml(c.github_url)}" target="_blank" rel="noopener">View commit ${c.sha} on GitHub →</a></div>` : ""}
  `;
  return card;
}

function _renderHeroes(heroes) {
  if (!heroes || !heroes.length) return null;
  const wrap = el("div", "hero-grid");
  heroes.slice(0, 6).forEach((h) => wrap.appendChild(_renderHeroCard(h)));
  return wrap;
}

/* ------------------------------------------------------------------ */
// Category-driven commit rendering
/* ------------------------------------------------------------------ */

function _renderCommitDetail(c) {
  const inner = el("div", "commit-detail-inner");

  const s = c.summary || {};
  const detailBox = el("div", "commit-detail-box");
  detailBox.innerHTML = `
    <div class="detail-row">
      <span class="detail-label">What it is</span>
      <p>${escapeHtml(s.what || c.subject)}</p>
    </div>
    <div class="detail-row">
      <span class="detail-label">Why it matters</span>
      <p>${escapeHtml(s.why_rad || "Keeps the project moving forward.")}</p>
    </div>
    <div class="detail-row">
      <span class="detail-label">What it enables</span>
      <p>${escapeHtml(s.how_helps || "Part of the continuous improvement pipeline.")}</p>
    </div>
  `;
  inner.appendChild(detailBox);

  if (c.github_url) {
    const linkWrap = el("div", "commit-github-link");
    linkWrap.innerHTML = `<a href="${escapeHtml(c.github_url)}" target="_blank" rel="noopener">View commit ${c.sha} on GitHub →</a>`;
    inner.appendChild(linkWrap);
  }

  if (c.body) {
    const pre = el("pre", "commit-body-pre", escapeHtml(c.body));
    inner.appendChild(pre);
  }
  if (c.files && c.files.length) {
    const filesWrap = el("div", "commit-files");
    filesWrap.appendChild(el("span", "files-label", "Files: "));
    c.files.forEach((f, i) => {
      if (i > 0) filesWrap.appendChild(document.createTextNode(", "));
      filesWrap.appendChild(el("code", "", f));
    });
    inner.appendChild(filesWrap);
  }
  return inner;
}

function _renderCategoryCommit(c) {
  const row = el("div", "cat-commit");
  const color = THEME_COLORS[c.theme] || "#6b7d91";
  const kindBadge = c.kind && c.kind !== "other" && c.kind !== "merge"
    ? `<span class="kind kind-${c.kind}">${c.kind}</span>`
    : "";
  const impactDot = c.impact
    ? `<span class="impact-dot ${c.impact}" title="${(IMPACT_META[c.impact] || IMPACT_META.routine).tone}"></span>`
    : "";

  const head = el("div", "cat-commit-head");
  head.innerHTML = `
    <div class="cat-commit-main">
      ${impactDot}
      <span class="sha">${c.sha}</span>
      <span class="date">${c.date}</span>
      ${kindBadge}
      <span class="subject">${escapeHtml(c.subject)}</span>
    </div>
    <span class="theme" style="border-color:${color};color:${color}">${c.theme}</span>
  `;

  const body = el("div", "cat-commit-body");
  body.appendChild(_renderCommitDetail(c));

  head.addEventListener("click", () => _toggleEl(row, ".cat-commit-body"));

  row.appendChild(head);
  row.appendChild(body);
  return row;
}

function _renderCategorySection(group, openByDefault) {
  const section = el("div", `category-section category-${group.key}`);
  section.dataset.category = group.key;

  const header = el("div", "category-header");
  header.innerHTML = `
    <div class="category-title-row">
      <h4 class="category-title">${group.title}</h4>
      <span class="category-count">${group.count}</span>
    </div>
    <p class="category-description">${group.description}</p>
  `;
  header.addEventListener("click", () => _toggleEl(section, ".category-commits"));

  const commitsWrap = el("div", "category-commits");
  group.commits.forEach((c) => commitsWrap.appendChild(_renderCategoryCommit(c)));

  section.appendChild(header);
  section.appendChild(commitsWrap);

  if (openByDefault) {
    requestAnimationFrame(() => _openEl(section, ".category-commits"));
  }
  return section;
}

function _renderCategorizedCommits(release, container) {
  const groups = release.category_groups || [];
  if (!groups.length) return;

  const openByDefault = new Set(["major", "feature", "fix"]);
  const wrap = el("div", "category-grid");
  groups.forEach((g) => wrap.appendChild(_renderCategorySection(g, openByDefault.has(g.key))));
  container.appendChild(wrap);
}

function _renderCategoryMiniBar(groups) {
  if (!groups || !groups.length) return "";
  const categoryCls = {
    major: "cat-major",
    feature: "cat-feature",
    fix: "cat-fix",
    refactor: "cat-refactor",
    docs: "cat-docs",
    ci: "cat-ci",
    chore: "cat-chore",
    other: "cat-other",
  };
  return groups.map((g) => `<span class="category-mini ${categoryCls[g.key] || "cat-other"}">${g.title} ${g.count}</span>`).join("");
}

/* ------------------------------------------------------------------ */
// Main changelog render
/* ------------------------------------------------------------------ */

function renderChangelog() {
  const changelog = DATA.changelog || {};
  const releases = changelog.releases || [];
  const totalCommits = changelog.total_commits || 0;
  const since = changelog.since || "recent history";
  const unreleased = releases.find((r) => r.type === "unreleased");
  const versionReleases = releases.filter((r) => r.type === "release");

  const majorReleases = versionReleases.filter((r) => r.impact_level === "major").length;
  const notableReleases = versionReleases.filter((r) => r.impact_level === "notable").length;

  document.getElementById("changelog-intro").innerHTML = `
    <p><strong>${totalCommits.toLocaleString()}</strong> commits on <code>main</code> since <strong>${since}</strong>,
    grouped into <strong>${versionReleases.length}</strong> version releases plus the unreleased leading edge.</p>
    <p class="impact-legend">
      <span class="impact-badge impact-major">* Major</span> = new capabilities, big fixes, architecture moves
      <span class="impact-badge impact-notable">^ Notable</span> = solid improvements worth knowing
      <span class="impact-badge impact-routine">. Routine</span> = bumps, CI, docs, small cleanups
    </p>
    <p><strong>${majorReleases}</strong> major releases, <strong>${notableReleases}</strong> notable releases.
    Inside each release, changes are grouped into categories — Features, Bug Fixes, Optimizations, Docs, CI/Tests, and Maintenance — so you can zero in on what matters.</p>
    <p>Click any commit to see the full story: what changed, why it matters, what it enables you to do, and a direct link to the diff on GitHub.</p>
  `;

  const container = document.getElementById("changelog-timeline");

  // Theme guide explainer
  const themeGuide = changelog.theme_guide || {};
  if (Object.keys(themeGuide).length) {
    const guideWrap = el("div", "theme-guide");
    const guideHeader = el("div", "theme-guide-header");
    guideHeader.innerHTML = `<h4>What the themes mean</h4><span class="toggle-hint">click to expand</span>`;
    const guideBody = el("div", "theme-guide-body");
    Object.entries(themeGuide).forEach(([theme, desc]) => {
      const color = THEME_COLORS[theme] || "#6b7d91";
      const row = el("div", "theme-guide-row");
      row.innerHTML = `
        <span class="theme-guide-name" style="color:${color}">${theme}</span>
        <span class="theme-guide-desc">${escapeHtml(desc)}</span>
      `;
      guideBody.appendChild(row);
    });
    guideWrap.appendChild(guideHeader);
    guideWrap.appendChild(guideBody);
    guideHeader.addEventListener("click", () => _toggleEl(guideWrap, ".theme-guide-body"));
    container.appendChild(guideWrap);
    // Start collapsed so it doesn't steal focus from releases.
    _closeEl(guideWrap, ".theme-guide-body");
  }

  // Global controls
  const controls = el("div", "changelog-controls");
  const expandBtn = el("button", "btn", "Expand all releases");
  const collapseBtn = el("button", "btn", "Collapse all releases");
  const majorFilterBtn = el("button", "btn", "Show only major");
  expandBtn.addEventListener("click", () => {
    container.querySelectorAll(".release-hidden").forEach((r) => r.classList.remove("release-hidden"));
    container.querySelectorAll(".release").forEach((r) => _openEl(r, ".release-body"));
  });
  collapseBtn.addEventListener("click", () => {
    container.querySelectorAll(".release").forEach((r) => _closeEl(r, ".release-body"));
  });
  let majorOnly = false;
  majorFilterBtn.addEventListener("click", () => {
    majorOnly = !majorOnly;
    majorFilterBtn.textContent = majorOnly ? "Show all releases" : "Show only major";
    majorFilterBtn.classList.toggle("primary", majorOnly);
    container.querySelectorAll(".release").forEach((r) => {
      const isMajor = r.dataset.impact === "major";
      if (majorOnly && !isMajor) {
        r.style.display = "none";
      } else {
        r.style.display = "";
      }
    });
  });
  controls.appendChild(expandBtn);
  controls.appendChild(collapseBtn);
  controls.appendChild(majorFilterBtn);
  container.appendChild(controls);

  // Category filter chips (built from all groups across releases)
  const allCategoryKeys = new Set();
  releases.forEach((r) => {
    (r.category_groups || []).forEach((g) => allCategoryKeys.add(g.key));
  });
  if (allCategoryKeys.size) {
    const filterBar = el("div", "category-filter-bar");
    const keyTitle = {
      major: "Major",
      feature: "Features",
      fix: "Bug Fixes",
      refactor: "Optimizations",
      docs: "Docs",
      ci: "CI/Tests",
      chore: "Maintenance",
      other: "Other",
    };
    const activeFilters = new Set(allCategoryKeys);
    Array.from(allCategoryKeys).forEach((key) => {
      const chip = el("button", "chip active", keyTitle[key] || key);
      chip.dataset.category = key;
      chip.addEventListener("click", () => {
        chip.classList.toggle("active");
        if (chip.classList.contains("active")) {
          activeFilters.add(key);
        } else {
          activeFilters.delete(key);
        }
        container.querySelectorAll(".category-section").forEach((section) => {
          const show = activeFilters.has(section.dataset.category);
          section.style.display = show ? "" : "none";
        });
      });
      filterBar.appendChild(chip);
    });
    container.appendChild(filterBar);
  }

  function renderRelease(rel, hidden) {
    const releaseEl = el("div", `release release-${rel.impact_level || "routine"}`);
    releaseEl.dataset.impact = rel.impact_level || "routine";
    if (hidden) releaseEl.classList.add("release-hidden");

    const header = el("div", "release-header");
    const versionClass = rel.type === "unreleased" ? "unreleased" : "";
    const dateRange = rel.date === rel.end_date ? rel.date : `${rel.date} -> ${rel.end_date}`;
    const categoryBar = _renderCategoryMiniBar(rel.category_groups || []);

    header.innerHTML = `
      <div class="release-title">
        <span class="release-version ${versionClass}">${rel.version || "unknown"}</span>
        <span class="release-type">${rel.type}</span>
        ${_impactBadge(rel.impact_level || "routine")}
      </div>
      <div class="release-meta">${rel.commit_count} commits &bull; ${dateRange}</div>
      <div class="release-impact-summary">${escapeHtml(rel.impact_summary || "")}</div>
      <div class="release-category-bar">${categoryBar}</div>
      <div class="release-impact-counts">${_impactCountsHtml(rel.impact_counts || {})}</div>
    `;
    header.addEventListener("click", () => _toggleEl(releaseEl, ".release-body"));

    const body = el("div", "release-body");

    const heroGrid = _renderHeroes(rel.heroes || []);
    if (heroGrid) {
      const heroWrap = el("div", "release-heroes");
      heroWrap.appendChild(el("h4", "", "High-impact changes"));
      heroWrap.appendChild(heroGrid);
      body.appendChild(heroWrap);
    }

    _renderCategorizedCommits(rel, body);

    body.appendChild(_renderThemeBars(rel.themes || {}));

    releaseEl.appendChild(header);
    releaseEl.appendChild(body);
    container.appendChild(releaseEl);
    return releaseEl;
  }

  // Always show unreleased edge first
  const visibleLimit = 12;
  let visibleCount = 0;

  if (unreleased) {
    renderRelease(unreleased, false);
    visibleCount += 1;
  }

  versionReleases.forEach((rel) => {
    const hidden = visibleCount >= visibleLimit;
    renderRelease(rel, hidden);
    if (!hidden) visibleCount += 1;
  });

  // Add show-more button if releases were hidden
  const hiddenReleases = versionReleases.length - visibleCount + 1;
  if (hiddenReleases > 0) {
    const showMoreWrap = el("div", "show-more-wrap");
    const showMoreBtn = el("button", "btn primary", `Show all ${versionReleases.length} version releases`);
    showMoreBtn.addEventListener("click", () => {
      container.querySelectorAll(".release-hidden").forEach((el) => {
        el.classList.remove("release-hidden");
      });
      showMoreWrap.style.display = "none";
    });
    showMoreWrap.appendChild(showMoreBtn);
    container.appendChild(showMoreWrap);
  }

  // Auto-expand the first release so the page is not completely collapsed
  const firstRelease = container.querySelector(".release");
  if (firstRelease) _openEl(firstRelease, ".release-body");
}

// Render the changelog once the DOM is ready. Because changelog.js is loaded
// after app.js, this ensures app.js has already run boot() and set up the page.
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", renderChangelog);
} else {
  renderChangelog();
}

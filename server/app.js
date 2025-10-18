const express = require('express');
const path = require('path');
const app = express();

app.use(express.json());

app.get('/api/ping', (req, res) => {
  res.json({ ok: true, time: new Date().toISOString() });
});

// POST /api/solve
// Expects JSON { pattern: string, flags?: string, text: string, maxResults?: number }
// Returns { ok: true, matches: [{ match, groups: [...], named: {...} | null, index }], count: number, truncated: boolean }
app.post('/api/solve', (req, res) => {
  const { pattern, flags, text, maxResults } = req.body || {};
  if (!pattern || typeof text !== 'string') {
    return res.status(400).json({ ok: false, error: 'Request must include `pattern` and `text` fields' });
  }

  try {
    // Validate flags (only allow valid RegExp flags)
    const allowedFlags = /^[gimsuy]*$/;
    const usedFlags = flags || 'g';
    if (!allowedFlags.test(usedFlags)) {
      return res.status(400).json({ ok: false, error: 'Invalid regex flags' });
    }

    // Limit pattern length to avoid extremely large patterns
    if (pattern.length > 2000) {
      return res.status(400).json({ ok: false, error: 'Pattern too long' });
    }

    // Enforce numeric maxResults, default 100, maximum cap 100
    let limit = 100;
    if (typeof maxResults === 'number' && Number.isFinite(maxResults)) {
      limit = Math.max(1, Math.min(100, Math.floor(maxResults)));
    }

    // Ensure global flag is present for matchAll
    const flagsWithG = usedFlags.includes('g') ? usedFlags : usedFlags + 'g';
    const re = new RegExp(pattern, flagsWithG);

    const matches = [];
    for (const m of text.matchAll(re)) {
      const groups = [];
      for (let i = 1; i < m.length; i++) {
        groups.push(m[i] === undefined ? null : m[i]);
      }
      const named = m.groups || null;
      matches.push({
        match: m[0],
        groups,
        named,
        index: m.index
      });
      if (matches.length >= limit) break;
    }

    // approximate total matches count (may be expensive for huge texts)
    const allCount = [...text.matchAll(re)].length;
    const truncated = allCount > matches.length;

    return res.json({ ok: true, matches, count: matches.length, truncated });
  } catch (err) {
    return res.status(400).json({ ok: false, error: err.message });
  }
});

// Serve client static files if present
const clientDir = path.join(__dirname, '..', 'client');
app.use(express.static(clientDir));

module.exports = app;

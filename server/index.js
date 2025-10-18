const app = require('./app');

const port = process.env.PORT || 3000;
app.listen(port, () => console.log(`Server listening on ${port}`));

const express = require('express');
const path = require('path');
const app = express();

app.use(express.json());

app.get('/api/ping', (req, res) => {
  res.json({ ok: true, time: new Date().toISOString() });
});

// POST /api/solve
// Expects JSON { pattern: string, flags?: string, text: string }
// Returns { ok: true, matches: string[], count: number } on success
app.post('/api/solve', (req, res) => {
  const { pattern, flags, text } = req.body || {};
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

    const re = new RegExp(pattern, usedFlags);
    const matches = [...text.matchAll(re)].map(m => m[0]);
    return res.json({ ok: true, matches, count: matches.length });
  } catch (err) {
    return res.status(400).json({ ok: false, error: err.message });
  }
});

// Serve client static files if present
const clientDir = path.join(__dirname, '..', 'client');
app.use(express.static(clientDir));

const port = process.env.PORT || 3000;
app.listen(port, () => console.log(`Server listening on ${port}`));

const express = require('express');
const path = require('path');
const app = express();

app.use(express.json());

app.get('/api/ping', (req, res) => {
  res.json({ ok: true, time: new Date().toISOString() });
});

// Serve client static files if present
const clientDir = path.join(__dirname, '..', 'client');
app.use(express.static(clientDir));

const port = process.env.PORT || 3000;
app.listen(port, () => console.log(`Server listening on ${port}`));

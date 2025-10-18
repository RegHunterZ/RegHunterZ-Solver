#!/usr/bin/env bash
set -e
BRANCH="scaffold"
git checkout -b "$BRANCH"

# .gitignore
cat > .gitignore <<'EOF'
node_modules/
server/node_modules/
client/node_modules/
.env
.DS_Store
/dist
EOF

# README.md
cat > README.md <<'EOF'
# RegHunterZ-Solver

Cél: Poker solver + replayer — képi (OCR), TXT és konzol input, OpenAI alapú elemzés, replayer vizualizáció.

Kezdeti telepítés (lokálisan)
1. Klónozd:
   git clone https://github.com/RegHunterZ/RegHunterZ-Solver.git
   cd RegHunterZ-Solver
2. Server:
   cd server
   cp .env.example .env
   npm install
   npm run dev
3. Client:
   cd ../client
   npm install
   npm run dev

ENV változók (.env)
- OPENAI_API_KEY — OpenAI API kulcs (server)
- OPENAI_MODEL — alapértelmezett modell
- PORT — server port (opcionális)
EOF

# (Itt létrehozhatod a server/, client/, tools/ fájlokat — az előző üzenetben részletes tartalmat adtam.)
# Példa: üres server könyvtár
mkdir -p server/src server/promptTemplates client/src tools

# Commit & push
git add .
git commit -m "scaffold: add server, client, tools, README" || echo "nothing to commit"
git push -u origin "$BRANCH"
echo "Done. Branch '$BRANCH' pushed."
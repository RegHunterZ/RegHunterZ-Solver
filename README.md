# RegHunterZ-Solver

Cél: Poker solver + replayer, ami fogad képi, TXT és konzolos inputot, elküldi a leosztást OpenAI-nak és visszakapott stratégiai elemzést megjeleníti.

Fő komponensek:
- server: Node.js + Express — elemzés API, OpenAI integráció, OCR hook
- client: React — replayer, hand editor, range vizualizáció
- tools: CLI — kézi/konzol input és küldés

Kezdeti telepítés (lokálisan)
1. Klónozd:
   git clone https://github.com/RegHunterZ/RegHunterZ-Solver.git
2. Server:
   cd server
   cp .env.example .env
   npm install
   npm run dev
3. Client:
   cd ../client
   npm install
   npm run dev

ENV változók:
- OPENAI_API_KEY — OpenAI API kulcs (server oldalon)
- SOLVER_API_URL — (opcionális) a server URL-je a CLI-hoz

API (példa)
- POST /api/analyze
  - body: hand JSON vagy TXT (multipart/form-data ha image)
  - válasz: strukturált JSON stratégiai elemzés

Prompt és válasz formátum: a server a promptTemplates/analyzePrompt.txt alapján generálja a kérdést a GPT-nek.

---
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

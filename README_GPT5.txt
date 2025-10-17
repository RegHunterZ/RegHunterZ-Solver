KKPoker Solver — GPT‑5 Integration (v11)

   What changed (strictly internal, no UI/feature changes):
   - Updated model identifiers to `gpt-5` wherever an OpenAI model name was referenced in code/config.
   - Left all UI/QSS/assets untouched.
   - No change to features, window layout, button labels, or behavior.
   - API key is read from environment variable OPENAI_API_KEY (no embedded keys).

   Files auto-updated (2):
    - start.bat
- ai_coach/kkpoker_ai/api.py

   Notes:
   - If you previously set a different model in a user config file, it may now default to `gpt-5`.
   - To run: ensure OPENAI_API_KEY is set (e.g., in .env next to the launcher or in system env).
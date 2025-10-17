
# AI Coach (CostSaver)
- Paste HH text or use **Load Image (AI OCR)**.
- Mode selector: `cloud_first` / `local_first` / `local_only` (Tesseract).
- Image downscale + JPEG compress before API; cache by image-hash; retries with backoff on 429.

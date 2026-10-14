# Agentic RAG — Local AI System

Baseline teknologi: **ViteJS + React + TailwindCSS, FastAPI, LangChain (tahap integrasi berikutnya), Ollama, PaddleOCR (tahap integrasi berikutnya), dan PostgreSQL + pgvector**.

## Status
Fondasi aplikasi, health checks, Docker Compose, dan CI awal sudah tersedia. Pipeline RAG, OCR, agent tools, autentikasi, dan deployment production belum selesai.

## Struktur
- `frontend/`: ViteJS + React + TailwindCSS
- `backend/`: FastAPI dan SQLAlchemy
- `storage/uploads/`: file upload lokal (tidak di-commit)
- `storage/processed/`: hasil pemrosesan lokal (tidak di-commit)
- `docker-compose.yml`: PostgreSQL + pgvector, FastAPI, dan frontend Nginx
- `.env.example`: template konfigurasi; salin menjadi `.env`
- `.github/workflows/ci.yml`: backend test dan frontend build

## Prasyarat
- Docker Desktop dengan Docker Compose
- Git
- Untuk pengembangan tanpa Docker: Python 3.11+, Node.js 20+, dan npm
- Ollama lokal untuk tahap integrasi model; model disesuaikan dengan kapasitas perangkat

## Jalankan seluruh aplikasi dengan Docker
Dari root repository:

```powershell
Copy-Item .env.example .env
```

Buka `.env`, ganti `POSTGRES_PASSWORD` dengan password lokal yang kuat (gunakan karakter alfanumerik untuk menghindari masalah URL encoding), dan samakan password di `DATABASE_URL` untuk menjalankan backend langsung dari host. Docker Compose menyusun URL database internalnya sendiri.

Kemudian jalankan:

```bash
docker compose up --build -d
docker compose ps
```

Akses:
- Frontend: http://localhost:8080
- API langsung: http://localhost:8000
- Dokumentasi API: http://localhost:8000/docs
- Liveness: http://localhost:8000/health
- Readiness database: http://localhost:8000/health/ready

Log layanan:
```bash
docker compose logs -f backend
docker compose logs -f frontend
```

Matikan layanan:
```bash
docker compose down
```

Data PostgreSQL tetap tersimpan di named volume. Untuk menghapus volume database secara permanen, jangan gunakan `-v` kecuali memang ingin menghapus data.

## Menjalankan tanpa Docker (development)
### Database
Pastikan PostgreSQL + pgvector berjalan, lalu konfigurasi `DATABASE_URL` di `.env`.

### Backend (PowerShell)
```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend (terminal terpisah)
```powershell
cd frontend
npm install
npm run dev
```

Frontend development: http://localhost:5173

## Ollama
Install Ollama di host lokal dan unduh model yang sesuai dengan RAM/VRAM. Saat backend berjalan di Docker, konfigurasi default mengakses host melalui `host.docker.internal:11434`. Pada lingkungan yang tidak mendukung hostname tersebut, sesuaikan `OLLAMA_BASE_URL`.

## Keamanan
- Jangan commit file `.env`, kredensial, uploads, atau hasil pemrosesan.
- PostgreSQL diikat ke localhost; jangan ekspos port database ke internet.
- Ganti secrets sebelum penggunaan bersama/production.
- SQL Agent nantinya wajib memakai koneksi read-only, allowlist tabel/kolom, timeout, dan validasi query.
- Dokumen dari RAG harus diperlakukan sebagai data tidak tepercaya, bukan instruksi.
- Dockerfile saat ini untuk fondasi development; hardening production, TLS, autentikasi, dan observability masih perlu dikerjakan.

## Tahapan implementasi
1. Fondasi repository, Docker, health checks, dan CI.
2. Skema metadata dokumen serta koneksi pgvector.
3. Pipeline ingest dokumen, chunking, embedding, dan retrieval.
4. OCR dengan PaddleOCR dan agent tools.
5. Frontend chat/upload dan sitasi sumber.
6. Pengujian keamanan dan deployment VPS.

# Agentic RAG — Local AI System

Baseline development mengikuti spesifikasi proyek: **ViteJS + React, FastAPI, LangChain, PostgreSQL + pgvector, PaddleOCR, dan Ollama**.

## Status
Fondasi awal repository sudah tersedia. Fitur RAG, OCR, SQL Tool, agent orchestration, autentikasi, dan deployment production akan diimplementasikan bertahap setelah infrastruktur dasar tervalidasi.

## Struktur
- `frontend/`: ViteJS + React + TailwindCSS
- `backend/`: FastAPI
- `storage/uploads/`: file upload lokal (tidak di-commit)
- `storage/processed/`: hasil pemrosesan lokal (tidak di-commit)
- `docker-compose.yml`: PostgreSQL dengan pgvector
- `.env.example`: template konfigurasi; salin menjadi `.env`

## Prasyarat development
- Python 3.10+
- Node.js LTS dan npm
- Docker Desktop dengan Docker Compose
- Ollama (dapat dijalankan di host lokal)
- Git

## Setup awal
Dari root repository, salin template environment:

```powershell
Copy-Item .env.example .env
```

Edit `.env` dan ubah `POSTGRES_PASSWORD` serta `DATABASE_URL` dengan password yang sama. Jangan commit `.env`.

## Menjalankan database
```bash
docker compose up -d postgres
docker compose ps
```

Verifikasi extension pgvector:
```bash
docker compose exec postgres psql -U agentic_rag_app -d agentic_rag -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

## Menjalankan backend
Windows PowerShell, dari root repository:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Health check: http://127.0.0.1:8000/health  
API docs: http://127.0.0.1:8000/docs

## Menjalankan frontend
Di terminal terpisah, dari root repository:

```bash
cd frontend
npm install
npm run dev
```

Frontend: http://localhost:5173

## Ollama
Install Ollama sesuai OS dari situs resminya, lalu pilih model yang sesuai dengan kapasitas RAM/VRAM lokal. Jangan mengasumsikan model 8B cocok untuk VPS 2 vCPU / RAM 4 GB.

## Keamanan
- Jangan commit file `.env`, kredensial, uploads, atau hasil pemrosesan.
- SQL Agent nantinya wajib menggunakan koneksi read-only, allowlist tabel/kolom, timeout, dan validasi query.
- Jangan mengekspos port PostgreSQL ke internet pada production.
- Dokumen yang diambil dari RAG diperlakukan sebagai data tidak tepercaya, bukan instruksi.
- Password dan secrets harus diganti sebelum penggunaan bersama/production.

## Tahapan
1. Fondasi repository dan database.
2. Backend API dan koneksi database.
3. Pipeline ingest dokumen, embedding, dan RAG.
4. OCR dan agent tools.
5. Frontend chat dan upload.
6. Testing keamanan serta deployment VPS.

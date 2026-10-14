# Agentic RAG — Local AI System

Baseline teknologi: **ViteJS + React + TailwindCSS, FastAPI, SQLAlchemy, PostgreSQL + pgvector, dan Ollama**. PaddleOCR, LangChain, agent tools, autentikasi, dan deployment production masih menjadi tahapan lanjutan.

## Status
Fondasi aplikasi, Docker Compose, health checks, model dokumen/chunk, ingest teks, embedding, semantic search, endpoint RAG berbasis Ollama, dan enkripsi file AES-256-GCM sudah ditambahkan. OCR untuk dokumen scan, orchestration agent, autentikasi, enkripsi metadata database, dan deployment production belum selesai.

## Struktur utama
- `frontend/`: ViteJS + React + TailwindCSS
- `backend/`: FastAPI, konfigurasi, SQLAlchemy, model dokumen, dan perintah inisialisasi DB
- `backend/models.py`: tabel `documents` dan `document_chunks`; embedding disiapkan untuk 768 dimensi `nomic-embed-text`
- `backend/init_db.py`: inisialisasi extension pgvector dan tabel awal
- `docker-compose.yml`: PostgreSQL + pgvector, FastAPI, dan frontend Nginx
- `.github/workflows/ci.yml`: backend tests dan frontend build

## Prasyarat
- Docker Desktop dengan Docker Compose
- Git
- Untuk pengembangan tanpa Docker: Python 3.11+, Node.js 20+, dan npm
- Ollama lokal untuk tahap integrasi model; model harus disesuaikan dengan kapasitas perangkat

## Jalankan seluruh aplikasi dengan Docker
Dari root repository:

```powershell
Copy-Item .env.example .env
```

Buka `.env` dan ubah `POSTGRES_PASSWORD` menjadi password lokal yang kuat. Gunakan karakter alfanumerik untuk menghindari masalah URL encoding. Jika menjalankan backend langsung dari host, samakan password di `DATABASE_URL`. Docker Compose membentuk URL internal database sendiri.

Generate key enkripsi AES-256-GCM yang unik, lalu masukkan hasilnya ke `FILE_ENCRYPTION_KEY` di file `.env`:

```powershell
py -c "import secrets,base64; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())"
```

Jangan commit atau membagikan key tersebut. Simpan cadangan key di pengelola rahasia yang aman. **Jika key hilang, file yang tersimpan terenkripsi tidak dapat dipulihkan.** Jangan mengganti key setelah ada dokumen yang tersimpan kecuali kamu sudah membuat prosedur re-enkripsi.

Kemudian:

```bash
docker compose up --build -d
docker compose ps
```

Akses:
- Frontend: http://localhost:8080
- API: http://localhost:8000
- Dokumentasi API: http://localhost:8000/docs
- Liveness: http://localhost:8000/health
- Readiness database: http://localhost:8000/health/ready

Log dan stop:

```bash
docker compose logs -f backend
docker compose logs -f frontend
docker compose down
```

## Upload dan ingest dokumen

Endpoint `POST /api/documents` menerima file TXT, Markdown, PDF berbasis teks, dan DOCX. Endpoint menghitung SHA-256 untuk mencegah upload ulang konten yang sama, mengekstrak teks, membuat chunk ber-overlap, meminta embedding ke Ollama, lalu menyimpan metadata dan vector ke PostgreSQL + pgvector.

Contoh dengan curl:

```bash
curl -X POST http://localhost:8000/api/documents \
  -F "file=@./contoh.pdf"
```

Persyaratan: database schema sudah diinisialisasi dan Ollama berjalan dengan model embedding yang dikonfigurasi. PDF hasil scan dan gambar belum diproses OCR.

## Semantic search

Endpoint `POST /api/search` mengubah pertanyaan menjadi embedding melalui Ollama, lalu mencari chunk terdekat dengan cosine distance di pgvector.

```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query":"Apa isi dokumen ini?","top_k":5}'
```

Hasil berisi teks chunk, nama file, nomor halaman bila tersedia, dan skor kemiripan cosine (bukan probabilitas).

## Tanya dokumen dengan RAG

Endpoint `POST /api/chat` mengambil lima chunk terdekat dari pgvector, lalu meminta model Ollama menyusun jawaban berdasarkan konteks yang ditemukan. Instruksi model mengharuskan penggunaan penanda sumber seperti `[S1]` dan memperlakukan isi dokumen sebagai data, bukan instruksi.

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"demo","message":"Apa poin penting dari dokumen?"}'
```

Response berisi jawaban, metode retrieval yang digunakan, dan daftar sumber yang disertakan ke model. Validasi sitasi tetap diperlukan. Endpoint ini adalah RAG dasar; belum merupakan agent yang dapat memilih dan menjalankan banyak tools, dan belum memakai n8n.

## Inisialisasi schema pgvector
Setelah database tersedia, jalankan sekali dari root repository:

```bash
docker compose exec backend python init_db.py
```

Perintah ini membuat extension `vector` dan tabel awal. Tabel yang dibuat:
- `documents`: metadata file, hash SHA-256, status pemrosesan, dan lokasi penyimpanan
- `document_chunks`: teks per chunk, indeks chunk, nomor halaman, metadata, dan embedding vector

Dimensi embedding awal disetel ke 768 untuk `nomic-embed-text`. Jika model embedding diganti, sesuaikan dimensi sebelum menyimpan vector dari model baru.

## Menjalankan backend tanpa Docker
Pastikan PostgreSQL + pgvector tersedia dan `DATABASE_URL` pada `.env` sesuai.

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python init_db.py
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

## Menjalankan frontend tanpa Docker
Terminal terpisah:

```powershell
cd frontend
npm install
npm run dev
```

Frontend development: http://localhost:5173

## Tes backend
Dari folder `backend`:

```bash
pip install pytest
pytest -q
```

GitHub Actions juga menjalankan backend tests dan frontend build pada push/pull request ke branch `main`.

## Ollama
Install Ollama di host lokal dan unduh model yang sesuai dengan RAM/VRAM. Default konfigurasi model chat adalah `qwen2.5:3b` dan embedding `nomic-embed-text`. Unduh keduanya sebelum pengujian dengan `ollama pull qwen2.5:3b` dan `ollama pull nomic-embed-text`. Model 3B dipilih sebagai titik awal yang lebih ringan, tetapi penggunaan pada VPS RAM 4 GB tetap perlu diuji karena model, PostgreSQL, dan API berbagi memori. Saat backend berjalan di Docker, URL default mengarah ke host melalui `host.docker.internal:11434`; sesuaikan pada lingkungan yang tidak mendukung hostname tersebut.

## Keamanan
- Jangan commit file `.env`, kredensial, uploads, atau hasil pemrosesan.
- File asli yang disimpan pada disk dienkripsi dengan AES-256-GCM; metadata dan teks chunk pada PostgreSQL belum dienkripsi pada level aplikasi.
- Jaga kerahasiaan dan backup `FILE_ENCRYPTION_KEY`; rotasi key memerlukan migrasi file.
- PostgreSQL hanya dipublikasikan ke localhost; jangan ekspos port database ke internet.
- Ganti secrets sebelum penggunaan bersama/production.
- SQL Agent nantinya harus memakai koneksi read-only, allowlist tabel/kolom, timeout, dan validasi query.
- Dokumen dari RAG adalah data tidak tepercaya, bukan instruksi.
- Hardening production, TLS, autentikasi, backup, dan observability masih perlu dikerjakan.

## Tahapan implementasi
1. Fondasi repository, Docker, health checks, dan CI.
2. Skema metadata dokumen serta pgvector.
3. Pipeline ingest dokumen, chunking, embedding, dan retrieval.
4. Enkripsi file AES-256-GCM dan pengujian dasar.
5. OCR dengan PaddleOCR dan agent tools.
6. Autentikasi, otorisasi, pengujian keamanan, serta deployment VPS.

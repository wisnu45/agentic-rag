# Agentic RAG — Local AI System

Baseline teknologi: **ViteJS + React + TailwindCSS, FastAPI, SQLAlchemy, PostgreSQL + pgvector, Ollama (model lokal/gratis), JWT, RBAC, dan workflow n8n opsional**. PaddleOCR tersedia sebagai dependensi opsional.

## Status
Fondasi aplikasi, Docker Compose, ingest/retrieval, RAG Ollama, enkripsi file AES-256-GCM, OCR opsional, JWT/RBAC, adapter n8n, workflow n8n importable, dan CI sudah tersedia. CI terakhir memverifikasi 33 tes backend dan frontend build (periksa run terbaru pada GitHub Actions). Workflow n8n belum diuji end-to-end terhadap instance n8n dan model Ollama yang berjalan; benchmark OCR, enkripsi metadata database, serta deployment production masih perlu dikerjakan.

## Struktur utama
- `frontend/`: ViteJS + React + TailwindCSS
- `backend/`: FastAPI, konfigurasi, SQLAlchemy, model dokumen, ekstraksi teks, dan OCR opsional
- `backend/models.py`: tabel `users`, `documents`, dan `document_chunks`; embedding disiapkan untuk 768 dimensi `nomic-embed-text`
- `backend/auth.py`: password hashing scrypt, JWT, dan role checks (`admin`, `editor`, `viewer`)
- `backend/create_user.py`: provisioning akun dari terminal tepercaya; tidak ada endpoint registrasi publik
- `backend/orchestration.py`: adapter webhook n8n opsional untuk generasi jawaban; Ollama langsung menjadi fallback saat webhook tidak dikonfigurasi
- `n8n/workflows/agentic-rag-ollama.json`: workflow n8n importable yang mengirim konteks ke Ollama dan mengembalikan `{ "answer": "..." }`
- `backend/ocr.py`: PaddleOCR CPU-only untuk raster image dan PDF hasil scan; dependensi dimuat secara lazy
- `backend/requirements-ocr.txt`: paket tambahan khusus OCR, terpisah dari requirements inti
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

## Import skema PostgreSQL secara manual

Skema SQL siap impor tersedia di `database/schema.sql`. Script ini sesuai dengan tabel ORM utama dan memakai pgvector dengan embedding 768 dimensi. Jalankan hanya pada database baru/kosong, atau tinjau objek yang sudah ada sebelum mengimpor.

**Melalui DBeaver**
1. Hubungkan DBeaver ke database PostgreSQL tujuan.
2. Pilih database, lalu buka SQL Editor.
3. Buka file `database/schema.sql` dari repository.
4. Jalankan seluruh script.
5. Refresh `Schemas → public → Tables`, lalu pastikan tabel `users`, `documents`, dan `document_chunks` tersedia.

**Melalui terminal**
```bash
psql -h localhost -U agentic_rag_app -d agentic_rag -v ON_ERROR_STOP=1 -f database/schema.sql
```

Pastikan ekstensi pgvector sudah terpasang pada server PostgreSQL dan akun database memiliki izin untuk membuat ekstensi. Script membuat struktur tabel dan indeks saja; script tidak membuat akun admin, tidak mengisi dokumen, dan tidak memindahkan data dari Google AI Studio. Untuk deployment Docker, backend juga memiliki `backend/init_db.py` yang menginisialisasi ekstensi dan tabel berdasarkan model ORM.

## OCR untuk PDF scan dan gambar (opsional)

Ekstraksi teks standar tetap digunakan untuk halaman PDF yang memiliki text layer. Jika satu atau beberapa halaman tidak memiliki teks yang bisa diekstrak, hanya halaman tersebut yang dirender dan diproses dengan PaddleOCR; teks dari halaman yang sudah terbaca tetap dipertahankan. File PNG, JPG/JPEG, TIFF, dan BMP juga diarahkan ke OCR. Nomor halaman PDF dipertahankan pada hasil ekstraksi.

OCR sengaja tidak dipasang pada image default karena dependensinya besar dan inferensi CPU dapat menambah waktu serta konsumsi RAM. Untuk mengaktifkannya, ubah `INSTALL_OCR=true` di `.env`, lalu build ulang:

```bash
docker compose build --no-cache backend
docker compose up -d backend
```

Untuk instalasi backend langsung dari host:

```powershell
cd backend
pip install -r requirements-ocr.txt
```

PaddleOCR dikonfigurasi untuk CPU dan model bahasa Latin (`lang="en"`) sebagai baseline. Akurasi untuk dokumen bahasa Indonesia, tabel, tulisan buram, dan tata letak kompleks perlu dievaluasi menggunakan sampel dokumen nyata. OCR tidak menjamin hasil sempurna. **Pada VPS 2 vCPU/4 GB RAM, jangan mengaktifkan OCR sebelum mengukur penggunaan memori dan waktu proses**; sebaiknya lakukan benchmark pada mesin pengembangan terlebih dahulu. Dependensi OCR dan model mungkin menambah ukuran image serta waktu build.

Contoh upload gambar melalui API:

```bash
curl -X POST http://localhost:8000/api/documents \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -F "file=@./scan.jpg"
```

Jika paket OCR belum dipasang, endpoint akan mengembalikan pesan yang menjelaskan bahwa dependensi opsional diperlukan.

## Autentikasi dan RBAC

Endpoint dokumen, pencarian, dan chat membutuhkan access token JWT. Upload hanya dapat dilakukan oleh role `admin` atau `editor`; pencarian dan chat tersedia bagi seluruh pengguna yang sudah login (`admin`, `editor`, atau `viewer`). Token berlaku selama 30 menit secara default dan disimpan di memori frontend; setelah browser di-refresh, login kembali diperlukan.

1. Isi `JWT_SECRET_KEY` pada `.env` dengan secret acak unik minimal 32 karakter:

   ```powershell
   py -c "import secrets; print(secrets.token_urlsafe(48))"
   ```

2. Jalankan aplikasi dan inisialisasi schema:

   ```bash
   docker compose up --build -d
   docker compose exec backend python init_db.py
   ```

3. Buat akun admin melalui terminal tepercaya. Password diminta secara interaktif dan disimpan sebagai hash scrypt:

   ```bash
   docker compose exec backend python create_user.py --username admin --role admin
   ```

4. Login melalui UI. Untuk integrasi API, kirim username/password sebagai form-urlencoded ke `POST /api/auth/token`, lalu gunakan `Authorization: Bearer <token>` untuk endpoint yang dilindungi. `GET /api/auth/me` mengembalikan username dan role aktif.

Tidak tersedia registrasi publik. Simpan secret JWT dan kredensial di luar repository. Implementasi ini adalah baseline MVP; sebelum production, tambahkan rate limiting untuk login, audit log, kebijakan pencabutan token, serta hardening reverse proxy/TLS.

## Integrasi n8n + Ollama (opsional)

Model LLM menggunakan **Ollama tanpa biaya API**. Default model chat adalah `qwen2.5:3b`; model embedding adalah `nomic-embed-text`. Model diunduh ke mesin yang menjalankan Ollama, sehingga penggunaan tetap bergantung pada RAM/CPU mesin tersebut. Tidak diperlukan API key OpenAI.

Jika `N8N_CHAT_WEBHOOK_URL` kosong, FastAPI menggunakan Ollama secara langsung. Jika URL diisi, FastAPI melakukan retrieval di pgvector lalu meneruskan pertanyaan dan lima konteks teratas ke workflow n8n. Jika workflow gagal, API mengembalikan error alih-alih diam-diam mengubah jalur.

### Workflow siap impor

File workflow tersedia di `n8n/workflows/agentic-rag-ollama.json`.

1. Buka n8n, pilih **Workflows → Import from File**, lalu pilih file JSON tersebut.
2. Pada node **Webhook**, atur Authentication menjadi **Header Auth**. Buat credential Header Auth dengan:
   - Name: `X-Agentic-RAG-Webhook-Secret`
   - Value: nilai secret yang sama dengan `N8N_WEBHOOK_SECRET` di file `.env`
3. Pada node **Generate Answer with Ollama**, sesuaikan URL Ollama. Default `http://host.docker.internal:11434/api/chat` sesuai untuk banyak setup Docker Desktop. Jika n8n bukan di Docker Desktop atau Ollama berada di mesin lain, gunakan alamat Ollama yang dapat dijangkau dari container n8n; jangan gunakan `localhost` kecuali Ollama berjalan di container/host network yang sama.
4. Pastikan Ollama aktif dan model sudah diunduh. Jalankan di terminal mesin Ollama:
   ```bash
   ollama pull qwen2.5:3b
   ollama pull nomic-embed-text
   ollama list
   ```
5. Simpan workflow dan aktifkan (**Active**). Gunakan **Production URL** pada node Webhook, dengan path `agentic-rag-chat`.
6. Isi URL webhook dan secret yang sama pada `.env`, lalu restart backend:
   ```dotenv
   N8N_CHAT_WEBHOOK_URL=https://n8n.example.com/webhook/agentic-rag-chat
   N8N_WEBHOOK_SECRET=GANTI_DENGAN_SECRET_ACAK_MINIMAL_32_KARAKTER
   N8N_TIMEOUT_SECONDS=90
   ```
   Generate secret dengan `py -c "import secrets; print(secrets.token_urlsafe(48))"`.
7. Uji workflow dengan contoh payload sebelum menyambungkan aplikasi. Response harus berupa JSON dengan field string `answer` yang tidak kosong.

**Keamanan:** jangan mengaktifkan webhook tanpa Header Auth. Gunakan HTTPS atau jaringan privat tepercaya karena kutipan dokumen dapat berisi informasi internal. Jangan memberikan akses shell, file system, atau SQL write ke agent. Prompt berusaha memperlakukan kutipan sebagai data tidak tepercaya, tetapi ini bukan jaminan mutlak terhadap prompt injection.

### Tes integrasi manual

Setelah workflow aktif dan URL production sudah diisi di `.env`, login ke aplikasi untuk memperoleh token JWT. Kemudian uji endpoint chat melalui API:
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"session_id":"demo","message":"Ringkas isi dokumen dan sertakan sumber."}'
```
Pastikan respons memiliki `tool_used: "pgvector_retrieval+n8n"`, jawaban tidak kosong, dan daftar sumber sesuai dokumen yang terindeks. Tes CI menggunakan mock dan **tidak** menggantikan pengujian end-to-end ini.

## Upload dan ingest dokumen

Endpoint `POST /api/documents` menerima file TXT, Markdown, PDF, DOCX, serta gambar raster yang didukung. Endpoint menghitung SHA-256 untuk mencegah upload ulang konten yang sama, mengekstrak teks (OCR bila diperlukan dan tersedia), membuat chunk ber-overlap, meminta embedding ke Ollama, lalu menyimpan metadata dan vector ke PostgreSQL + pgvector.

Contoh dengan curl:

```bash
curl -X POST http://localhost:8000/api/documents \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -F "file=@./contoh.pdf"
```

Persyaratan: database schema sudah diinisialisasi dan Ollama berjalan dengan model embedding yang dikonfigurasi.

## Semantic search

Endpoint `POST /api/search` mengubah pertanyaan menjadi embedding melalui Ollama, lalu mencari chunk terdekat dengan cosine distance di pgvector.

```bash
curl -X POST http://localhost:8000/api/search \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"query":"Apa isi dokumen ini?","top_k":5}'
```

Hasil berisi teks chunk, nama file, nomor halaman bila tersedia, dan skor kemiripan cosine (bukan probabilitas).

## Tanya dokumen dengan RAG

Endpoint `POST /api/chat` mengambil lima chunk terdekat dari pgvector, lalu meminta model Ollama menyusun jawaban berdasarkan konteks yang ditemukan. Jika `N8N_CHAT_WEBHOOK_URL` dikonfigurasi, generasi jawaban diarahkan melalui workflow n8n dan node Ollama di workflow tersebut. Instruksi model mengharuskan penggunaan penanda sumber seperti `[S1]` dan memperlakukan isi dokumen sebagai data, bukan instruksi.

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"session_id":"demo","message":"Apa poin penting dari dokumen?"}'
```

Response berisi jawaban, metode yang digunakan, dan daftar sumber yang disertakan ke model. Validasi sitasi tetap diperlukan. Sistem ini merupakan RAG dengan orkestrasi n8n opsional; belum merupakan agent yang dapat memilih dan menjalankan banyak tools secara dinamis.

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

GitHub Actions juga menjalankan backend tests dan frontend build pada push/pull request ke branch `main`. Status tes harus dicek dari hasil workflow aktual; perubahan kode tidak dianggap tervalidasi hanya karena sudah di-commit.

## Ollama

Install Ollama di host lokal dan unduh model yang sesuai dengan RAM/VRAM. Default konfigurasi model chat adalah `qwen2.5:3b` dan embedding `nomic-embed-text`. Unduh keduanya sebelum pengujian dengan `ollama pull qwen2.5:3b` dan `ollama pull nomic-embed-text`. Model 3B dipilih sebagai titik awal yang lebih ringan, tetapi penggunaan pada VPS RAM 4 GB tetap perlu diuji karena model, PostgreSQL, dan API berbagi memori. Saat backend berjalan di Docker, URL default mengarah ke host melalui `host.docker.internal:11434`; sesuaikan pada lingkungan yang tidak mendukung hostname tersebut.

## Keamanan

- Jangan commit file `.env`, kredensial, uploads, atau hasil pemrosesan.
- File asli yang disimpan pada disk dienkripsi dengan AES-256-GCM; metadata dan teks chunk pada PostgreSQL belum dienkripsi pada level aplikasi.
- Jaga kerahasiaan dan backup `FILE_ENCRYPTION_KEY`; rotasi key memerlukan migrasi file.
- PostgreSQL hanya dipublikasikan ke localhost; jangan ekspos port database ke internet.
- Ganti secrets sebelum penggunaan bersama/production; `JWT_SECRET_KEY` wajib diisi dan minimal 32 karakter.
- Endpoint dokumen/search/chat dilindungi JWT; upload dibatasi pada role admin/editor. Akun dibuat melalui CLI, bukan registrasi publik.
- Token JWT singkat disimpan di memori frontend, bukan localStorage; refresh browser memerlukan login ulang.
- SQL Agent nantinya harus memakai koneksi read-only, allowlist tabel/kolom, timeout, dan validasi query.
- Dokumen dari RAG adalah data tidak tepercaya, bukan instruksi.
- Hardening production, TLS, rate limiting login, audit log, pencabutan token, backup, dan observability masih perlu dikerjakan.

## Tahapan implementasi

1. Fondasi repository, Docker, health checks, dan CI.
2. Skema metadata dokumen serta pgvector.
3. Pipeline ingest dokumen, chunking, embedding, dan retrieval.
4. Enkripsi file AES-256-GCM dan pengujian dasar.
5. OCR PaddleOCR opsional untuk PDF scan/gambar; benchmark CPU/RAM masih diperlukan.
6. JWT dan RBAC baseline; perlu pengujian keamanan tambahan dan rate limiting.
7. Adapter webhook n8n tersedia; workflow chat n8n, pengujian end-to-end, dan pembatasan tool masih perlu dikonfigurasi.
8. Enkripsi metadata database, backup/restore, monitoring, CI/CD registry, dan deployment VPS Ubuntu dengan Nginx/TLS/firewall.

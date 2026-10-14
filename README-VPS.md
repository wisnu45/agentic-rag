# README-VPS.md — Panduan DevOps Agentic RAG di VPS Ubuntu

Dokumen ini merupakan rancangan dan runbook deployment untuk repository wisnu45/agentic-rag. Panduan ini belum berarti deployment telah dilakukan. Jalankan setiap tahap secara berurutan dan verifikasi hasilnya.

## 1. Arsitektur target

```text
Pengguna
  | HTTPS :443
  v
Nginx host (reverse proxy + TLS)
  | HTTP ke loopback
  v
Frontend container (127.0.0.1:8080)
  | /api/*
  v
FastAPI container (127.0.0.1:8000)
  | SQL                    | HTTP API
  v                        v
PostgreSQL + pgvector     Ollama (idealnya host inference terpisah/private network)
                             |
                             +-- n8n opsional, webhook terautentikasi
```

Compose saat ini memublikasikan PostgreSQL, backend, dan frontend hanya ke loopback VPS. Jangan membuka port 5432, 8000, 8080, atau 11434 ke internet. Nginx publik hanya menerima HTTP/HTTPS.

### Kapasitas VPS

- VPS 2 vCPU/4 GB RAM dapat menjadi titik awal untuk aplikasi ringan, tetapi RAM harus dipantau.
- Jangan menganggap VPS kecil tersebut memadai untuk Ollama, PostgreSQL, API, dan OCR secara bersamaan. Jalankan Ollama di mesin inference terpisah melalui VPN/jaringan privat atau tingkatkan sumber daya setelah pengujian beban.
- OCR PaddleOCR nonaktif pada deployment awal. Aktifkan hanya setelah benchmark.
- Model default: qwen2.5:3b untuk chat dan nomic-embed-text untuk embedding 768 dimensi.

## 2. Prasyarat

Siapkan:
- IP publik VPS dan akses SSH dengan akun non-root yang memiliki sudo.
- Domain/subdomain yang mengarah ke IP VPS.
- Ubuntu yang didukung Docker Engine dan Docker Compose plugin.
- Repository GitHub, secret aplikasi, URL Ollama privat, serta strategi backup di luar VPS.

Contoh di dokumen ini menggunakan domain rag.example.com dan direktori /opt/agentic-rag. Ganti sesuai lingkungan sebenarnya.

## 3. Siapkan Ubuntu dan firewall

Login:

```bash
ssh <user>@<IP_VPS>
sudo apt update
sudo apt upgrade -y
sudo apt install -y ca-certificates curl git gnupg ufw unattended-upgrades
```

Tambahkan SSH sebelum mengaktifkan firewall. Sesuaikan port SSH bila bukan 22:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw status
sudo ufw enable
```

Jangan buka port publik 5432, 8000, 8080, atau 11434. Gunakan SSH tunnel atau jaringan privat untuk administrasi database.

## 4. Instal Docker

Ikuti dokumentasi resmi Docker untuk menginstal Docker Engine dan Compose plugin pada versi Ubuntu VPS. Lalu verifikasi:

```bash
sudo systemctl enable --now docker
sudo docker version
sudo docker compose version
```

Keanggotaan grup docker memberi hak istimewa tinggi yang pada praktiknya setara root. Berikan akses hanya kepada administrator tepercaya.

## 5. Clone repository

```bash
sudo mkdir -p /opt/agentic-rag
sudo chown "$USER":"$USER" /opt/agentic-rag
git clone https://github.com/wisnu45/agentic-rag.git /opt/agentic-rag
cd /opt/agentic-rag
```

Untuk update, periksa status CI dan perubahan terlebih dahulu, lalu gunakan git pull --ff-only dari branch yang disetujui.

## 6. Konfigurasi environment produksi

```bash
cp .env.example .env
chmod 600 .env
nano .env
```

Buat secret unik. Jangan commit atau membagikan file .env.

JWT secret:

```bash
openssl rand -hex 32
```

Key enkripsi file URL-safe Base64 32 byte:

```bash
python3 -c 'import secrets,base64; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())'
```

Buat password PostgreSQL dan webhook secret secara terpisah. Atur nilai minimal berikut pada .env:

```dotenv
APP_ENV=production
APP_NAME=Agentic RAG
POSTGRES_DB=agentic_rag
POSTGRES_USER=agentic_rag_app
POSTGRES_PASSWORD=<PASSWORD_POSTGRES_ACAK>
JWT_SECRET_KEY=<SECRET_JWT_ACAK_MINIMAL_32_KARAKTER>
FILE_ENCRYPTION_KEY=<KEY_URLSAFE_BASE64_32_BYTE>
JWT_ACCESS_TOKEN_MINUTES=30
OLLAMA_BASE_URL=http://<HOST_OLLAMA_PRIVAT>:11434
OLLAMA_LLM_MODEL=qwen2.5:3b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
INSTALL_OCR=false
CORS_ORIGINS=https://rag.example.com
N8N_CHAT_WEBHOOK_URL=
N8N_WEBHOOK_SECRET=
N8N_TIMEOUT_SECONDS=90
MAX_UPLOAD_SIZE_MB=20
CHUNK_SIZE=1000
CHUNK_OVERLAP=150
```

Ganti seluruh placeholder. Jangan biarkan nilai contoh seperti change_me_local_only atau REPLACE_WITH pada konfigurasi produksi. Gunakan password database alfanumerik agar URL yang dibentuk Compose tidak bermasalah dengan URL encoding. Pastikan OLLAMA_BASE_URL dapat dijangkau dari container backend; localhost di dalam container menunjuk ke container itu sendiri.

Cadangkan FILE_ENCRYPTION_KEY secara aman dan terpisah. Jika key hilang, file terenkripsi tidak dapat dipulihkan. Jangan mengganti key setelah dokumen tersimpan tanpa prosedur re-enkripsi.

## 7. Siapkan Ollama

Disarankan menjalankan Ollama pada mesin inference terpisah yang dapat dijangkau melalui VPN/jaringan privat. Jangan mengekspos port 11434 ke seluruh internet.

Pada host Ollama:

```bash
ollama pull qwen2.5:3b
ollama pull nomic-embed-text
ollama list
```

Uji konektivitas dari VPS:

```bash
curl --fail --silent --show-error http://<HOST_OLLAMA_PRIVAT>:11434/api/tags
```

Jika Ollama hanya bind ke localhost di mesin lain, VPS tidak akan dapat mengaksesnya. Atur akses jaringan secara eksplisit dan batasi dengan VPN/firewall.

Jika memakai n8n, impor n8n/workflows/agentic-rag-ollama.json, atur credential Header Auth dengan nama header X-Agentic-RAG-Webhook-Secret dan nilai yang sama dengan N8N_WEBHOOK_SECRET, lalu aktifkan workflow. Isi N8N_CHAT_WEBHOOK_URL dengan URL webhook produksi. Pastikan n8n juga dapat menjangkau Ollama dengan aman.

## 8. Build dan jalankan Docker Compose

```bash
cd /opt/agentic-rag
sudo docker compose config --quiet
sudo docker compose build
sudo docker compose up -d
sudo docker compose ps
```

Jika config gagal, perbaiki variabel yang hilang sebelum melanjutkan. Periksa log:

```bash
sudo docker compose logs --tail=150 postgres
sudo docker compose logs --tail=150 backend
sudo docker compose logs --tail=150 frontend
```

Compose yang ada menggunakan port host loopback:
- Frontend: 127.0.0.1:8080
- Backend: 127.0.0.1:8000
- PostgreSQL: 127.0.0.1:5432

Smoke test lokal:

```bash
curl --fail http://127.0.0.1:8080/
curl --fail http://127.0.0.1:8000/health
curl --fail http://127.0.0.1:8000/health/ready
```

Jangan lanjut ke konfigurasi TLS sebelum health check lokal lulus. Jika readiness gagal, periksa log PostgreSQL/backend, password/environment, dan inisialisasi pgvector/tabel.

Catatan database: repository memiliki backend/init_db.py untuk membuat extension dan tabel berdasarkan ORM. Pastikan inisialisasi yang diperlukan benar-benar dijalankan. Jangan menjalankan skema SQL manual dan inisialisasi ORM tanpa memahami bahwa keduanya menyasar tabel yang sama. Untuk database existing, backup dan tinjau perubahan skema terlebih dahulu.

## 9. Konfigurasi Nginx host

Frontend container sudah memiliki Nginx yang meneruskan /api/* ke backend. Nginx host meneruskan trafik publik ke 127.0.0.1:8080.

```bash
sudo apt install -y nginx
sudo systemctl enable --now nginx
```

Buat /etc/nginx/sites-available/agentic-rag:

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name rag.example.com;
    client_max_body_size 20m;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 180s;
        proxy_send_timeout 180s;
    }
}
```

Ganti domain dengan domain milik sendiri, lalu aktifkan:

```bash
sudo ln -s /etc/nginx/sites-available/agentic-rag /etc/nginx/sites-enabled/agentic-rag
sudo nginx -t
sudo systemctl reload nginx
```

Pastikan DNS mengarah ke VPS. Bila ada record AAAA, pastikan IPv6 memang dikonfigurasi dengan benar.

## 10. Aktifkan HTTPS

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d rag.example.com
sudo certbot renew --dry-run
curl --fail --head https://rag.example.com/
```

Ikuti prompt Certbot dan gunakan email operasional. Pastikan redirect HTTP ke HTTPS, sertifikat valid, dan pembaruan otomatis berhasil.

## 11. Buat akun admin

Jangan memasukkan password plaintext melalui SQL. Gunakan provisioning CLI yang tersedia pada backend/create_user.py. Periksa petunjuk dan argumen aktual file tersebut terlebih dahulu; jangan menebak argumen command. Pastikan CLI menggunakan DATABASE_URL deployment yang sama. Setelah akun dibuat, uji login dan endpoint /api/auth/me.

## 12. Smoke test penerimaan

- [ ] Container berjalan stabil setelah start/restart.
- [ ] /health merespons sukses dan /health/ready mengonfirmasi database.
- [ ] Situs tersedia melalui HTTPS.
- [ ] Login menghasilkan JWT dan role benar.
- [ ] Endpoint privat menolak request tanpa token.
- [ ] Admin/editor dapat mengunggah TXT/Markdown/PDF/DOCX yang valid.
- [ ] File asli disimpan terenkripsi dan metadata dokumen tersimpan.
- [ ] Chunk serta embedding 768 dimensi tersimpan di PostgreSQL + pgvector.
- [ ] Pencarian vektor menemukan sumber relevan.
- [ ] Ollama menjawab berdasarkan sumber dan memberi referensi yang valid.
- [ ] Pertanyaan yang tidak didukung dokumen menghasilkan jawaban bahwa informasi tidak cukup.
- [ ] Jika n8n dipakai, autentikasi webhook dan generation diuji nyata.
- [ ] Port database, API, frontend internal, dan Ollama tidak terbuka ke internet.
- [ ] Backup dan restore diuji pada lingkungan aman.

CI GitHub tidak menggantikan smoke test VPS dengan layanan nyata.

## 13. Backup dan pemulihan

Buat direktori dengan akses terbatas:

```bash
sudo install -d -m 700 /var/backups/agentic-rag
```

Backup database:

```bash
sudo docker compose exec -T postgres pg_dump -U agentic_rag_app -d agentic_rag -Fc > /var/backups/agentic-rag/db-$(date +%F-%H%M).dump
```

Backup file storage:

```bash
sudo tar -czf /var/backups/agentic-rag/storage-$(date +%F-%H%M).tar.gz storage/uploads storage/processed
sudo chmod 600 /var/backups/agentic-rag/*
```

Simpan backup di luar VPS juga. Backup file dapat berisi data sensitif. Cadangkan key enkripsi secara terpisah. Jangan menganggap backup berhasil sampai restore diuji.

Contoh restore ke database uji kosong (ganti nama file sesuai backup yang tersedia):

```bash
sudo docker compose exec -T postgres createdb -U agentic_rag_app agentic_rag_restore_test
sudo docker compose exec -T postgres pg_restore -U agentic_rag_app -d agentic_rag_restore_test --clean --if-exists < /var/backups/agentic-rag/db-YYYY-MM-DD-HHMM.dump
```

Pastikan target adalah database uji, bukan database produksi.

## 14. Prosedur rilis dan rollback

1. Periksa CI pada commit yang akan dirilis.
2. Backup database dan storage.
3. Catat commit aktif dengan git rev-parse HEAD.
4. Tinjau perubahan aplikasi, skema, dan environment.
5. Ambil commit yang disetujui menggunakan git pull --ff-only.
6. Jalankan docker compose config --quiet.
7. Build dengan docker compose build.
8. Terapkan dengan docker compose up -d.
9. Jalankan seluruh smoke test dan tinjau log.
10. Jika gagal, simpan log dan rollback sesuai prosedur yang telah diuji.

Mengembalikan image lama tidak selalu cukup bila skema database telah berubah. Jangan gunakan docker compose down -v pada produksi karena dapat menghapus volume database.

## 15. Monitoring dan troubleshooting

```bash
sudo docker compose ps
sudo docker compose logs --since=30m backend
sudo docker compose logs --since=30m postgres
sudo docker compose logs --since=30m frontend
free -h
df -h
uptime
sudo nginx -t
sudo systemctl status nginx
```

| Gejala | Pemeriksaan awal |
|---|---|
| 502 Bad Gateway | Nginx host, frontend container, port loopback 8080 |
| API tidak tersedia | Log backend, readiness DB, konfigurasi API |
| Database tidak siap | Password/environment, disk, status container, pgvector |
| Embedding gagal | URL Ollama, model embedding, jaringan privat, dimensi 768 |
| LLM timeout | RAM/CPU host Ollama, model, timeout backend/n8n |
| Upload ditolak | Ekstensi, ukuran file, role, batas Nginx |
| Disk penuh | Storage, log, backup; jangan menghapus dokumen tanpa prosedur |
| TLS gagal | DNS, port 80/443, waktu sistem, Certbot |

## 16. Hardening keamanan

- Gunakan SSH key dan nonaktifkan login root/password hanya setelah akses key teruji.
- Jangan expose port database/API/Ollama ke publik.
- Simpan secret di luar Git; gunakan secret unik untuk setiap fungsi.
- Aktifkan log rotation, monitoring disk/RAM, backup terenkripsi, dan restore drill.
- Evaluasi enkripsi metadata/teks chunk di database. Saat ini file asli dienkripsi, tetapi metadata dan teks chunk di PostgreSQL belum dienkripsi pada level aplikasi.
- Evaluasi rate limiting, ukuran request, CORS, akses dokumentasi API, audit log, dan kebijakan retensi data sebelum publik.
- Jangan aktifkan OCR di VPS kecil sebelum benchmark.
- Jangan memberi agent akses shell, file system, atau SQL write.

## 17. Definition of Done

Deployment baru dinyatakan selesai setelah:
1. Domain HTTPS dan redirect telah diverifikasi.
2. Container stabil setelah restart.
3. Login/RBAC dan upload telah diuji.
4. Dokumen diproses dan embedding tersimpan di pgvector.
5. Retrieval dan jawaban Ollama berjalan dengan layanan nyata.
6. n8n diuji bila digunakan, atau jalur Ollama langsung telah tervalidasi.
7. Port internal tidak terbuka ke internet.
8. Backup database, file, dan key memiliki prosedur pemulihan yang telah diuji.
9. Monitoring, update, rollback, dan hasil smoke test tercatat.

## Referensi repository

- Repository: https://github.com/wisnu45/agentic-rag
- Docker Compose: https://github.com/wisnu45/agentic-rag/blob/main/docker-compose.yml
- Environment template: https://github.com/wisnu45/agentic-rag/blob/main/.env.example
- SQL schema: https://github.com/wisnu45/agentic-rag/blob/main/database/schema.sql
- n8n workflow: https://github.com/wisnu45/agentic-rag/blob/main/n8n/workflows/agentic-rag-ollama.json
- CI: https://github.com/wisnu45/agentic-rag/blob/main/.github/workflows/ci.yml

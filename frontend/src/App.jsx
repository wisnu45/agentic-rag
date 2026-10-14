import { useEffect, useState } from "react";
import { getHealth, searchDocuments, uploadDocument } from "./services/api";

export default function App() {
  const [apiStatus, setApiStatus] = useState("checking");
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [uploadError, setUploadError] = useState("");
  const [query, setQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [searchResults, setSearchResults] = useState(null);
  const [searchError, setSearchError] = useState("");

  useEffect(() => {
    getHealth().then(() => setApiStatus("online")).catch(() => setApiStatus("offline"));
  }, []);

  async function handleUpload(event) {
    event.preventDefault();
    if (!file || uploading) return;
    setUploading(true);
    setUploadError("");
    setUploadResult(null);
    try {
      const data = await uploadDocument(file);
      setUploadResult(data);
      setFile(null);
      event.currentTarget.reset();
    } catch (err) {
      setUploadError(err?.response?.data?.detail || "Upload gagal. Pastikan API, database, dan Ollama tersedia.");
    } finally {
      setUploading(false);
    }
  }

  async function handleSearch(event) {
    event.preventDefault();
    if (!query.trim() || searching) return;
    setSearching(true);
    setSearchError("");
    setSearchResults(null);
    try {
      const data = await searchDocuments(query.trim());
      setSearchResults(data.results);
    } catch (err) {
      setSearchError(err?.response?.data?.detail || "Pencarian gagal. Pastikan schema database dan Ollama tersedia.");
    } finally {
      setSearching(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto flex min-h-screen max-w-5xl flex-col px-5 py-8">
        <header className="flex items-center justify-between border-b border-slate-800 pb-5">
          <div>
            <p className="text-sm font-medium tracking-wide text-cyan-400">LOCAL AI WORKSPACE</p>
            <h1 className="mt-1 text-2xl font-semibold">Agentic RAG Assistant</h1>
          </div>
          <span className={`rounded-full px-3 py-1 text-xs ${apiStatus === "online" ? "bg-emerald-950 text-emerald-300" : apiStatus === "offline" ? "bg-rose-950 text-rose-300" : "bg-slate-800 text-slate-300"}`}>
            API: {apiStatus}
          </span>
        </header>

        <section className="grid flex-1 content-center gap-6 py-10 lg:grid-cols-2">
          <form onSubmit={handleUpload} className="h-fit rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
            <h2 className="font-semibold">1. Upload dokumen</h2>
            <p className="mt-1 text-xs text-slate-400">TXT, MD, PDF berbasis teks, DOCX · maksimal 20 MB</p>
            <label htmlFor="document-file" className="mt-5 flex cursor-pointer flex-col items-center rounded-xl border border-dashed border-slate-700 bg-slate-950/60 px-4 py-8 text-center hover:border-cyan-700">
              <span className="text-sm font-medium">{file ? file.name : "Pilih dokumen dari perangkat"}</span>
              <span className="mt-1 text-xs text-slate-500">File akan diekstrak, di-chunk, dan di-embedding</span>
            </label>
            <input id="document-file" type="file" accept=".txt,.md,.pdf,.docx" className="sr-only" onChange={(event) => {
              setFile(event.target.files?.[0] || null);
              setUploadResult(null);
              setUploadError("");
            }} />
            <button type="submit" disabled={!file || uploading || apiStatus === "offline"} className="mt-4 w-full rounded-lg bg-cyan-500 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-40">
              {uploading ? "Memproses dokumen..." : "Upload dan indeks"}
            </button>
            {uploadError && <p role="alert" className="mt-4 rounded-lg border border-rose-900 bg-rose-950/50 p-3 text-sm text-rose-300">{uploadError}</p>}
            {uploadResult && <div role="status" className="mt-4 rounded-lg border border-emerald-900 bg-emerald-950/40 p-3 text-sm">
              <p className="font-medium text-emerald-300">Dokumen berhasil diindeks</p>
              <p className="mt-1 text-slate-300">{uploadResult.filename}</p>
              <p className="mt-1 text-xs text-slate-400">Status: {uploadResult.status} · Chunk: {uploadResult.chunks_created}</p>
            </div>}
            <p className="mt-4 text-xs leading-5 text-slate-500">PDF hasil scan belum didukung. Database dan Ollama harus aktif.</p>
          </form>

          <form onSubmit={handleSearch} className="h-fit rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
            <h2 className="font-semibold">2. Cari dalam dokumen</h2>
            <p className="mt-1 text-xs text-slate-400">Pencarian semantik menggunakan embedding dan pgvector.</p>
            <label htmlFor="search-query" className="mt-5 block text-sm text-slate-300">Pertanyaan atau kata kunci</label>
            <textarea id="search-query" value={query} onChange={(event) => setQuery(event.target.value)} rows={3} maxLength={5000} placeholder="Contoh: Apa kebijakan keamanan yang disebutkan?" className="mt-2 w-full resize-y rounded-xl border border-slate-700 bg-slate-950 p-3 text-sm outline-none focus:border-cyan-600" />
            <button type="submit" disabled={!query.trim() || searching || apiStatus === "offline"} className="mt-3 w-full rounded-lg border border-cyan-800 bg-cyan-950/50 px-4 py-3 text-sm font-semibold text-cyan-200 hover:bg-cyan-900/50 disabled:cursor-not-allowed disabled:opacity-40">
              {searching ? "Mencari..." : "Cari dokumen"}
            </button>
            {searchError && <p role="alert" className="mt-4 rounded-lg border border-rose-900 bg-rose-950/50 p-3 text-sm text-rose-300">{searchError}</p>}
            {searchResults && <div className="mt-4 space-y-3">
              <p className="text-xs text-slate-400">Ditemukan {searchResults.length} hasil terdekat.</p>
              {searchResults.length === 0 && <p className="rounded-lg bg-slate-950 p-3 text-sm text-slate-400">Belum ada dokumen terindeks yang cocok.</p>}
              {searchResults.map((item) => <article key={item.document_id + "-" + item.chunk_index} className="rounded-xl border border-slate-800 bg-slate-950/70 p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-sm font-medium text-cyan-200">{item.filename}</p>
                  <span className="text-xs text-slate-500">Similarity: {item.score.toFixed(3)}</span>
                </div>
                <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-300">{item.content}</p>
                <p className="mt-2 text-xs text-slate-500">Chunk {item.chunk_index + 1}{item.page_number ? " · Halaman " + item.page_number : ""}</p>
              </article>)}
            </div>}
            <p className="mt-4 text-xs leading-5 text-slate-500">Ini retrieval semantik, belum jawaban generatif dari LLM. Skor similarity bukan probabilitas.</p>
          </form>
        </section>
        <footer className="border-t border-slate-800 pt-4 text-xs text-slate-500">
          MVP • React + FastAPI • PostgreSQL + pgvector • Ollama
        </footer>
      </div>
    </main>
  );
}

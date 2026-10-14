import { useEffect, useState } from "react";
import { askQuestion, getHealth, uploadDocument } from "./services/api";

export default function App() {
  const [apiStatus, setApiStatus] = useState("checking");
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [uploadError, setUploadError] = useState("");
  const [query, setQuery] = useState("");
  const [asking, setAsking] = useState(false);
  const [chatResponse, setChatResponse] = useState(null);
  const [chatError, setChatError] = useState("");

  useEffect(() => {
    getHealth().then(() => setApiStatus("online")).catch(() => setApiStatus("offline"));
  }, []);

  async function handleUpload(event) {
    event.preventDefault();
    const form = event.currentTarget;
    if (!file || uploading) return;
    setUploading(true);
    setUploadError("");
    setUploadResult(null);
    try {
      const data = await uploadDocument(file);
      setUploadResult(data);
      setFile(null);
      form.reset();
    } catch (err) {
      setUploadError(err?.response?.data?.detail || "Upload gagal. Pastikan API, database, dan Ollama tersedia.");
    } finally {
      setUploading(false);
    }
  }

  async function handleAsk(event) {
    event.preventDefault();
    if (!query.trim() || asking) return;
    setAsking(true);
    setChatError("");
    setChatResponse(null);
    try {
      const data = await askQuestion(query.trim());
      setChatResponse(data);
    } catch (err) {
      setChatError(err?.response?.data?.detail || "Pertanyaan gagal diproses. Pastikan schema database dan model Ollama tersedia.");
    } finally {
      setAsking(false);
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
            <p className="mt-1 text-xs text-slate-400">TXT, MD, PDF, DOCX, JPG/PNG/TIFF/BMP · maksimal 20 MB</p>
            <label htmlFor="document-file" className="mt-5 flex cursor-pointer flex-col items-center rounded-xl border border-dashed border-slate-700 bg-slate-950/60 px-4 py-8 text-center hover:border-cyan-700">
              <span className="text-sm font-medium">{file ? file.name : "Pilih dokumen dari perangkat"}</span>
              <span className="mt-1 text-xs text-slate-500">File akan diekstrak, di-chunk, dan di-embedding</span>
            </label>
            <input id="document-file" type="file" accept=".txt,.md,.pdf,.docx,.png,.jpg,.jpeg,.tif,.tiff,.bmp" className="sr-only" onChange={(event) => {
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
            <p className="mt-4 text-xs leading-5 text-slate-500">OCR untuk PDF scan/gambar memerlukan dependensi PaddleOCR opsional. Database dan Ollama harus aktif.</p>
          </form>

          <form onSubmit={handleAsk} className="h-fit rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
            <h2 className="font-semibold">2. Tanya dokumen (RAG)</h2>
            <p className="mt-1 text-xs text-slate-400">Jawaban dirangkai oleh LLM berdasarkan chunk yang paling relevan.</p>
            <label htmlFor="question" className="mt-5 block text-sm text-slate-300">Pertanyaan</label>
            <textarea id="question" value={query} onChange={(event) => setQuery(event.target.value)} rows={3} maxLength={10000} placeholder="Contoh: Apa kebijakan keamanan yang disebutkan?" className="mt-2 w-full resize-y rounded-xl border border-slate-700 bg-slate-950 p-3 text-sm outline-none focus:border-cyan-600" />
            <button type="submit" disabled={!query.trim() || asking || apiStatus === "offline"} className="mt-3 w-full rounded-lg border border-cyan-800 bg-cyan-950/50 px-4 py-3 text-sm font-semibold text-cyan-200 hover:bg-cyan-900/50 disabled:cursor-not-allowed disabled:opacity-40">
              {asking ? "Menyusun jawaban..." : "Tanyakan"}
            </button>
            {chatError && <p role="alert" className="mt-4 rounded-lg border border-rose-900 bg-rose-950/50 p-3 text-sm text-rose-300">{chatError}</p>}
            {chatResponse && <div className="mt-4 space-y-3">
              <article className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
                <p className="text-xs font-semibold uppercase tracking-wide text-cyan-300">Jawaban</p>
                <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-200">{chatResponse.answer}</p>
              </article>
              <div>
                <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">Sumber yang diambil</p>
                {chatResponse.sources.length === 0 && <p className="text-sm text-slate-500">Belum ada sumber dokumen yang terindeks.</p>}
                {chatResponse.sources.map((source) => <div key={source.source_id} className="mb-2 rounded-lg border border-slate-800 p-3 text-xs">
                  <p className="font-medium text-cyan-200">[{source.source_id}] {source.filename}</p>
                  <p className="mt-1 text-slate-500">Halaman: {source.page} · Chunk: {Number(source.chunk_index) + 1}</p>
                </div>)}
              </div>
            </div>}
            <p className="mt-4 text-xs leading-5 text-slate-500">Model diminta mengutip penanda sumber seperti [S1]. Verifikasi jawaban terhadap dokumen asli untuk penggunaan penting.</p>
          </form>
        </section>
        <footer className="border-t border-slate-800 pt-4 text-xs text-slate-500">
          MVP • React + FastAPI • PostgreSQL + pgvector • Ollama • OCR opsional
        </footer>
      </div>
    </main>
  );
}

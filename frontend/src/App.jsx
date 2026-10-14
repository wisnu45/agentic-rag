import { useEffect, useState } from "react";
import { getHealth, uploadDocument } from "./services/api";

export default function App() {
  const [apiStatus, setApiStatus] = useState("checking");
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getHealth().then(() => setApiStatus("online")).catch(() => setApiStatus("offline"));
  }, []);

  async function handleUpload(event) {
    event.preventDefault();
    if (!file || uploading) return;
    setUploading(true);
    setError("");
    setResult(null);
    try {
      const data = await uploadDocument(file);
      setResult(data);
      setFile(null);
      event.currentTarget.reset();
    } catch (err) {
      setError(err?.response?.data?.detail || "Upload gagal. Pastikan API, database, dan Ollama tersedia.");
    } finally {
      setUploading(false);
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

        <section className="grid flex-1 content-center gap-8 py-10 lg:grid-cols-[1.05fr_0.95fr]">
          <div className="flex flex-col justify-center">
            <div className="mb-5 flex h-16 w-16 items-center justify-center rounded-2xl border border-cyan-900 bg-cyan-950/50 text-2xl">✦</div>
            <h2 className="text-3xl font-semibold tracking-tight">Knowledge, connected.</h2>
            <p className="mt-3 max-w-xl text-sm leading-6 text-slate-400">
              Unggah dokumen untuk diekstrak, dipecah menjadi chunk, dan disimpan sebagai embedding
              agar siap digunakan pada tahap retrieval berikutnya.
            </p>
            <div className="mt-6 grid gap-3 sm:grid-cols-3">
              {[
                ["01", "Document RAG", "Pipeline dokumen awal"],
                ["02", "Vector Store", "PostgreSQL + pgvector"],
                ["03", "Local LLM", "Embedding via Ollama"],
              ].map(([number, title, description]) => (
                <article key={number} className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
                  <span className="text-xs text-cyan-400">{number}</span>
                  <h3 className="mt-3 text-sm font-medium">{title}</h3>
                  <p className="mt-1 text-xs leading-5 text-slate-400">{description}</p>
                </article>
              ))}
            </div>
          </div>

          <form onSubmit={handleUpload} className="h-fit rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
            <h3 className="font-semibold">Upload dokumen</h3>
            <p className="mt-1 text-xs text-slate-400">TXT, MD, PDF berbasis teks, DOCX · maksimal 20 MB</p>
            <label htmlFor="document-file" className="mt-5 flex cursor-pointer flex-col items-center rounded-xl border border-dashed border-slate-700 bg-slate-950/60 px-4 py-8 text-center hover:border-cyan-700">
              <span className="text-sm font-medium">{file ? file.name : "Pilih dokumen dari perangkat"}</span>
              <span className="mt-1 text-xs text-slate-500">Pilih file untuk mulai ingest</span>
            </label>
            <input id="document-file" type="file" accept=".txt,.md,.pdf,.docx" className="sr-only" onChange={(event) => {
              setFile(event.target.files?.[0] || null);
              setResult(null);
              setError("");
            }} />
            <button type="submit" disabled={!file || uploading || apiStatus === "offline"} className="mt-4 w-full rounded-lg bg-cyan-500 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-40">
              {uploading ? "Memproses dokumen..." : "Upload dan proses"}
            </button>
            {error && <p role="alert" className="mt-4 rounded-lg border border-rose-900 bg-rose-950/50 p-3 text-sm text-rose-300">{error}</p>}
            {result && <div role="status" className="mt-4 rounded-lg border border-emerald-900 bg-emerald-950/40 p-3 text-sm">
              <p className="font-medium text-emerald-300">Dokumen berhasil diindeks</p>
              <p className="mt-1 text-slate-300">{result.filename}</p>
              <p className="mt-1 text-xs text-slate-400">Status: {result.status} · Chunk: {result.chunks_created}</p>
              <p className="mt-2 break-all text-xs text-slate-500">ID: {result.document_id}</p>
            </div>}
            <p className="mt-4 text-xs leading-5 text-slate-500">
              PDF hasil scan belum didukung. Database dan Ollama harus aktif untuk membuat embedding.
            </p>
          </form>
        </section>
        <footer className="border-t border-slate-800 pt-4 text-xs text-slate-500">
          MVP • React + FastAPI • PostgreSQL + pgvector • Ollama
        </footer>
      </div>
    </main>
  );
}

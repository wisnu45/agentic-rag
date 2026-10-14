import { useEffect, useState } from "react";
import { getHealth } from "./services/api";

export default function App() {
  const [apiStatus, setApiStatus] = useState("checking");

  useEffect(() => {
    getHealth()
      .then(() => setApiStatus("online"))
      .catch(() => setApiStatus("offline"));
  }, []);

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

        <section className="flex flex-1 flex-col items-center justify-center text-center">
          <div className="mb-5 flex h-16 w-16 items-center justify-center rounded-2xl border border-cyan-900 bg-cyan-950/50 text-2xl">✦</div>
          <h2 className="text-3xl font-semibold tracking-tight">Knowledge, connected.</h2>
          <p className="mt-3 max-w-xl text-sm leading-6 text-slate-400">
            Fondasi antarmuka sudah tersedia. Tahap berikutnya akan menghubungkan chat,
            upload dokumen, retrieval dari pgvector, OCR, dan Ollama.
          </p>
          <div className="mt-8 grid w-full max-w-2xl gap-3 text-left sm:grid-cols-3">
            {[
              ["01", "Document RAG", "Pencarian konteks dokumen"],
              ["02", "Image OCR", "Ekstraksi teks gambar"],
              ["03", "SQL Tool", "Akses data terstruktur terkontrol"],
            ].map(([number, title, description]) => (
              <article key={number} className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
                <span className="text-xs text-cyan-400">{number}</span>
                <h3 className="mt-3 font-medium">{title}</h3>
                <p className="mt-1 text-xs leading-5 text-slate-400">{description}</p>
              </article>
            ))}
          </div>
        </section>

        <footer className="border-t border-slate-800 pt-4 text-xs text-slate-500">
          MVP development • Vite + React • FastAPI • PostgreSQL + pgvector
        </footer>
      </div>
    </main>
  );
}

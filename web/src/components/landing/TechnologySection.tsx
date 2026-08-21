import {
  Bot,
  BrainCircuit,
  Cpu,
  Database,
  Mic,
  Network,
  ShieldCheck,
} from "lucide-react";

export function TechnologySection() {
  const techStack = [
    {
      category: "SPEECH-TO-TEXT",
      name: "Sarvam AI (Saaras)",
      role: "Acoustic Speech Recognition",
      description:
        "High-fidelity voice transcription optimized specifically for Indian languages, accents, and bilingual English/Hindi speech streams.",
      specs: "16kHz Sampling · Sub-150ms Latency · Multilingual ASR",
      icon: Mic,
      tag: "sarvamai",
    },
    {
      category: "EMBEDDINGS",
      name: "Sentence Transformers",
      role: "Multilingual Semantic Vector Space",
      description:
        "Generates dense multilingual embeddings that map conceptually identical English and Hindi queries to shared geometrical spaces.",
      specs: "paraphrase-multilingual-MiniLM-L12-v2 · 384 Dim",
      icon: BrainCircuit,
      tag: "sentence-transformers",
    },
    {
      category: "VECTOR INDEX",
      name: "FAISS Vector Search",
      role: "Sub-50ms Approximate Nearest Neighbors",
      description:
        "Fast IndexFlatIP vector search indexed over 15,000+ bilingual passages from the MSMARCO-XI dataset.",
      specs: "faiss-cpu · Cosine Similarity · Memory-Mapped Reads",
      icon: Database,
      tag: "faiss-cpu",
    },
    {
      category: "GUARDRAILS & ATTRIBUTION",
      name: "N-Gram Grounding Engine",
      role: "Real-time Citation Verification",
      description:
        "Evaluates answer text against retrieved passage spans using exact and semantic token overlap to prevent unsupported hallucinations.",
      specs: "Confidence Scoring · Citation Extraction · Verification",
      icon: ShieldCheck,
      tag: "src/orchestration",
    },
    {
      category: "LLM REASONING",
      name: "Groq Cloud (Llama 3)",
      role: "Low-Latency Response Generation",
      description:
        "Leverages LPU hardware acceleration to synthesize grounded, multilingual answers with instantaneous token streaming.",
      specs: "Llama 3 · 300+ Tokens/sec · Low TTFT",
      icon: Bot,
      tag: "groq",
    },
    {
      category: "API RUNTIME",
      name: "FastAPI & Uvicorn",
      role: "Asynchronous High-Throughput Pipeline",
      description:
        "Clean decoupled service contracts with correlation tracking (X-Request-ID), timing headers (X-Process-Time-Ms), and health checks.",
      specs: "Pydantic V2 · Python 3.11+ · CORS Managed",
      icon: Cpu,
      tag: "fastapi",
    },
  ];

  return (
    <section id="technology" className="relative py-24 sm:py-32 border-t border-white/[0.06] bg-[#030405]">
      <div className="mx-auto max-w-5xl px-4 sm:px-6">
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-1.5 rounded-full border border-white/[0.08] bg-white/[0.02] px-3.5 py-1 text-[10px] font-mono tracking-widest text-zinc-400 uppercase">
            <span>● Architecture & Systems</span>
          </div>

          <h2 className="mt-6 text-3xl sm:text-5xl font-bold tracking-tight text-white leading-tight">
            Built as a{" "}
            <span className="font-normal text-zinc-400">complete retrieval system.</span>
          </h2>

          <p className="mt-4 text-base sm:text-lg text-zinc-400 leading-relaxed font-normal">
            Every component in Vaani is purpose-selected for high throughput, sub-second latency, and multilingual accuracy.
          </p>
        </div>

        {/* Architecture Pipeline Flow Diagram */}
        <div className="mt-14 rounded-2xl border border-white/[0.08] bg-[#090B0F] p-6 sm:p-8">
          <div className="text-xs font-mono text-zinc-500 uppercase tracking-wider pb-4 border-b border-white/[0.06] flex items-center justify-between">
            <span>End-to-End Execution Flow</span>
            <span className="text-zinc-300">Total Latency: &lt;500ms</span>
          </div>

          <div className="mt-6 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 text-center">
            {[
              { step: "1. Voice", sub: "WebM/WAV Stream", icon: Mic },
              { step: "2. Sarvam ASR", sub: "Hindi & English", icon: Network },
              { step: "3. Embeddings", sub: "MiniLM L12 (384d)", icon: BrainCircuit },
              { step: "4. FAISS Search", sub: "15k MSMARCO", icon: Database },
              { step: "5. Grounding", sub: "N-gram Verification", icon: ShieldCheck },
              { step: "6. Groq LLM", sub: "Grounded Answer", icon: Bot },
            ].map((node, i) => {
              const NodeIcon = node.icon;
              return (
                <div
                  key={i}
                  className="relative flex flex-col items-center justify-center rounded-xl border border-white/[0.06] bg-[#06080B] p-4 transition-colors hover:border-white/20"
                >
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg border border-white/10 bg-white/5 text-zinc-300 mb-2">
                    <NodeIcon className="h-4 w-4 stroke-[1.75]" />
                  </div>
                  <span className="text-xs font-semibold text-white tracking-tight">
                    {node.step}
                  </span>
                  <span className="text-[10px] font-mono text-zinc-500 mt-0.5">
                    {node.sub}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Tech Stack Cards Grid */}
        <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {techStack.map((tech, idx) => {
            const Icon = tech.icon;
            return (
              <div
                key={idx}
                className="group relative flex flex-col justify-between rounded-2xl border border-white/[0.06] bg-[#08090B] p-6 sm:p-7 transition-all duration-300 hover:border-white/20 hover:bg-[#0D1015]"
              >
                <div>
                  <div className="flex items-center justify-between">
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-white/10 bg-white/5 text-zinc-200">
                      <Icon className="h-4 w-4 stroke-[1.75]" />
                    </div>
                    <span className="rounded-md border border-white/[0.06] bg-white/[0.02] px-2 py-0.5 font-mono text-[10px] text-zinc-500">
                      {tech.tag}
                    </span>
                  </div>

                  <div className="mt-5 text-[10px] font-mono uppercase tracking-wider text-zinc-500">
                    {tech.category}
                  </div>

                  <h3 className="mt-1 text-base font-semibold text-white tracking-tight">
                    {tech.name}
                  </h3>

                  <p className="mt-2 text-xs text-zinc-400 leading-relaxed font-normal">
                    {tech.description}
                  </p>
                </div>

                <div className="mt-6 pt-3 border-t border-white/[0.04] font-mono text-[10px] text-zinc-500">
                  {tech.specs}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

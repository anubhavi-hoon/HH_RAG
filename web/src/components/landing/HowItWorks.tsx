import { useState } from "react";
import {
  Bot,
  BrainCircuit,
  Database,
  Mic,
  ShieldCheck,
} from "lucide-react";

export function HowItWorks() {
  const [activeStep, setActiveStep] = useState(0);

  const steps = [
    {
      num: "01",
      title: "SPEAK",
      label: "Natural Voice Capture",
      icon: Mic,
      tech: "Sarvam AI Acoustic ASR",
      summary:
        "Speak your query naturally in English or Hindi. Vaani streams browser audio to Sarvam AI STT, delivering accurate transcriptions regardless of regional cadence.",
      latency: "~140ms",
    },
    {
      num: "02",
      title: "UNDERSTAND",
      label: "Language & Query Parsing",
      icon: BrainCircuit,
      tech: "Multilingual Tokenizer & Router",
      summary:
        "The transcript is parsed, language-tagged (EN/HI), and prepared for semantic embedding, preserving nuanced technical terms across both languages.",
      latency: "~15ms",
    },
    {
      num: "03",
      title: "RETRIEVE",
      label: "Dense FAISS Vector Search",
      icon: Database,
      tech: "paraphrase-multilingual-MiniLM-L12-v2",
      summary:
        "The query embedding searches through 15,000+ indexed passages in the MSMARCO-XI bilingual corpus via FAISS, calculating precise cosine similarity scores.",
      latency: "~30ms",
    },
    {
      num: "04",
      title: "GROUND",
      label: "Guardrails & Verification",
      icon: ShieldCheck,
      tech: "N-Gram Citation & Overlap Engine",
      summary:
        "Retrieved chunks undergo strict relevance filtering. The engine verifies that every potential answer sentence is supported by extracted source spans.",
      latency: "~20ms",
    },
    {
      num: "05",
      title: "ANSWER",
      label: "Ultra-Fast LLM Synthesis",
      icon: Bot,
      tech: "Groq Cloud (Llama 3)",
      summary:
        "Groq accelerates generation at 300+ tokens/sec, producing an elegant, formatted, and strictly grounded response with inline citation tags.",
      latency: "~280ms",
    },
  ];

  return (
    <section id="how-it-works" className="relative py-24 sm:py-32 border-t border-white/[0.06] bg-[#050608]">
      <div className="mx-auto max-w-5xl px-4 sm:px-6">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-1.5 rounded-full border border-white/[0.08] bg-white/[0.02] px-3.5 py-1 text-[10px] font-mono tracking-widest text-zinc-400 uppercase">
            <span>● Pipeline Execution</span>
          </div>

          <h2 className="mt-6 text-3xl sm:text-5xl font-bold tracking-tight text-white leading-tight">
            From your voice to a{" "}
            <span className="font-normal text-zinc-400">grounded answer.</span>
          </h2>

          <p className="mt-4 text-base sm:text-lg text-zinc-400 leading-relaxed font-normal">
            A high-speed, verifiable retrieval pipeline engineered for multilingual fluency.
          </p>
        </div>

        {/* Step Navigation Pill Strip */}
        <div className="mt-14 flex items-center justify-start overflow-x-auto pb-3 sm:justify-center gap-2">
          {steps.map((step, idx) => {
            const Icon = step.icon;
            const isSelected = activeStep === idx;
            return (
              <button
                key={step.num}
                type="button"
                onClick={() => setActiveStep(idx)}
                className={`flex items-center gap-2 rounded-full px-4 py-2 text-xs font-semibold transition-all shrink-0 cursor-pointer ${
                  isSelected
                    ? "border border-white/20 bg-white/10 text-white"
                    : "border border-white/[0.06] bg-[#0A0D11] text-zinc-500 hover:border-white/15 hover:text-zinc-300"
                }`}
              >
                <span className="font-mono text-[10px] opacity-60">{step.num}</span>
                <Icon className="h-3.5 w-3.5 stroke-[1.75]" />
                <span>{step.title}</span>
              </button>
            );
          })}
        </div>

        {/* Active Step Showcase Card */}
        <div className="mt-6 rounded-2xl border border-white/[0.08] bg-[#090B0F] p-6 sm:p-9 shadow-2xl">
          <div className="grid gap-8 lg:grid-cols-12 items-center">
            {/* Left: Step Overview */}
            <div className="lg:col-span-7 space-y-4">
              <div className="flex items-center gap-3">
                <span className="flex h-9 w-9 items-center justify-center rounded-lg border border-white/15 bg-white/5 text-white font-semibold font-mono text-xs">
                  {steps[activeStep].num}
                </span>
                <div>
                  <h3 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
                    {steps[activeStep].title} · {steps[activeStep].label}
                  </h3>
                  <p className="text-xs font-mono text-zinc-400">
                    {steps[activeStep].tech}
                  </p>
                </div>
              </div>

              <p className="text-sm sm:text-base text-zinc-300 leading-relaxed pt-2 font-normal">
                {steps[activeStep].summary}
              </p>

              <div className="flex items-center gap-3 pt-2">
                <span className="rounded-full border border-white/[0.08] bg-white/[0.03] px-3 py-1 text-xs font-mono text-zinc-300">
                  Stage Latency: {steps[activeStep].latency}
                </span>
                <span className="text-xs text-zinc-500 font-mono">
                  Sub-500ms End-to-End
                </span>
              </div>
            </div>

            {/* Right: Pipeline Matrix */}
            <div className="lg:col-span-5 rounded-xl border border-white/[0.06] bg-[#06080B] p-4 space-y-2">
              <div className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider pb-2 border-b border-white/[0.06] flex items-center justify-between">
                <span>Stage Status</span>
                <span className="text-zinc-300">Stage {activeStep + 1} of 5</span>
              </div>

              {steps.map((st, i) => (
                <div
                  key={st.num}
                  onClick={() => setActiveStep(i)}
                  className={`flex items-center justify-between rounded-lg p-2.5 text-xs font-mono cursor-pointer transition-all ${
                    activeStep === i
                      ? "border border-white/15 bg-white/5 text-white font-semibold"
                      : "border border-transparent text-zinc-500 hover:text-zinc-300 hover:bg-white/[0.02]"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className={activeStep === i ? "text-white" : "text-zinc-600"}>
                      {st.num}
                    </span>
                    <span>{st.title}</span>
                  </div>
                  <span className="text-[11px] text-zinc-500">{st.latency}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

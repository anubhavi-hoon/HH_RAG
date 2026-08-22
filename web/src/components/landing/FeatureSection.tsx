import { FileSearch, Mic, ShieldCheck } from "lucide-react";

export function FeatureSection() {
  const features = [
    {
      icon: Mic,
      title: "Voice-First Interaction",
      tagline: "Acoustic Querying",
      description:
        "Ask questions naturally instead of translating your thoughts into rigid search keywords. Speak in English or Hindi with high-accuracy speech understanding.",
      badge: "Sarvam AI STT",
    },
    {
      icon: ShieldCheck,
      title: "Grounded Answers",
      tagline: "Factual Synthesis",
      description:
        "Responses are generated strictly from retrieved knowledge instead of relying on unsupported hallucination. Guardrails verify source alignment in real time.",
      badge: "Zero-Hallucination Focus",
    },
    {
      icon: FileSearch,
      title: "Transparent Evidence",
      tagline: "Full Provenance",
      description:
        "See the exact source passages, similarity scores, and retrieval context behind every statement. Never wonder where an insight originated.",
      badge: "Verifiable Citations",
    },
  ];

  return (
    <section id="product" className="relative py-24 sm:py-32">
      <div className="mx-auto max-w-5xl px-4 sm:px-6">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-1.5 rounded-full border border-white/[0.08] bg-white/[0.02] px-3.5 py-1 text-[10px] font-mono tracking-widest text-zinc-400 uppercase">
            <span>● Why Vaani</span>
          </div>

          <h2 className="mt-6 text-3xl sm:text-5xl font-bold tracking-tight text-white leading-tight">
            Knowledge should be{" "}
            <span className="font-normal text-zinc-400">easier to access.</span>
          </h2>

          <p className="mt-4 text-base sm:text-lg text-zinc-400 leading-relaxed font-normal">
            Vaani turns your knowledge base into a conversational interface you can speak to naturally.
          </p>
        </div>

        {/* 3 Premium Feature Cards */}
        <div className="mt-16 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((item, idx) => {
            const Icon = item.icon;
            return (
              <div
                key={idx}
                className="group relative flex flex-col justify-between rounded-2xl border border-white/[0.06] bg-[#08090B] p-7 sm:p-8 transition-all duration-300 hover:border-white/20 hover:bg-[#0D1015]"
              >
                <div>
                  {/* Icon */}
                  <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-zinc-200 group-hover:border-white/20 group-hover:text-white transition-colors">
                    <Icon className="h-5 w-5 stroke-[1.75]" />
                  </div>

                  {/* Tagline */}
                  <div className="mt-6 text-[10px] font-mono text-zinc-500 uppercase tracking-wider">
                    {item.tagline}
                  </div>

                  {/* Title */}
                  <h3 className="mt-1.5 text-lg font-semibold text-white tracking-tight">
                    {item.title}
                  </h3>

                  {/* Description */}
                  <p className="mt-3 text-sm text-zinc-400 leading-relaxed font-normal">
                    {item.description}
                  </p>
                </div>

                {/* Footer Micro-Badge */}
                <div className="mt-8 pt-4 border-t border-white/[0.04] flex items-center justify-between text-xs font-mono text-zinc-500">
                  <span>{item.badge}</span>
                  <span className="text-zinc-400 opacity-0 group-hover:opacity-100 transition-opacity">
                    →
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

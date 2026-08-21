import { useState } from "react";
import { Check, FileCheck, ShieldCheck } from "lucide-react";

export function GroundingSection() {
  const [selectedSource, setSelectedSource] = useState(0);

  const sources = [
    {
      id: "doc_msmarco_0831",
      strategy: "Sentence-aware semantic chunk (1200 char)",
      title: "Atmospheric CO2 Trapping & Radiative Forcing",
      similarity: "94.8%",
      score: 0.948,
      text: "Greenhouse gases trap infrared radiation escaping from Earth's surface. Carbon dioxide and methane absorb wavelengths in the 12-15 micrometer spectral window, creating radiative forcing that elevates surface equilibrium temperatures across oceanic and continental basins.",
    },
    {
      id: "doc_msmarco_1194",
      strategy: "Fixed-window chunk (1000 char, 150 overlap)",
      title: "Anthropogenic Combustion & Industrial Baseline",
      similarity: "91.2%",
      score: 0.912,
      text: "Fossil fuel combustion accounts for over 72% of global greenhouse emissions. Deforestation reduces biological carbon sink capacity, releasing stored carbon and reducing annual photosynthetic absorption rates.",
    },
    {
      id: "doc_msmarco_2041",
      strategy: "Sentence-aware semantic chunk (1200 char)",
      title: "Methane Emissive Pathways & Agricultural Heat Flux",
      similarity: "88.6%",
      score: 0.886,
      text: "Methane possesses a 28-fold higher global warming potential over a 100-year timescale relative to CO2. Agricultural livestock rumination and natural gas extraction leakage represent the primary non-fossil emissive vectors.",
    },
  ];

  return (
    <section id="grounding" className="relative py-24 sm:py-32 border-t border-white/[0.06] bg-[#050608]">
      <div className="mx-auto max-w-5xl px-4 sm:px-6">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-1.5 rounded-full border border-white/[0.08] bg-white/[0.02] px-3.5 py-1 text-[10px] font-mono tracking-widest text-zinc-400 uppercase">
            <span>● Zero Hallucination Architecture</span>
          </div>

          <h2 className="mt-6 text-3xl sm:text-5xl font-bold tracking-tight text-white leading-tight">
            Don't just trust the answer.{" "}
            <span className="font-normal text-zinc-400">See why.</span>
          </h2>

          <p className="mt-4 text-base sm:text-lg text-zinc-400 leading-relaxed font-normal">
            Vaani doesn't fabricate ungrounded answers. Every claim is linked directly to retrieved evidence with verifiable similarity scores and chunk provenance.
          </p>
        </div>

        {/* Evidence Verification Showcase */}
        <div className="mt-16 grid gap-6 lg:grid-cols-12 items-start">
          {/* Left Column: Grounded Answer with Highlighted Spans */}
          <div className="lg:col-span-6 rounded-2xl border border-white/[0.08] bg-[#090B0F] p-6 sm:p-8 space-y-6">
            <div className="flex items-center justify-between pb-4 border-b border-white/[0.06]">
              <div className="flex items-center gap-2">
                <ShieldCheck className="h-4 w-4 text-zinc-300" />
                <span className="text-xs font-mono font-semibold text-zinc-200 uppercase tracking-wider">
                  Grounded Output
                </span>
              </div>
              <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-mono text-zinc-300">
                94% Grounding Score
              </span>
            </div>

            <div className="space-y-4 text-sm sm:text-base leading-relaxed text-zinc-200">
              <p>
                <span className="border-b border-white/40 pb-0.5 text-white font-medium">
                  Greenhouse gases trap infrared radiation
                </span>{" "}
                in the atmosphere, creating radiative forcing that elevates global temperatures.{" "}
                <button
                  type="button"
                  onClick={() => setSelectedSource(0)}
                  className="inline-flex items-center text-xs font-mono text-zinc-400 hover:text-white underline decoration-dotted ml-1 cursor-pointer"
                >
                  [Source #1]
                </button>
              </p>

              <p>
                <span className="border-b border-white/40 pb-0.5 text-white font-medium">
                  Fossil fuel combustion accounts for &gt;72%
                </span>{" "}
                of human emissions, while deforestation reduces natural carbon sinks.{" "}
                <button
                  type="button"
                  onClick={() => setSelectedSource(1)}
                  className="inline-flex items-center text-xs font-mono text-zinc-400 hover:text-white underline decoration-dotted ml-1 cursor-pointer"
                >
                  [Source #2]
                </button>
              </p>

              <p>
                <span className="border-b border-white/40 pb-0.5 text-white font-medium">
                  Methane emissions from agriculture & energy leaks
                </span>{" "}
                exert a 28x stronger warming effect per ton over 100 years.{" "}
                <button
                  type="button"
                  onClick={() => setSelectedSource(2)}
                  className="inline-flex items-center text-xs font-mono text-zinc-400 hover:text-white underline decoration-dotted ml-1 cursor-pointer"
                >
                  [Source #3]
                </button>
              </p>
            </div>

            <div className="pt-4 border-t border-white/[0.04] flex items-center justify-between text-xs font-mono text-zinc-500">
              <span>Guardrail: N-gram Overlap Passed</span>
              <span className="text-zinc-300 flex items-center gap-1 font-medium">
                <Check className="h-3.5 w-3.5" />
                Verified
              </span>
            </div>
          </div>

          {/* Right Column: Interactive Source Documents */}
          <div className="lg:col-span-6 space-y-3.5">
            <div className="text-xs font-mono text-zinc-500 uppercase tracking-wider px-1 flex items-center justify-between">
              <span>Select source to inspect passage</span>
              <span>{sources.length} Documents</span>
            </div>

            {sources.map((src, idx) => {
              const isSelected = selectedSource === idx;
              return (
                <div
                  key={src.id}
                  onClick={() => setSelectedSource(idx)}
                  className={`rounded-xl p-5 transition-all cursor-pointer ${
                    isSelected
                      ? "border border-white/20 bg-[#0E1117] shadow-lg"
                      : "border border-white/[0.06] bg-[#080A0E] hover:border-white/10 hover:bg-[#0A0D12]"
                  }`}
                >
                  <div className="flex items-center justify-between gap-2 pb-2">
                    <div className="flex items-center gap-2">
                      <FileCheck
                        className={`h-4 w-4 ${
                          isSelected ? "text-white" : "text-zinc-500"
                        }`}
                      />
                      <span className="text-xs font-semibold text-white tracking-tight">
                        {src.title}
                      </span>
                    </div>
                    <span
                      className={`text-xs font-mono px-2 py-0.5 rounded-md border ${
                        isSelected
                          ? "border-white/20 bg-white/10 text-white"
                          : "border-white/[0.06] bg-white/[0.02] text-zinc-500"
                      }`}
                    >
                      {src.similarity}
                    </span>
                  </div>

                  <p className="mt-2 text-xs text-zinc-400 leading-relaxed font-normal">
                    "{src.text}"
                  </p>

                  <div className="mt-3 pt-2.5 border-t border-white/[0.04] flex items-center justify-between text-[11px] font-mono text-zinc-500">
                    <span className="truncate max-w-[200px]">{src.id}</span>
                    <span className="text-zinc-500">{src.strategy}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}

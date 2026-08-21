import { useState } from "react";
import { Globe, Mic, ShieldCheck } from "lucide-react";

export function MultilingualSection() {
  const [selectedLang, setSelectedLang] = useState<"hi" | "en">("hi");

  const examples = {
    hi: {
      langName: "हिन्दी (Hindi)",
      script: "Devanagari",
      queryVoice: "जलवायु परिवर्तन के मुख्य कारण क्या हैं?",
      queryEnglishMeaning: "What are the primary causes of climate change?",
      response:
        "जलवायु परिवर्तन मुख्य रूप से मानवीय गतिविधियों द्वारा संचालित होता है, विशेषकर जीवाश्म ईंधन (कोयला, तेल और प्राकृतिक गैस) के जलने से। इससे वायुमंडल में ग्रीनहाउस गैसों जैसे कार्बन डाइऑक्साइड (CO₂) और मीथेन का स्तर बढ़ता है। इसके अतिरिक्त, बड़े पैमाने पर वनों की कटाई और कृषि पद्धतियां भी ताप को अवशोषित करने वाले आवरण को गहरा करती हैं।",
      tags: ["ग्रीनहाउस गैस", "जीवाश्म ईंधन", "वनोन्मूलन"],
      groundedPct: "95%",
    },
    en: {
      langName: "English",
      script: "Latin",
      queryVoice: "What are the primary causes of climate change?",
      queryEnglishMeaning: "Direct natural language query",
      response:
        "Climate change is primarily driven by anthropogenic activities, specifically the combustion of fossil fuels (coal, petroleum, and natural gas). This releases elevated concentrations of greenhouse gases such as carbon dioxide (CO₂) and methane. Deforestation and intensive industrial agriculture further accelerate global atmospheric warming.",
      tags: ["Greenhouse Gases", "Fossil Fuels", "Deforestation"],
      groundedPct: "96%",
    },
  };

  const current = examples[selectedLang];

  return (
    <section id="multilingual" className="relative py-24 sm:py-32 border-t border-white/[0.06] bg-[#030405]">
      <div className="mx-auto max-w-5xl px-4 sm:px-6">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-1.5 rounded-full border border-white/[0.08] bg-white/[0.02] px-3.5 py-1 text-[10px] font-mono tracking-widest text-zinc-400 uppercase">
            <span>● Multilingual Understanding</span>
          </div>

          <h2 className="mt-6 text-3xl sm:text-5xl font-bold tracking-tight text-white leading-tight">
            One knowledge base.{" "}
            <span className="font-normal text-zinc-400">Every language.</span>
          </h2>

          <p className="mt-4 text-base sm:text-lg text-zinc-400 leading-relaxed font-normal">
            Vaani bridges linguistic barriers natively. Speak in Hindi or English, and receive grounded answers with full contextual fidelity.
          </p>
        </div>

        {/* Language Selection Switch */}
        <div className="mt-12 flex justify-center">
          <div className="inline-flex items-center gap-1 rounded-full border border-white/[0.08] bg-[#090B0F] p-1 shadow-xl">
            <button
              type="button"
              onClick={() => setSelectedLang("hi")}
              className={`flex items-center gap-2 rounded-full px-5 py-2 text-xs font-semibold font-['Noto_Sans_Devanagari'] transition-all cursor-pointer ${
                selectedLang === "hi"
                  ? "bg-[#F2F2F2] text-[#050505]"
                  : "text-zinc-400 hover:text-white"
              }`}
            >
              <Globe className="h-3.5 w-3.5" />
              <span>हिन्दी (Hindi)</span>
            </button>

            <button
              type="button"
              onClick={() => setSelectedLang("en")}
              className={`flex items-center gap-2 rounded-full px-5 py-2 text-xs font-semibold transition-all cursor-pointer ${
                selectedLang === "en"
                  ? "bg-[#F2F2F2] text-[#050505]"
                  : "text-zinc-400 hover:text-white"
              }`}
            >
              <Globe className="h-3.5 w-3.5" />
              <span>English</span>
            </button>
          </div>
        </div>

        {/* Bilingual Comparison Cards */}
        <div className="mt-10 grid gap-6 lg:grid-cols-12 items-stretch">
          {/* Left: Spoken Query Card */}
          <div className="lg:col-span-5 rounded-2xl border border-white/[0.06] bg-[#090B0F] p-6 sm:p-8 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between gap-2 pb-4 border-b border-white/[0.06] text-xs font-mono text-zinc-500">
                <span className="flex items-center gap-1.5 text-zinc-300">
                  <Mic className="h-3.5 w-3.5" />
                  <span>Voice Prompt</span>
                </span>
                <span className="rounded bg-white/[0.03] px-2 py-0.5 border border-white/[0.06]">
                  {current.script}
                </span>
              </div>

              <div className="mt-6">
                <p className="text-lg sm:text-xl font-medium text-white leading-relaxed font-['Noto_Sans_Devanagari']">
                  "{current.queryVoice}"
                </p>
                {selectedLang === "hi" && (
                  <p className="mt-3 text-xs text-zinc-500 italic">
                    Meaning: "{current.queryEnglishMeaning}"
                  </p>
                )}
              </div>
            </div>

            <div className="mt-8 pt-4 border-t border-white/[0.04] flex items-center justify-between text-xs font-mono text-zinc-500">
              <span>Sampling: 16kHz</span>
              <span className="text-zinc-300">Native ASR</span>
            </div>
          </div>

          {/* Right: Synthesized Response Card */}
          <div className="lg:col-span-7 rounded-2xl border border-white/[0.08] bg-[#0B0E13] p-6 sm:p-8 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between gap-2 pb-4 border-b border-white/[0.06] text-xs">
                <div className="flex items-center gap-2 text-zinc-300 font-semibold font-mono">
                  <ShieldCheck className="h-4 w-4" />
                  <span>GROUNDED SYNTHESIS</span>
                </div>
                <span className="rounded-full border border-white/10 bg-white/5 px-2.5 py-0.5 text-xs text-zinc-300 font-mono">
                  {current.groundedPct} Confidence
                </span>
              </div>

              <p className="mt-5 text-sm sm:text-base text-zinc-200 leading-relaxed font-['Noto_Sans_Devanagari']">
                {current.response}
              </p>

              <div className="mt-5 flex flex-wrap gap-2">
                {current.tags.map((tag, idx) => (
                  <span
                    key={idx}
                    className="rounded-md border border-white/[0.06] bg-white/[0.02] px-2.5 py-1 text-xs text-zinc-400 font-['Noto_Sans_Devanagari']"
                  >
                    #{tag}
                  </span>
                ))}
              </div>
            </div>

            <div className="mt-8 pt-4 border-t border-white/[0.04] flex items-center justify-between text-xs font-mono text-zinc-500">
              <span>Corpus: MSMARCO-XI (hi + en)</span>
              <span className="text-zinc-400">Zero Translation Loss</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

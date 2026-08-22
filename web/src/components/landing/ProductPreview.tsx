import { useState } from "react";
import {
  Check,
  ChevronDown,
  Database,
  Mic,
  ShieldCheck,
  Zap,
} from "lucide-react";

export function ProductPreview() {
  const [activeTab, setActiveTab] = useState<"en" | "hi">("en");
  const [sourcesOpen, setSourcesOpen] = useState(true);

  const previewData = {
    en: {
      query: "What are the primary causes of renewable energy intermittency?",
      transcript: "What are the primary causes of renewable energy intermittency and how does grid storage help?",
      answer:
        "Renewable energy intermittency is primarily driven by diurnal solar cycles, atmospheric cloud cover variations, and seasonal wind velocity fluctuations. Modern grid stability relies on hybrid utility-scale lithium-ion storage, pumped hydro systems, and dynamic load-frequency balancing to smooth generation deficits.",
      confidence: "94%",
      sources: [
        {
          id: "chunk_0482",
          title: "MSMARCO-XI / Energy Systems & Grid Dynamics",
          score: "0.892",
          snippet:
            "Intermittent generation from wind and solar occurs due to atmospheric fluctuations and diurnal variations. Lithium storage and pumped hydroelectric dams buffer supply-demand mismatches...",
        },
        {
          id: "chunk_0914",
          title: "Renewable Power Integration Frameworks",
          score: "0.841",
          snippet:
            "Grid frequency regulation requires sub-second response times during rapid cloud shading events. Storage assets provide synthetic inertia to maintain standard frequencies...",
        },
      ],
      metrics: {
        stt: "138ms",
        embedding: "22ms",
        retrieval: "34ms",
        generation: "285ms",
        total: "479ms",
      },
    },
    hi: {
      query: "नवीकरणीय ऊर्जा की आंतरायिकता के मुख्य कारण क्या हैं?",
      transcript: "नवीकरणीय ऊर्जा की आंतरायिकता के मुख्य कारण क्या हैं और ग्रिड भंडारण इसमें कैसे मदद करता है?",
      answer:
        "नवीकरणीय ऊर्जा की आंतरायिकता मुख्य रूप से सौर विकिरण में दैनिक चक्र, बादलों के आवरण में परिवर्तन और मौसमी वायु गति में उतार-चढ़ाव के कारण होती है। आधुनिक ग्रिड स्थिरता उत्पादन की कमी को संतुलित करने के लिए बड़े पैमाने पर लिथियम-आयन बैटरी भंडारण और पंप किए गए जलविद्युत प्रणालियों पर निर्भर करती है।",
      confidence: "92%",
      sources: [
        {
          id: "chunk_1204",
          title: "MSMARCO-XI / ऊर्जा प्रणालियां और ग्रिड डायनेमिक्स",
          score: "0.878",
          snippet:
            "सौर और पवन ऊर्जा से अनियमित उत्पादन वायुमंडलीय उतार-चढ़ाव और दैनिक परिवर्तनों के कारण होता है। बैटरी भंडारण आपूर्ति-मांग के अंतर को स्थिर करता है...",
        },
        {
          id: "chunk_1562",
          title: "स्वच्छ ऊर्जा ग्रिड एकीकरण ढांचा",
          score: "0.835",
          snippet:
            "बादलों के छाने के दौरान ग्रिड आवृत्ति नियमन के लिए त्वरित प्रतिक्रिया की आवश्यकता होती है। भंडारण संपत्तियां मानक आवृत्तियों को बनाए रखती हैं...",
        },
      ],
      metrics: {
        stt: "152ms",
        embedding: "26ms",
        retrieval: "38ms",
        generation: "310ms",
        total: "526ms",
      },
    },
  };

  const current = previewData[activeTab];

  return (
    <div className="relative mx-auto w-full max-w-5xl px-4 sm:px-6 pt-4 pb-12">
      {/* Subtle Container Shadow */}
      <div className="relative rounded-2xl sm:rounded-3xl border border-white/[0.08] bg-[#090B0F] shadow-2xl overflow-hidden">
        {/* Top Window Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/[0.06] bg-[#0D1015] px-5 py-3 sm:px-6">
          <div className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-zinc-700" />
            <span className="h-2.5 w-2.5 rounded-full bg-zinc-700" />
            <span className="h-2.5 w-2.5 rounded-full bg-zinc-700" />
            <div className="ml-3 hidden sm:flex items-center gap-2 rounded-md bg-[#05070A] px-2.5 py-1 text-[11px] font-mono text-zinc-500 border border-white/[0.04]">
              <span>vaani.ai/session/live</span>
            </div>
          </div>

          {/* Language Toggle */}
          <div className="flex items-center gap-1 rounded-lg border border-white/[0.08] bg-[#05070A] p-0.5">
            <button
              type="button"
              onClick={() => setActiveTab("en")}
              className={`rounded-md px-2.5 py-1 text-xs font-medium transition-all cursor-pointer ${
                activeTab === "en"
                  ? "bg-white/10 text-white font-semibold"
                  : "text-zinc-500 hover:text-zinc-300"
              }`}
            >
              <span>English</span>
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("hi")}
              className={`rounded-md px-2.5 py-1 text-xs font-medium font-['Noto_Sans_Devanagari'] transition-all cursor-pointer ${
                activeTab === "hi"
                  ? "bg-white/10 text-white font-semibold"
                  : "text-zinc-500 hover:text-zinc-300"
              }`}
            >
              <span>हिन्दी</span>
            </button>
          </div>
        </div>

        {/* Workspace Body */}
        <div className="p-5 sm:p-8 space-y-6">
          {/* User Voice Input Bubble */}
          <div className="flex items-start gap-3.5">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-white/10 bg-white/5 text-zinc-300">
              <Mic className="h-4 w-4 stroke-[1.75]" />
            </div>
            <div className="flex-1 rounded-xl border border-white/[0.06] bg-[#0D1015] p-4">
              <div className="flex items-center justify-between gap-2 pb-1.5 text-[10px] font-mono text-zinc-500 uppercase tracking-wider">
                <span className="flex items-center gap-1.5">
                  <span className="h-1.5 w-1.5 rounded-full bg-zinc-400" />
                  <span>Spoken Query</span>
                </span>
                <span>{activeTab.toUpperCase()}</span>
              </div>
              <p className="text-sm font-medium text-[#F5F5F5] sm:text-base leading-relaxed">
                "{current.transcript}"
              </p>
            </div>
          </div>

          {/* Vaani Grounded Answer Box */}
          <div className="rounded-xl border border-white/[0.08] bg-[#0B0E13] p-5 sm:p-6 shadow-inner">
            {/* Answer Header */}
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/[0.06] pb-3.5">
              <div className="flex items-center gap-2">
                <ShieldCheck className="h-4 w-4 text-zinc-300" />
                <span className="text-xs font-semibold tracking-wider text-zinc-200 uppercase font-mono">
                  Grounded Synthesis
                </span>
              </div>

              <div className="flex items-center gap-2">
                <div className="flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-2.5 py-0.5 text-xs font-mono text-zinc-300">
                  <Check className="h-3 w-3 text-zinc-300" />
                  <span>{current.confidence} Confidence</span>
                </div>
                <span className="rounded-full border border-white/[0.06] bg-white/[0.02] px-2.5 py-0.5 text-xs font-mono text-zinc-500">
                  2 Sources
                </span>
              </div>
            </div>

            {/* Answer Content */}
            <div className="py-4">
              <p className="text-sm leading-relaxed text-zinc-200 sm:text-base">
                {current.answer}
              </p>
            </div>

            {/* Stage-by-Stage Latency Bar */}
            <div className="mt-2 flex flex-wrap items-center gap-2 rounded-lg border border-white/[0.04] bg-[#06080B] px-3.5 py-2 text-[11px] font-mono text-zinc-500">
              <span className="text-zinc-300 font-medium flex items-center gap-1">
                <Zap className="h-3 w-3" />
                Latency:
              </span>
              <span>STT {current.metrics.stt}</span>
              <span className="text-zinc-700">·</span>
              <span>Embed {current.metrics.embedding}</span>
              <span className="text-zinc-700">·</span>
              <span>FAISS {current.metrics.retrieval}</span>
              <span className="text-zinc-700">·</span>
              <span>Groq LLM {current.metrics.generation}</span>
              <span className="text-zinc-700">·</span>
              <span className="text-zinc-200 font-semibold">Total {current.metrics.total}</span>
            </div>
          </div>

          {/* Retrievable Sources Drawer */}
          <div className="rounded-xl border border-white/[0.06] bg-[#0B0E13] p-4 sm:p-5">
            <button
              type="button"
              onClick={() => setSourcesOpen(!sourcesOpen)}
              className="flex w-full items-center justify-between text-left text-xs font-semibold text-zinc-300 hover:text-white cursor-pointer"
            >
              <div className="flex items-center gap-2">
                <Database className="h-4 w-4 text-zinc-400" />
                <span>Retrieved Context ({current.sources.length} Documents)</span>
              </div>
              <ChevronDown
                className={`h-4 w-4 text-zinc-500 transition-transform duration-200 ${
                  sourcesOpen ? "rotate-180" : ""
                }`}
              />
            </button>

            {sourcesOpen && (
              <div className="mt-3.5 grid gap-3 sm:grid-cols-2">
                {current.sources.map((src) => (
                  <div
                    key={src.id}
                    className="rounded-lg border border-white/[0.04] bg-[#07090D] p-3.5 transition-colors hover:border-white/10"
                  >
                    <div className="flex items-center justify-between gap-2 pb-2 text-[11px] font-mono">
                      <span className="text-zinc-400 truncate max-w-[180px]">{src.title}</span>
                      <span className="rounded bg-white/5 px-1.5 py-0.5 text-zinc-300 border border-white/10">
                        Score {src.score}
                      </span>
                    </div>
                    <p className="text-xs text-zinc-400 line-clamp-3 leading-relaxed">
                      "{src.snippet}"
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Subtle Bottom Fade Mask */}
        <div className="absolute inset-x-0 bottom-0 h-16 bg-gradient-to-t from-[#030405] to-transparent pointer-events-none" />
      </div>
    </div>
  );
}

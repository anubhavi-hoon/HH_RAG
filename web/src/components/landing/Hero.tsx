import { ArrowRight, ChevronDown } from "lucide-react";
import { VoiceOrb } from "./VoiceOrb";
import { ProductPreview } from "./ProductPreview";

interface HeroProps {
  onNavigateApp: () => void;
}

export function Hero({ onNavigateApp }: HeroProps) {
  const handleScrollExplore = () => {
    const el = document.querySelector("#product");
    if (el) {
      el.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <section className="relative pt-16 pb-16 sm:pt-24 sm:pb-24">
      {/* Extremely faint white/grey bloom behind hero */}
      <div className="pointer-events-none absolute inset-0 -z-10 overflow-hidden">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 h-[500px] w-[800px] rounded-full bg-white/[0.02] blur-3xl opacity-60" />
      </div>

      <div className="mx-auto max-w-5xl px-4 sm:px-6 text-center">
        {/* Subtle Eyebrow Pill */}
        <div className="inline-flex items-center gap-2 rounded-full border border-white/[0.08] bg-white/[0.03] px-3.5 py-1 text-xs font-medium text-zinc-400 backdrop-blur-md">
          <span className="h-1.5 w-1.5 rounded-full bg-white" />
          <span className="tracking-widest uppercase text-[11px] font-mono text-zinc-400">
            Voice · Knowledge · Intelligence
          </span>
        </div>

        {/* Main Headline */}
        <h1 className="mt-8 text-4xl sm:text-6xl md:text-7xl font-bold tracking-tight text-white leading-[1.12] max-w-4xl mx-auto">
          Intelligence that <br className="hidden sm:inline" />
          <span className="font-medium text-zinc-300">
            speaks your language.
          </span>
        </h1>

        {/* Supporting Copy */}
        <p className="mt-6 text-base sm:text-lg text-zinc-400 max-w-2xl mx-auto leading-relaxed font-normal">
          Ask questions naturally. Speak in English or Hindi. Get grounded answers from your knowledge.
        </p>

        {/* Hero CTA Buttons */}
        <div className="mt-9 flex flex-col sm:flex-row items-center justify-center gap-3.5">
          <button
            type="button"
            onClick={onNavigateApp}
            className="group inline-flex w-full sm:w-auto items-center justify-center gap-2.5 rounded-full bg-[#F2F2F2] px-7 py-3.5 text-sm font-semibold text-[#050505] transition-all hover:bg-white hover:scale-[1.02] cursor-pointer shadow-lg shadow-white/[0.02]"
          >
            <span>Try Vaani</span>
            <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-0.5" />
          </button>

          <button
            type="button"
            onClick={handleScrollExplore}
            className="inline-flex w-full sm:w-auto items-center justify-center gap-2 rounded-full border border-white/[0.1] bg-transparent px-6 py-3.5 text-sm font-medium text-zinc-300 transition-all hover:border-white/20 hover:bg-[#15171A] hover:text-white cursor-pointer"
          >
            <span>Explore how it works</span>
            <ChevronDown className="h-4 w-4 text-zinc-400" />
          </button>
        </div>

        {/* Voice Core Orb Centerpiece */}
        <div className="mt-8 sm:mt-12">
          <VoiceOrb onActivate={onNavigateApp} />
        </div>

        {/* Product Visual Showcase Preview */}
        <div className="mt-6">
          <ProductPreview />
        </div>
      </div>
    </section>
  );
}

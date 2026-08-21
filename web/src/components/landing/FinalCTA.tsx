import { ArrowRight } from "lucide-react";

interface FinalCTAProps {
  onNavigateApp: () => void;
}

export function FinalCTA({ onNavigateApp }: FinalCTAProps) {
  return (
    <section className="relative py-28 sm:py-36 border-t border-white/[0.06] bg-[#030405]">
      <div className="mx-auto max-w-4xl px-4 sm:px-6 text-center">
        {/* Subtle Brand Badge */}
        <div className="inline-flex items-center gap-2 rounded-full border border-white/[0.08] bg-white/[0.02] px-4 py-1 text-xs font-medium text-zinc-400">
          <span className="h-1.5 w-1.5 rounded-full bg-white" />
          <span className="font-semibold text-white">VAANI</span>
          <span className="font-['Noto_Sans_Devanagari'] text-zinc-400">वाणी</span>
        </div>

        {/* Dramatic Headline */}
        <h2 className="mt-8 text-4xl sm:text-6xl md:text-7xl font-bold tracking-tight text-white leading-tight">
          Give your knowledge <br className="hidden sm:inline" />
          <span className="font-medium text-zinc-300">a voice.</span>
        </h2>

        {/* Supporting Copy */}
        <p className="mt-6 text-base sm:text-xl text-zinc-400 max-w-xl mx-auto font-normal leading-relaxed">
          Ask naturally. Understand deeply. Grounded intelligence across English and Hindi.
        </p>

        {/* White CTA Button */}
        <div className="mt-10 flex justify-center">
          <button
            type="button"
            onClick={onNavigateApp}
            className="group inline-flex items-center gap-2.5 rounded-full bg-[#F2F2F2] px-8 py-3.5 text-sm font-semibold text-[#050505] transition-all hover:bg-white hover:scale-105 cursor-pointer shadow-lg shadow-white/[0.02]"
          >
            <span>Try Vaani Now</span>
            <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-0.5" />
          </button>
        </div>

        {/* Tagline Footer */}
        <p className="mt-12 text-xs font-mono tracking-widest text-zinc-600 uppercase">
          Intelligence that speaks your language · Zero Hallucinations
        </p>
      </div>
    </section>
  );
}

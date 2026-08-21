import { Mic } from "lucide-react";

interface VoiceOrbProps {
  onActivate?: () => void;
}

export function VoiceOrb({ onActivate }: VoiceOrbProps) {
  const waveformBars = [6, 12, 18, 10, 24, 14, 28, 16, 8, 20, 10];

  return (
    <div className="relative flex flex-col items-center justify-center my-8">
      {/* Subtle concentric graphite ripple rings */}
      <div className="absolute h-72 w-72 sm:h-96 sm:w-96 rounded-full border border-white/[0.04] animate-ripple-mono pointer-events-none" />
      <div className="absolute h-56 w-56 sm:h-76 sm:w-76 rounded-full border border-white/[0.06] animate-ripple-mono [animation-delay:1.5s] pointer-events-none" />
      <div className="absolute h-44 w-44 sm:h-60 sm:w-60 rounded-full border border-white/[0.08] animate-ripple-mono [animation-delay:3s] pointer-events-none" />

      {/* Very soft white/grey bloom */}
      <div className="absolute h-52 w-52 rounded-full bg-white/[0.03] blur-3xl pointer-events-none" />

      {/* Voice Core Dark Glass Sphere */}
      <div
        role="button"
        tabIndex={0}
        onClick={onActivate}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            onActivate?.();
          }
        }}
        className="group relative flex h-36 w-36 sm:h-44 sm:w-44 cursor-pointer items-center justify-center rounded-full border border-white/[0.12] bg-[#0A0D12]/90 p-1 shadow-2xl backdrop-blur-2xl transition-all duration-500 hover:scale-105 hover:border-white/30 focus:outline-none focus:ring-2 focus:ring-white/40 focus:ring-offset-4 focus:ring-offset-[#030405]"
        aria-label="Interactive Vaani Voice Core"
      >
        {/* Subtle glass specular highlight */}
        <div className="absolute inset-1.5 rounded-full bg-gradient-to-b from-white/[0.08] via-transparent to-black/80 pointer-events-none" />

        {/* Breathing inner core glow */}
        <div className="absolute inset-4 rounded-full bg-white/[0.02] blur-md transition-all duration-500 group-hover:bg-white/[0.06]" />

        {/* Center Mic Symbol */}
        <div className="relative z-10 flex flex-col items-center justify-center">
          <div className="flex h-16 w-16 sm:h-18 sm:w-18 items-center justify-center rounded-full border border-white/[0.15] bg-[#12161E] text-[#F5F5F5] shadow-inner transition-transform duration-500 group-hover:scale-110">
            <Mic className="h-7 w-7 sm:h-8 sm:w-8 text-[#F5F5F5] stroke-[1.75]" />
          </div>

          {/* Micro status badge */}
          <div className="mt-2.5 flex items-center gap-1.5 rounded-full border border-white/[0.08] bg-[#05070A] px-2.5 py-0.5 text-[10px] font-mono text-zinc-400">
            <span className="h-1.5 w-1.5 rounded-full bg-zinc-300" />
            <span>Voice Ready</span>
          </div>
        </div>
      </div>

      {/* Subtle Monochromatic Audio Waveform Strip */}
      <div className="mt-7 flex items-center gap-1 px-5 py-2 rounded-full border border-white/[0.06] bg-[#080A0E]/70 backdrop-blur-md">
        <span className="text-[10px] font-mono text-zinc-500 mr-2 tracking-wider uppercase">
          Acoustic Input
        </span>
        <div className="flex items-center gap-1 h-5">
          {waveformBars.map((height, idx) => (
            <span
              key={idx}
              className="w-0.5 rounded-full bg-zinc-300 transition-all duration-300"
              style={{
                height: `${height}px`,
                animation: "waveBarMono 2.2s ease-in-out infinite",
                animationDelay: `${idx * 0.18}s`,
              }}
            />
          ))}
        </div>
        <span className="text-[10px] font-mono text-zinc-400 ml-2">EN · HI</span>
      </div>
    </div>
  );
}

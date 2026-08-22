import { CheckCircle, Globe, Mic, ShieldCheck, Zap } from "lucide-react";

export function CapabilityStrip() {
  const capabilities = [
    {
      icon: Globe,
      label: "English · हिन्दी",
      sub: "Bilingual Intelligence",
    },
    {
      icon: Mic,
      label: "Voice + Text",
      sub: "Acoustic & Semantic",
    },
    {
      icon: ShieldCheck,
      label: "Grounded Retrieval",
      sub: "Zero Hallucinations",
    },
    {
      icon: CheckCircle,
      label: "Transparent Sources",
      sub: "Verifiable Evidence",
    },
    {
      icon: Zap,
      label: "Sub-Second Pipeline",
      sub: "High-Throughput Speed",
    },
  ];

  return (
    <section className="relative border-y border-white/[0.06] bg-[#050608] py-8">
      <div className="mx-auto max-w-5xl px-4 sm:px-6">
        <div className="grid grid-cols-2 gap-6 sm:grid-cols-3 md:grid-cols-5">
          {capabilities.map((item, idx) => {
            const Icon = item.icon;
            return (
              <div
                key={idx}
                className="flex flex-col items-center text-center space-y-1.5 group"
              >
                <div className="flex h-8 w-8 items-center justify-center rounded-full border border-white/[0.08] bg-white/[0.02] text-zinc-400 group-hover:border-white/20 group-hover:text-white transition-colors">
                  <Icon className="h-4 w-4 stroke-[1.5]" />
                </div>
                <span className="text-xs font-medium text-zinc-200 tracking-tight">
                  {item.label}
                </span>
                <span className="text-[10px] font-mono text-zinc-500">
                  {item.sub}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

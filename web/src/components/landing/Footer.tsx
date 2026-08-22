interface FooterProps {
  onNavigateApp: () => void;
}

export function Footer({ onNavigateApp }: FooterProps) {
  const links = [
    { label: "Product", href: "#product" },
    { label: "How it works", href: "#how-it-works" },
    { label: "Multilingual", href: "#multilingual" },
    { label: "Grounding", href: "#grounding" },
    { label: "Technology", href: "#technology" },
  ];

  const handleScroll = (href: string) => {
    const el = document.querySelector(href);
    if (el) {
      el.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <footer className="border-t border-white/[0.06] bg-[#020304] py-14 text-zinc-500">
      <div className="mx-auto max-w-5xl px-4 sm:px-6">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-8 pb-12 border-b border-white/[0.06]">
          {/* Brand Col */}
          <div className="space-y-2 max-w-xs">
            <div className="flex items-center gap-2">
              <div className="flex h-6 w-6 items-center justify-center rounded-full border border-white/20 bg-white/10 text-white font-semibold text-[10px]">
                V
              </div>
              <span className="text-sm font-bold text-white tracking-tight">VAANI</span>
              <span className="font-['Noto_Sans_Devanagari'] text-xs font-normal text-zinc-400">
                वाणी
              </span>
            </div>
            <p className="text-xs text-zinc-500 leading-relaxed">
              Intelligence that speaks your language. Multilingual, voice-enabled AI knowledge retrieval.
            </p>
          </div>

          {/* Navigation Links */}
          <div className="flex flex-wrap gap-6 text-xs font-medium text-zinc-400">
            {links.map((link) => (
              <button
                key={link.href}
                type="button"
                onClick={() => handleScroll(link.href)}
                className="hover:text-white transition-colors cursor-pointer"
              >
                {link.label}
              </button>
            ))}
            <button
              type="button"
              onClick={onNavigateApp}
              className="text-white font-semibold hover:text-zinc-300 transition-colors cursor-pointer"
            >
              Launch App →
            </button>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="mt-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-mono text-zinc-600">
          <div>
            © {new Date().getFullYear()} Vaani (वाणी) · Multilingual Voice-Enabled RAG
          </div>
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-zinc-400" />
              <span>Pipeline Ready</span>
            </span>
            <span>English · हिन्दी</span>
          </div>
        </div>
      </div>
    </footer>
  );
}

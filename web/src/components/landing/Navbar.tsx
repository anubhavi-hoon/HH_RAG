import { useState } from "react";
import { ArrowRight, Menu, X } from "lucide-react";

interface NavbarProps {
  onNavigateApp: () => void;
}

export function Navbar({ onNavigateApp }: NavbarProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navLinks = [
    { label: "Product", href: "#product" },
    { label: "How it works", href: "#how-it-works" },
    { label: "Multilingual", href: "#multilingual" },
    { label: "Grounding", href: "#grounding" },
    { label: "Technology", href: "#technology" },
  ];

  const handleLinkClick = (href: string) => {
    setMobileMenuOpen(false);
    const element = document.querySelector(href);
    if (element) {
      element.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <header className="sticky top-5 z-50 mx-auto w-full max-w-5xl px-4 sm:px-6">
      <nav className="relative flex items-center justify-between rounded-full border border-white/[0.08] bg-[#08090B]/80 px-4 py-2.5 shadow-2xl backdrop-blur-xl sm:px-6">
        {/* Brand Mark */}
        <a
          href="#"
          className="group flex items-center gap-2.5 transition-opacity hover:opacity-80"
          aria-label="Vaani Home"
        >
          <div className="flex h-7 w-7 items-center justify-center rounded-full border border-white/20 bg-white/10 text-[11px] font-semibold text-white">
            V
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-sm font-semibold tracking-tight text-white sm:text-base">
              VAANI
            </span>
            <span className="font-['Noto_Sans_Devanagari'] text-xs font-normal text-zinc-400">
              वाणी
            </span>
          </div>
        </a>

        {/* Desktop Navigation Links */}
        <div className="hidden items-center gap-7 md:flex">
          {navLinks.map((link) => (
            <button
              key={link.href}
              type="button"
              onClick={() => handleLinkClick(link.href)}
              className="text-xs font-medium text-zinc-400 transition-colors hover:text-white cursor-pointer"
            >
              {link.label}
            </button>
          ))}
        </div>

        {/* Right CTA Button */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onNavigateApp}
            className="group inline-flex items-center gap-1.5 rounded-full bg-[#F2F2F2] px-4 py-2 text-xs font-semibold text-[#050505] transition-all hover:bg-white hover:scale-[1.02] cursor-pointer"
          >
            <span>Try Vaani</span>
            <ArrowRight className="h-3.5 w-3.5 transition-transform duration-200 group-hover:translate-x-0.5" />
          </button>

          {/* Mobile Hamburger Toggle */}
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="flex h-8 w-8 items-center justify-center rounded-full border border-white/10 bg-white/5 text-zinc-400 hover:text-white md:hidden cursor-pointer"
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
          </button>
        </div>
      </nav>

      {/* Mobile Slide-down Sheet */}
      {mobileMenuOpen && (
        <div className="mt-2.5 overflow-hidden rounded-2xl border border-white/[0.08] bg-[#08090B]/95 p-5 shadow-2xl backdrop-blur-2xl md:hidden">
          <div className="flex flex-col space-y-3.5">
            {navLinks.map((link) => (
              <button
                key={link.href}
                type="button"
                onClick={() => handleLinkClick(link.href)}
                className="text-left text-sm font-medium text-zinc-400 hover:text-white transition-colors py-1 cursor-pointer"
              >
                {link.label}
              </button>
            ))}
            <div className="pt-2 border-t border-white/[0.08]">
              <button
                type="button"
                onClick={() => {
                  setMobileMenuOpen(false);
                  onNavigateApp();
                }}
                className="flex w-full items-center justify-center gap-2 rounded-xl bg-[#F2F2F2] py-2.5 text-sm font-semibold text-[#050505] transition-all hover:bg-white cursor-pointer"
              >
                <span>Launch Application</span>
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}

import { Navbar } from "../components/landing/Navbar";
import { Hero } from "../components/landing/Hero";
import { CapabilityStrip } from "../components/landing/CapabilityStrip";
import { FeatureSection } from "../components/landing/FeatureSection";
import { HowItWorks } from "../components/landing/HowItWorks";
import { MultilingualSection } from "../components/landing/MultilingualSection";
import { GroundingSection } from "../components/landing/GroundingSection";
import { TechnologySection } from "../components/landing/TechnologySection";
import { FinalCTA } from "../components/landing/FinalCTA";
import { Footer } from "../components/landing/Footer";

interface LandingPageProps {
  onNavigateApp: () => void;
}

export function LandingPage({ onNavigateApp }: LandingPageProps) {
  return (
    <div className="relative min-h-screen bg-[#030405] text-[#F5F5F5] selection:bg-white/15 selection:text-white">
      {/* Extremely subtle monochromatic background depth */}
      <div className="pointer-events-none fixed inset-0 -z-50 overflow-hidden">
        {/* Soft top ambient bloom */}
        <div className="absolute -top-40 left-1/2 -translate-x-1/2 h-[600px] w-[1000px] rounded-full bg-white/[0.015] blur-[140px]" />
      </div>

      {/* Floating Understated Navbar */}
      <Navbar onNavigateApp={onNavigateApp} />

      {/* Main Content Sections */}
      <main className="relative z-10">
        <Hero onNavigateApp={onNavigateApp} />
        <CapabilityStrip />
        <FeatureSection />
        <HowItWorks />
        <MultilingualSection />
        <GroundingSection />
        <TechnologySection />
        <FinalCTA onNavigateApp={onNavigateApp} />
      </main>

      {/* Footer */}
      <Footer onNavigateApp={onNavigateApp} />
    </div>
  );
}

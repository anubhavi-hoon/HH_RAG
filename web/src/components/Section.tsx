import type { ReactNode } from "react";

interface SectionProps {
  label: string;
  aside?: ReactNode;
  children: ReactNode;
}

/** Labelled content block used by every panel to keep spacing consistent. */
export function Section({ label, aside, children }: SectionProps) {
  return (
    <section className="border-t border-zinc-900 pt-6">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
        <h2 className="text-[11px] font-semibold uppercase tracking-[0.18em] text-zinc-500">
          {label}
        </h2>
        {aside}
      </div>
      {children}
    </section>
  );
}

export function EmptyState({ children }: { children: ReactNode }) {
  return (
    <p className="rounded-md border border-dashed border-zinc-900 px-4 py-6 text-sm text-zinc-600">
      {children}
    </p>
  );
}

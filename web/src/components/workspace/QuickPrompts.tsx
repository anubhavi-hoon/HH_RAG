interface QuickPromptsProps {
  onSelect: (prompt: string) => void;
  disabled?: boolean;
}

const PROMPTS = [
  "What was the impact of the Manhattan Project?",
  "What is photosynthesis?",
  "जलवायु परिवर्तन के मुख्य कारण क्या हैं?",
];

export function QuickPrompts({ onSelect, disabled = false }: QuickPromptsProps) {
  return (
    <div className="mx-auto w-full max-w-[640px] text-center">
      <div className="flex flex-wrap items-center justify-center gap-2">
        <span className="text-xs text-zinc-600 mr-1 select-none">
          Try asking:
        </span>
        {PROMPTS.map((prompt) => (
          <button
            key={prompt}
            type="button"
            disabled={disabled}
            onClick={() => onSelect(prompt)}
            className="rounded-full border border-white/[0.06] bg-white/[0.02] px-3 py-1 text-xs text-zinc-400 transition-all hover:border-white/20 hover:bg-white/[0.05] hover:text-zinc-200 disabled:cursor-not-allowed disabled:opacity-50 cursor-pointer"
          >
            &ldquo;{prompt}&rdquo;
          </button>
        ))}
      </div>
    </div>
  );
}

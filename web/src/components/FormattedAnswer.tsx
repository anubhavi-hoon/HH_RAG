import React, { useMemo } from "react";

interface HeadingBlock {
  type: "heading";
  level: number;
  content: string;
}

interface CodeBlock {
  type: "code_block";
  lang: string;
  content: string;
}

interface BlockMath {
  type: "block_math";
  content: string;
}

interface TableBlock {
  type: "table";
  headers: string[];
  alignments: ("left" | "center" | "right")[];
  rows: string[][];
}

interface ListBlock {
  type: "ul" | "ol";
  items: string[];
}

interface BlockquoteBlock {
  type: "blockquote";
  content: string;
}

interface HorizontalRuleBlock {
  type: "hr";
}

interface ParagraphBlock {
  type: "paragraph";
  content: string;
}

type Block =
  | HeadingBlock
  | CodeBlock
  | BlockMath
  | TableBlock
  | ListBlock
  | BlockquoteBlock
  | HorizontalRuleBlock
  | ParagraphBlock;

function isTableSeparator(line: string): boolean {
  const trimmed = line.trim();
  if (!trimmed.includes("-")) {
    return false;
  }
  const parts = trimmed.replace(/^\|/, "").replace(/\|$/, "").split("|");
  if (parts.length < 1) return false;
  return parts.every((part) => /^[\s:-]+$/.test(part) && part.includes("-"));
}

function parseTableAlignments(separatorLine: string): ("left" | "center" | "right")[] {
  const parts = separatorLine.trim().replace(/^\|/, "").replace(/\|$/, "").split("|");
  return parts.map((part) => {
    const p = part.trim();
    const startColon = p.startsWith(":");
    const endColon = p.endsWith(":");
    if (startColon && endColon) return "center";
    if (endColon) return "right";
    return "left";
  });
}

function splitTableRow(rowLine: string): string[] {
  let line = rowLine.trim();
  if (line.startsWith("|")) line = line.slice(1);
  if (line.endsWith("|")) line = line.slice(0, -1);
  return line.split("|").map((cell) => cell.trim());
}

function parseBlocks(rawText: string): Block[] {
  if (!rawText) return [];
  const normalized = rawText.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
  const lines = normalized.split("\n");
  const blocks: Block[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // 1. Empty lines
    if (line.trim() === "") {
      i++;
      continue;
    }

    // 2. Fenced Code Block: ```lang
    if (line.trim().startsWith("```")) {
      const lang = line.trim().slice(3).trim();
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].trim().startsWith("```")) {
        codeLines.push(lines[i]);
        i++;
      }
      if (i < lines.length && lines[i].trim().startsWith("```")) {
        i++;
      }
      blocks.push({
        type: "code_block",
        lang,
        content: codeLines.join("\n"),
      });
      continue;
    }

    // 3. Block math: $$ ... $$ or \[ ... \]
    if (line.trim().startsWith("$$") || line.trim().startsWith("\\[")) {
      const isBracket = line.trim().startsWith("\\[");
      const endMarker = isBracket ? "\\]" : "$$";
      const startMarker = isBracket ? "\\[" : "$$";
      const trimmed = line.trim();
      const restOfLine = trimmed.slice(startMarker.length);

      if (restOfLine.includes(endMarker)) {
        const mathContent = restOfLine.slice(0, restOfLine.indexOf(endMarker)).trim();
        blocks.push({ type: "block_math", content: mathContent });
        i++;
        continue;
      }

      const mathLines: string[] = [];
      if (restOfLine.trim()) mathLines.push(restOfLine);
      i++;
      while (i < lines.length && !lines[i].includes(endMarker)) {
        mathLines.push(lines[i]);
        i++;
      }
      if (i < lines.length && lines[i].includes(endMarker)) {
        const endLine = lines[i];
        const beforeEnd = endLine.slice(0, endLine.indexOf(endMarker));
        if (beforeEnd.trim()) mathLines.push(beforeEnd);
        i++;
      }
      blocks.push({
        type: "block_math",
        content: mathLines.join("\n").trim(),
      });
      continue;
    }

    // 4. Headings: #, ##, ###, ####, #####, ######
    const headingMatch = line.match(/^(#{1,6})\s+(.+)$/);
    if (headingMatch) {
      blocks.push({
        type: "heading",
        level: headingMatch[1].length,
        content: headingMatch[2].trim(),
      });
      i++;
      continue;
    }

    // 5. Horizontal Rule: ---, ***, ___
    if (/^(?:---+|\*\*\*+|___+)\s*$/.test(line.trim())) {
      blocks.push({ type: "hr" });
      i++;
      continue;
    }

    // 6. Blockquote: > text
    if (line.trim().startsWith(">")) {
      const quoteLines: string[] = [];
      while (i < lines.length && lines[i].trim().startsWith(">")) {
        quoteLines.push(lines[i].trim().replace(/^>\s?/, ""));
        i++;
      }
      blocks.push({
        type: "blockquote",
        content: quoteLines.join("\n"),
      });
      continue;
    }

    // 7. Table detection: line has '|' and next line is table separator |---|---|
    if (line.includes("|") && i + 1 < lines.length && isTableSeparator(lines[i + 1])) {
      const headerLine = line;
      const separatorLine = lines[i + 1];
      i += 2;

      const headers = splitTableRow(headerLine);
      const alignments = parseTableAlignments(separatorLine);
      const rows: string[][] = [];

      while (i < lines.length && lines[i].includes("|") && lines[i].trim() !== "") {
        const rowCells = splitTableRow(lines[i]);
        rows.push(rowCells);
        i++;
      }

      blocks.push({
        type: "table",
        headers,
        alignments,
        rows,
      });
      continue;
    }

    // 8. Unordered list: - item, * item, + item
    if (/^[-*+]\s+/.test(line.trim())) {
      const items: string[] = [];
      while (i < lines.length && /^[-*+]\s+/.test(lines[i].trim())) {
        items.push(lines[i].trim().replace(/^[-*+]\s+/, ""));
        i++;
      }
      blocks.push({
        type: "ul",
        items,
      });
      continue;
    }

    // 9. Ordered list: 1. item, 2. item
    if (/^\d+\.\s+/.test(line.trim())) {
      const items: string[] = [];
      while (i < lines.length && /^\d+\.\s+/.test(lines[i].trim())) {
        items.push(lines[i].trim().replace(/^\d+\.\s+/, ""));
        i++;
      }
      blocks.push({
        type: "ol",
        items,
      });
      continue;
    }

    // 10. Paragraph: collect regular text lines until next special block or empty line
    const paraLines: string[] = [];
    while (
      i < lines.length &&
      lines[i].trim() !== "" &&
      !lines[i].trim().startsWith("```") &&
      !lines[i].trim().startsWith("$$") &&
      !lines[i].trim().startsWith("\\[") &&
      !lines[i].match(/^#{1,6}\s+/) &&
      !/^(?:---+|\*\*\*+|___+)\s*$/.test(lines[i].trim()) &&
      !lines[i].trim().startsWith(">") &&
      !(lines[i].includes("|") && i + 1 < lines.length && isTableSeparator(lines[i + 1])) &&
      !/^[-*+]\s+/.test(lines[i].trim()) &&
      !/^\d+\.\s+/.test(lines[i].trim())
    ) {
      paraLines.push(lines[i]);
      i++;
    }

    if (paraLines.length > 0) {
      blocks.push({
        type: "paragraph",
        content: paraLines.join("\n"),
      });
    }
  }

  return blocks;
}

function renderMath(mathText: string, keyPrefix: string): React.ReactNode {
  let text = mathText
    .replace(/\\left/g, "")
    .replace(/\\right/g, "")
    .replace(/\\times/g, "×")
    .replace(/\\cdot/g, "·")
    .replace(/\\pm/g, "±")
    .replace(/\\div/g, "÷")
    .replace(/\\le(q)?\b/g, "≤")
    .replace(/\\ge(q)?\b/g, "≥")
    .replace(/\\neq\b/g, "≠")
    .replace(/\\approx\b/g, "≈")
    .replace(/\\infty\b/g, "∞")
    .replace(/\\pi\b/g, "π")
    .replace(/\\alpha\b/g, "α")
    .replace(/\\beta\b/g, "β")
    .replace(/\\gamma\b/g, "γ")
    .replace(/\\delta\b/g, "δ")
    .replace(/\\theta\b/g, "θ")
    .replace(/\\lambda\b/g, "λ")
    .replace(/\\sigma\b/g, "σ")
    .replace(/\\omega\b/g, "ω")
    .replace(/\\Delta\b/g, "Δ")
    .replace(/\\Sigma\b/g, "Σ")
    .replace(/\\Omega\b/g, "Ω")
    .replace(/\\sqrt\{([^}]+)\}/g, "√($1)")
    .replace(/\\frac\{([^}]+)\}\{([^}]+)\}/g, "($1 / $2)")
    .replace(/\\text\{([^}]+)\}/g, "$1")
    .replace(/\\mathrm\{([^}]+)\}/g, "$1")
    .replace(/\\mathbf\{([^}]+)\}/g, "$1");

  const parts: React.ReactNode[] = [];
  const regex = /(\^\{[^}]+\}|\^[0-9a-zA-Z+-]+|_\{[^}]+\}|_[0-9a-zA-Z+-]+)/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }
    const token = match[0];
    if (token.startsWith("^")) {
      const val = token.startsWith("^{") ? token.slice(2, -1) : token.slice(1);
      parts.push(
        <sup key={`${keyPrefix}-sup-${match.index}`} className="text-[0.75em] leading-none">
          {val}
        </sup>
      );
    } else if (token.startsWith("_")) {
      const val = token.startsWith("_{") ? token.slice(2, -1) : token.slice(1);
      parts.push(
        <sub key={`${keyPrefix}-sub-${match.index}`} className="text-[0.75em] leading-none">
          {val}
        </sub>
      );
    }
    lastIndex = regex.lastIndex;
  }
  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }

  return (
    <span className="inline-block px-0.5 font-serif italic tracking-wide text-amber-200/90">
      {parts}
    </span>
  );
}

function renderInline(text: string, keyPrefix: string = "inline"): React.ReactNode[] {
  if (!text) return [];

  const regex =
    /(\\\[[\s\S]*?\\\]|\\\([\s\S]*?\\\)|\$\$[\s\S]*?\$\$|\$[^\$\n]+?\$|`[^`\n]+`|\*\*\*[^*]+?\*\*\*|___[^_]+?___|\*\*[^*]+?\*\*|__[^_]+?__|\*[^*\n]+?\*|~~[^~]+?~~|\n)/g;

  const result: React.ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;
  let count = 0;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      result.push(text.slice(lastIndex, match.index));
    }
    const token = match[0];
    const k = `${keyPrefix}-${count++}`;

    if (token.startsWith("\\[") && token.endsWith("\\]")) {
      const math = token.slice(2, -2).trim();
      result.push(renderMath(math, k));
    } else if (token.startsWith("\\(") && token.endsWith("\\)")) {
      const math = token.slice(2, -2).trim();
      result.push(renderMath(math, k));
    } else if (token.startsWith("$$") && token.endsWith("$$")) {
      const math = token.slice(2, -2).trim();
      result.push(renderMath(math, k));
    } else if (token.startsWith("$") && token.endsWith("$") && token.length > 2) {
      const math = token.slice(1, -1).trim();
      result.push(renderMath(math, k));
    } else if (token.startsWith("`") && token.endsWith("`")) {
      const code = token.slice(1, -1);
      result.push(
        <code
          key={k}
          className="rounded border border-zinc-800 bg-zinc-900/80 px-1.5 py-0.5 font-mono text-[0.85em] font-normal text-emerald-400"
        >
          {code}
        </code>
      );
    } else if (
      (token.startsWith("***") && token.endsWith("***")) ||
      (token.startsWith("___") && token.endsWith("___"))
    ) {
      const inner = token.slice(3, -3);
      result.push(
        <strong key={k} className="font-semibold text-white">
          <em className="italic">{renderInline(inner, `${k}-bi`)}</em>
        </strong>
      );
    } else if (
      (token.startsWith("**") && token.endsWith("**")) ||
      (token.startsWith("__") && token.endsWith("__"))
    ) {
      const inner = token.slice(2, -2);
      result.push(
        <strong key={k} className="font-semibold text-white">
          {renderInline(inner, `${k}-b`)}
        </strong>
      );
    } else if (token.startsWith("*") && token.endsWith("*")) {
      const inner = token.slice(1, -1);
      result.push(
        <em key={k} className="italic text-zinc-200">
          {renderInline(inner, `${k}-i`)}
        </em>
      );
    } else if (token.startsWith("~~") && token.endsWith("~~")) {
      const inner = token.slice(2, -2);
      result.push(
        <del key={k} className="line-through text-zinc-400">
          {renderInline(inner, `${k}-s`)}
        </del>
      );
    } else if (token === "\n") {
      result.push(<br key={k} />);
    } else {
      result.push(token);
    }

    lastIndex = regex.lastIndex;
  }

  if (lastIndex < text.length) {
    result.push(text.slice(lastIndex));
  }

  return result;
}

export function FormattedAnswer({ content, language }: { content: string; language?: string }) {
  const blocks = useMemo(() => parseBlocks(content), [content]);

  return (
    <div lang={language} className="max-w-3xl space-y-4 text-zinc-100">
      {blocks.map((block, index) => {
        const k = `block-${index}`;
        switch (block.type) {
          case "heading": {
            const Tag = `h${Math.min(6, Math.max(1, block.level))}` as
              | "h1"
              | "h2"
              | "h3"
              | "h4"
              | "h5"
              | "h6";
            const sizeClass =
              block.level === 1
                ? "text-2xl sm:text-3xl font-bold text-white tracking-tight"
                : block.level === 2
                ? "text-xl sm:text-2xl font-bold text-white tracking-tight"
                : block.level === 3
                ? "text-lg sm:text-xl font-semibold text-white"
                : "text-base sm:text-lg font-semibold text-zinc-200";
            return (
              <Tag key={k} className={`${sizeClass} mt-4 first:mt-0`}>
                {renderInline(block.content, `${k}-h`)}
              </Tag>
            );
          }
          case "paragraph": {
            return (
              <p
                key={k}
                className="text-xl leading-relaxed text-zinc-100 sm:text-2xl first:mt-0"
              >
                {renderInline(block.content, `${k}-p`)}
              </p>
            );
          }
          case "ul": {
            return (
              <ul
                key={k}
                className="my-3 ml-6 list-disc space-y-2 text-xl leading-relaxed text-zinc-100 sm:text-2xl"
              >
                {block.items.map((item, i) => (
                  <li key={`${k}-li-${i}`}>{renderInline(item, `${k}-li-${i}`)}</li>
                ))}
              </ul>
            );
          }
          case "ol": {
            return (
              <ol
                key={k}
                className="my-3 ml-6 list-decimal space-y-2 text-xl leading-relaxed text-zinc-100 sm:text-2xl"
              >
                {block.items.map((item, i) => (
                  <li key={`${k}-li-${i}`}>{renderInline(item, `${k}-li-${i}`)}</li>
                ))}
              </ol>
            );
          }
          case "blockquote": {
            return (
              <blockquote
                key={k}
                className="my-3 rounded-r border-l-4 border-emerald-500/70 bg-zinc-900/40 py-2 pl-4 pr-3 text-lg italic text-zinc-300 sm:text-xl"
              >
                {renderInline(block.content, `${k}-bq`)}
              </blockquote>
            );
          }
          case "code_block": {
            return (
              <div
                key={k}
                className="my-4 overflow-hidden rounded-lg border border-zinc-800 bg-zinc-950"
              >
                {block.lang && (
                  <div className="border-b border-zinc-800/80 bg-zinc-900/60 px-4 py-1.5 font-mono text-xs text-zinc-400">
                    {block.lang}
                  </div>
                )}
                <pre className="overflow-x-auto p-4 font-mono text-sm leading-relaxed text-emerald-300">
                  <code>{block.content}</code>
                </pre>
              </div>
            );
          }
          case "block_math": {
            return (
              <div
                key={k}
                className="my-4 overflow-x-auto rounded-lg border border-zinc-800/80 bg-zinc-900/40 p-4 text-center text-xl sm:text-2xl"
              >
                {renderMath(block.content, `${k}-bm`)}
              </div>
            );
          }
          case "table": {
            return (
              <div
                key={k}
                className="my-4 overflow-x-auto rounded-lg border border-zinc-800 bg-zinc-950/60 shadow-sm"
              >
                <table className="w-full border-collapse text-left text-base sm:text-lg">
                  <thead>
                    <tr className="border-b border-zinc-800 bg-zinc-900/80">
                      {block.headers.map((h, i) => {
                        const align = block.alignments[i] || "left";
                        const alignClass =
                          align === "center"
                            ? "text-center"
                            : align === "right"
                            ? "text-right"
                            : "text-left";
                        return (
                          <th
                            key={i}
                            className={`px-4 py-3 font-semibold text-zinc-200 ${alignClass}`}
                          >
                            {renderInline(h, `${k}-th-${i}`)}
                          </th>
                        );
                      })}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-800/60">
                    {block.rows.map((row, rIdx) => (
                      <tr key={rIdx} className="transition-colors hover:bg-zinc-900/30">
                        {row.map((cell, cIdx) => {
                          const align = block.alignments[cIdx] || "left";
                          const alignClass =
                            align === "center"
                              ? "text-center"
                              : align === "right"
                              ? "text-right"
                              : "text-left";
                          return (
                            <td key={cIdx} className={`px-4 py-3 text-zinc-300 ${alignClass}`}>
                              {renderInline(cell, `${k}-td-${rIdx}-${cIdx}`)}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            );
          }
          case "hr": {
            return <hr key={k} className="my-6 border-zinc-800" />;
          }
          default:
            return null;
        }
      })}
    </div>
  );
}

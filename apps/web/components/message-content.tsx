"use client";

import { Fragment } from "react";
import katex from "katex";

function MathExpression({ expression, display = false }: { expression: string; display?: boolean }) {
  // Some model providers send a second layer of JSON-style escaping. KaTeX
  // expects one slash before commands (for example, `\\frac`), so collapse
  // only duplicated command slashes after we have identified a math span.
  const normalizedExpression = expression.replace(/\\\\(?=[A-Za-z])/g, "\\");
  const html = katex.renderToString(normalizedExpression, { displayMode: display, throwOnError: false, strict: "ignore" });
  return <span className={display ? "my-3 block overflow-x-auto" : "inline-block align-middle"} dangerouslySetInnerHTML={{ __html: html }}/>;
}

function normalizeMathDelimiters(text: string) {
  return text
    // Support providers which literally emit `\\(` and `\\[` rather than
    // the usual TeX delimiters `\(` and `\[`.
    .replace(/\\\\([()[\]])/g, (_match, delimiter: string) => `\\${delimiter}`)
    // Both one- and two-slash escaped dollar delimiters occur in model output.
    .replace(/\\\\\$([^$\n]+)\\\\\$/g, (_match, expression: string) => `$${expression}$`)
    .replace(/\\\$([^$\n]+)\\\$/g, (_match, expression: string) => `$${expression}$`);
}

function Inline({ text }: { text: string }) {
  const pieces = normalizeMathDelimiters(text).split(/(`[^`]+`|\\\([\s\S]*?\\\)|\$[^$\n]+\$|\*\*[^*]+\*\*)/g);
  return <>{pieces.map((piece, index) => {
    if (piece.startsWith("`") && piece.endsWith("`")) return <code className="rounded bg-[var(--surface)] px-1.5 py-0.5 font-mono text-sm" key={index}>{piece.slice(1, -1)}</code>;
    if (piece.startsWith("\\(") && piece.endsWith("\\)")) return <MathExpression expression={piece.slice(2, -2)} key={index}/>;
    if (piece.startsWith("$") && piece.endsWith("$")) return <MathExpression expression={piece.slice(1, -1)} key={index}/>;
    if (piece.startsWith("**") && piece.endsWith("**")) return <strong key={index}>{piece.slice(2, -2)}</strong>;
    return <Fragment key={index}>{piece}</Fragment>;
  })}</>;
}

function JavaCode({ code }: { code: string }) {
  const parts = code.split(/(\b(?:abstract|boolean|break|case|catch|class|else|extends|final|for|if|import|int|new|null|private|public|return|static|String|this|throw|try|void|while)\b|\b\d+(?:\.\d+)?\b|"(?:[^"\\]|\\.)*"|\/\/[^\n]*)/g);
  return <>{parts.map((part, index) => {
    if (/^\/\//.test(part)) return <span className="text-[var(--muted)]" key={index}>{part}</span>;
    if (/^"/.test(part)) return <span className="font-medium" key={index}>{part}</span>;
    if (/^\d/.test(part)) return <span className="font-semibold" key={index}>{part}</span>;
    if (/^(abstract|boolean|break|case|catch|class|else|extends|final|for|if|import|int|new|null|private|public|return|static|String|this|throw|try|void|while)$/.test(part)) return <span className="font-bold" key={index}>{part}</span>;
    return <Fragment key={index}>{part}</Fragment>;
  })}</>;
}

function CodeBlock({ language, code }: { language: string; code: string }) {
  async function copy() { await navigator.clipboard?.writeText(code); }
  return <div className="my-3 overflow-hidden rounded-lg border border-[var(--line)]"><div className="flex items-center justify-between border-b border-[var(--line)] bg-[var(--surface)] px-3 py-2 font-mono text-xs text-[var(--muted)]"><span>{language || "code"}</span><button className="underline" onClick={copy}>Copy</button></div><pre className="overflow-x-auto p-3 text-sm leading-6"><code>{language.toLowerCase() === "java" ? <JavaCode code={code}/> : code}</code></pre></div>;
}

function TextBlock({ block }: { block: string }) {
  return <>{normalizeMathDelimiters(block).split("\n\n").filter(Boolean).map((paragraph, paragraphIndex) => {
    const trimmed = paragraph.trim();
    if (trimmed.startsWith("$$") && trimmed.endsWith("$$") && trimmed.length > 4) return <MathExpression display expression={trimmed.slice(2, -2).trim()} key={paragraphIndex}/>;
    const bracketedDisplay = /^\\\[\s*([\s\S]*?)\s*\\\]$/.exec(trimmed);
    if (bracketedDisplay) return <MathExpression display expression={bracketedDisplay[1]} key={paragraphIndex}/>;
    const lines = paragraph.split("\n");
    const bullets = lines.every(line => /^[-*]\s+/.test(line));
    if (bullets) return <ul className="list-disc space-y-1 pl-5" key={paragraphIndex}>{lines.map((line, index) => <li key={index}><Inline text={line.replace(/^[-*]\s+/, "")}/></li>)}</ul>;
    if (lines.length === 1 && /^#{1,3}\s+/.test(lines[0])) {
      const text = lines[0].replace(/^#{1,3}\s+/, "");
      return <h3 className="font-semibold" key={paragraphIndex}><Inline text={text}/></h3>;
    }
    return <p className="whitespace-pre-wrap" key={paragraphIndex}><Inline text={paragraph}/></p>;
  })}</>;
}

/** React text nodes keep model output inert: this component never injects HTML. */
export function MessageContent({ content }: { content: string }) {
  const blocks = content.split(/```([\w+-]*)\n?([\s\S]*?)```/g);
  return <div className="space-y-3 leading-7">{blocks.map((block, index) => {
    if (index % 3 === 1) return <CodeBlock key={index} language={block} code={blocks[index + 1] ?? ""}/>;
    if (index % 3 === 2) return null;
    return <TextBlock block={block} key={index}/>;
  })}</div>;
}

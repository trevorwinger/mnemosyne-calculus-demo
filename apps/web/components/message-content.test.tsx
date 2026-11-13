import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { MessageContent } from "./message-content";

describe("MessageContent", () => {
  it("renders Markdown-style content without injecting model HTML", () => {
    const output = renderToStaticMarkup(<MessageContent content={'# Hint\n\n- **Check** `i < values.length`\n\n$\\frac{1}{2}$\n\n```java\nfor (int i = 0; i < values.length; i++) {}\n```\n\n<script>alert("no")</script>'}/>);
    expect(output).toContain("Hint");
    expect(output).toContain("Check");
    expect(output).toContain("for");
    expect(output).toContain("&lt;script&gt;");
    expect(output).not.toContain("<script>");
    expect(output).toContain("katex");
  });

  it("renders conventional and double-escaped TeX delimiters from model output", () => {
    const output = renderToStaticMarkup(<MessageContent content={String.raw`The slope is \\(\\frac{1}{2}\\), so substitute it below.

\\[ \\frac{x^2}{4} = 9 \\]`}/>);
    expect(output).toContain('class="katex"');
    expect(output).toContain('class="katex-display"');
    expect(output).toContain("frac");
    expect(output).not.toContain("\\\\(");
    expect(output).not.toContain("\\\\[");
  });
});

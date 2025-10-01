from __future__ import annotations
import asyncio, base64, os, pathlib, textwrap
from typing import Optional
from markdown_it import MarkdownIt
from markdown_it.extensions.front_matter import front_matter_plugin
from markdown_it.extensions.footnote import footnote_plugin
from markdown_it.extensions.tasklists import tasklists_plugin
from markdown_it.extensions.deflist import deflist_plugin

ASSETS_DIR = pathlib.Path(__file__).resolve().parents[1] / "assets"

def md_to_html(md: str) -> str:
    md = md.strip("\ufeff")  # trim BOM if pasted
    parser = (
        MarkdownIt("commonmark", {"html": False}) # disallow raw HTML
        .use(front_matter_plugin)
        .use(footnote_plugin)
        .use(tasklists_plugin)
        .use(deflist_plugin)
    )
    html_body = parser.render(md)
    css = (ASSETS_DIR / "github-markdown.css").read_text(encoding="utf-8")
    # Strict CSP: no external loads
    csp = "default-src 'none'; img-src data:; style-src 'self' 'unsafe-inline'; font-src 'self' data:;"
    template = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<meta http-equiv="Content-Security-Policy" content="{csp}"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<style>{css}</style>
</head>
<body>
<article class="markdown-body">
{html_body}
</article>
</body>
</html>"""
    return template

class Renderer:
    def __init__(self, width: int = 1024):
        self.width = width

    async def html_to_png(self, html: str, *, width: Optional[int] = None) -> bytes:
        width = width or self.width
        # Playwright is imported lazily to keep import cost low
        from playwright.async_api import async_playwright
        async with async_playwright() as pw:
            browser = await pw.chromium.launch()
            page = await browser.new_page(viewport={"width": width, "height": 10})
            await page.set_content(html, wait_until="load")
            # Auto-size the page height
            height = await page.evaluate("document.documentElement.scrollHeight")
            await page.set_viewport_size({"width": width, "height": height})
            buf = await page.screenshot(full_page=True, type="png")
            await browser.close()
            return buf

    async def render_markdown(self, md: str, *, width: Optional[int] = None) -> bytes:
        html = md_to_html(md)
        return await self.html_to_png(html, width=width)

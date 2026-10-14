"""Run after `make PRESENTATION=search-migration html`."""
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
import importlib.util
spec = importlib.util.spec_from_file_location('build_html', ROOT / 'scripts/build-html.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class Deck(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.titles, self.codes, self.links, self.images, self.ids = [], [], [], [], set()
        self.tag_counts = {}
        self.capture = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tag_counts[tag] = self.tag_counts.get(tag, 0) + 1
        if 'id' in attrs:
            self.ids.add(attrs['id'])
        if tag == 'a':
            self.links.append(attrs['href'])
        if tag == 'img':
            self.images.append(attrs['src'])
        if tag in ('h2', 'pre'):
            self.capture = (tag, [])

    def handle_data(self, data):
        if self.capture:
            self.capture[1].append(data)

    def handle_endtag(self, tag):
        if self.capture and tag == self.capture[0]:
            text = ''.join(self.capture[1]).strip()
            (self.titles if tag == 'h2' else self.codes).append(text)
            self.capture = None


class HtmlExportTests(unittest.TestCase):
    def test_nested_latex_arguments(self):
        text = r'{Search \texttt{pg\_trgm} and \{braces\}}tail'
        content, end = module.group(text, 0)
        self.assertEqual(content, r'Search \texttt{pg\_trgm} and \{braces\}')
        self.assertEqual(text[end:], 'tail')

    def test_nested_columns(self):
        source = r'\begin{columns}\column{.4\textwidth}A\begin{columns}\column{.5\textwidth}B\column{.5\textwidth}C\end{columns}\column{.6\textwidth}D\end{columns}'
        converted = module.normalize_columns(source)
        self.assertEqual(converted, r'\begin{columns}\begin{column}A\begin{columns}\begin{column}B\end{column}\begin{column}C\end{column}\end{columns}\end{column}\begin{column}D\end{column}\end{columns}')

    def test_generated_deck_preserves_content_and_order(self):
        source = (ROOT / 'presentations/search-migration/main.tex').read_text()
        deck = Deck((ROOT / 'dist/search-migration-html/index.html').read_text())
        titles = re.findall(r'\\begin\{frame\}(?:\[[^\]]*\])?\{([^\n}]+)\}', source)
        self.assertEqual(deck.titles, [t.replace(r'\&', '&') for t in titles])
        count = source.count(r'\begin{frame}')
        self.assertTrue({f'slide-{i}' for i in range(1, count + 1)} <= deck.ids)
        expected_code = re.findall(r'\\begin\{verbatim\}(.*?)\\end\{verbatim\}', source, re.S)
        self.assertEqual(deck.codes, [code.strip() for code in expected_code])
        for href in deck.links:
            if href.startswith('#'):
                self.assertIn(href[1:], deck.ids)
        self.assertTrue(deck.images)
        self.assertTrue(all(image.startswith('data:image/') for image in deck.images))
        self.assertGreater(deck.tag_counts.get('math', 0), 0)
        self.assertGreater(deck.tag_counts.get('table', 0), 0)
        self.assertFalse({'iframe', 'object', 'embed'} & deck.tag_counts.keys())
        i = deck.titles.index('Index Design: Country-Specific Indexes')
        self.assertEqual(deck.titles[i - 1], 'Search Concepts: From Similarity to Relevance')


if __name__ == '__main__':
    unittest.main()

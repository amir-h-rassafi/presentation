#!/usr/bin/env python3
"""Export this repository's Beamer frames as self-contained HTML using Pandoc."""
import argparse
import base64
from datetime import date
import json
import mimetypes
import os
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def group(text, start):
    """Read a balanced LaTeX argument, retaining nested formatting commands."""
    while start < len(text) and text[start].isspace():
        start += 1
    if start >= len(text) or text[start] != '{':
        raise ValueError('Expected a braced LaTeX argument')
    depth, i = 1, start + 1
    while i < len(text):
        if text[i] == '\\':
            i += 2
            continue
        depth += (text[i] == '{') - (text[i] == '}')
        if depth == 0:
            return text[start + 1:i], i + 1
        i += 1
    raise ValueError('Unclosed LaTeX argument')


def normalize_columns(text):
    # Pandoc understands column environments, but not Beamer's \column shorthand.
    stack = []
    pattern = r'\\begin\{columns\}(?:\[[^\]]*\])?|\\end\{columns\}|\\column(?:\[[^\]]*\])?\{[^}]*\}'
    def replace(match):
        token = match.group()
        if token.startswith(r'\begin'):
            stack.append(False)
            return r'\begin{columns}'
        if token.startswith(r'\end'):
            return (r'\end{column}' if stack.pop() else '') + token
        previous = r'\end{column}' if stack[-1] else ''
        stack[-1] = True
        return previous + r'\begin{column}'
    result = re.sub(pattern, replace, text)
    if stack:
        raise ValueError('Unclosed columns environment')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('presentation')
    args = parser.parse_args()
    source_dir = ROOT / 'presentations' / args.presentation
    source = (source_dir / 'main.tex').read_text()
    output = ROOT / 'dist' / (args.presentation + '-html')
    pandoc = [os.environ.get('PANDOC', 'pandoc')]
    if os.environ.get('PANDOC_DATA_DIR'):
        pandoc += ['--data-dir=' + os.environ['PANDOC_DATA_DIR']]

    def convert(text, reader, writer, *options):
        return subprocess.check_output(pandoc + ['-f', reader, '-t', writer, *options],
                                       input=text, text=True, cwd=source_dir)

    with tempfile.TemporaryDirectory(prefix='beamer-html-') as tmp:
        work = Path(tmp)
        colors = dict(re.findall(r'\\definecolor\{([^}]+)\}\{HTML\}\{([^}]+)\}',
                                 (ROOT / 'common/preamble.tex').read_text() + source))
        libraries = re.findall(r'\\usetikzlibrary\{([^}]+)\}', source)
        diagram_number = 0

        def pdf_svg(pdf):
            target = work / (pdf.stem + '.svg')
            subprocess.run(['pdftocairo', '-svg', str(pdf), str(target)], check=True)
            return target

        def data_uri(path):
            if path.suffix.lower() == '.pdf':
                path = pdf_svg(path)
            mime = mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
            return 'data:' + mime + ';base64,' + base64.b64encode(path.read_bytes()).decode()

        def diagram(tex):
            nonlocal diagram_number
            diagram_number += 1
            name = f'diagram-{diagram_number}'
            preamble = r'''\documentclass[tikz,border=3pt]{standalone}
\usepackage{fontspec}
\setsansfont{TeX Gyre Heros}
\renewcommand{\familydefault}{\sfdefault}
'''
            preamble += '\n'.join(r'\definecolor{' + k + '}{HTML}{' + v + '}' for k, v in colors.items())
            preamble += '\n' + '\n'.join(r'\usetikzlibrary{' + v + '}' for v in libraries)
            (work / (name + '.tex')).write_text(preamble + '\n\\begin{document}\n' + tex + '\n\\end{document}\n')
            result = subprocess.run(['xelatex', '-interaction=nonstopmode', '-halt-on-error', name + '.tex'],
                                    cwd=work, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            if result.returncode:
                raise RuntimeError('Diagram compilation failed:\n' + result.stdout[-4000:])
            return r'\includegraphics{' + str(pdf_svg(work / (name + '.pdf'))) + '}'

        # Render only diagrams as SVG; all slide text remains HTML.
        def include(match):
            path = source_dir / match.group(1)
            if not path.suffix:
                path = path.with_suffix('.tex')
            if path.is_file() and r'\begin{tikzpicture}' in path.read_text():
                return diagram(path.read_text())
            return match.group()
        prepared = re.sub(r'\\input\{([^}]+)\}', include, source)
        prepared = re.sub(r'\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}',
                          lambda m: diagram(m.group()), prepared, flags=re.S)
        prepared = normalize_columns(prepared)
        prepared = re.sub(r'(\\begin\{beamercolorbox\}(?:\[[^\]]*\])?)\{[^}]+\}', r'\1', prepared)
        definitions = [r'\newcommand{\resizebox}[3]{#3}']
        for key in ['title', 'subtitle', 'author', 'institute', 'date']:
            match = re.search(r'\\' + key + r'\s*\{', source)
            value = group(source, match.end() - 1)[0] if match else ''
            if key == 'date':
                value = value.replace(r'\today', date.today().strftime('%B %d, %Y')) or date.today().strftime('%B %d, %Y')
            definitions.append(r'\newcommand{\insert' + key + '}{' + value + '}')
        prepared = '\n'.join(definitions) + '\n' + prepared
        prepared = prepared.replace(r'\titlepage', r'\begin{center}\section*{\inserttitle}\insertsubtitle\par\insertauthor\par\insertinstitute\par\insertdate\end{center}')
        sections = re.findall(r'\\section\{([^}]+)\}', source)
        toc = r'\begin{itemize}' + ''.join(r'\item ' + s for s in sections) + r'\end{itemize}'
        prepared = prepared.replace(r'\tableofcontents', toc)
        document = json.loads(convert(prepared, 'latex', 'json'))
        frames = [b for b in document['blocks'] if b['t'] == 'Div' and 'frame' in b['c'][0][1]]
        expected = len(re.findall(r'\\begin\{frame\}', source))
        if len(frames) != expected:
            raise ValueError(f'Expected {expected} frames, converted {len(frames)}')
        for i, frame in enumerate(frames, 1):
            frame['c'][0][0] = f'slide-{i}'
            blocks = frame['c'][1]
            if blocks and blocks[0]['t'] == 'Para' and blocks[0]['c'] and blocks[0]['c'][0]['t'] == 'Span':
                inlines = blocks[0]['c'].pop(0)['c'][1]
                if not blocks[0]['c']:
                    blocks.pop(0)
                blocks.insert(0, {'t': 'Header', 'c': [2, ['', [], []], inlines]})

        def visit(node):
            if isinstance(node, list):
                for child in node:
                    visit(child)
            elif isinstance(node, dict):
                if node.get('t') == 'Image':
                    image = node['c']
                    path = Path(image[2][0])
                    if not path.is_absolute():
                        path = source_dir / path
                    image[2][0] = data_uri(path)
                    image[1] = [{'t': 'Str', 'c': path.stem.replace('-', ' ')}]
                    image[0][2] = [(k, v) for k, v in image[0][2] if k not in ('width', 'height')]
                elif node.get('t') == 'Div' and any(c in node['c'][0][1] for c in ('block', 'alertblock', 'exampleblock')):
                    blocks = node['c'][1]
                    if blocks and blocks[0]['t'] == 'Para' and blocks[0]['c'] and blocks[0]['c'][0]['t'] == 'Span':
                        heading = blocks[0]['c'].pop(0)['c'][1]
                        if heading:
                            blocks.insert(0, {'t': 'Header', 'c': [3, ['', [], []], heading]})
                for child in node.values():
                    visit(child)
        visit(frames)
        document['blocks'] = frames
        result = convert(json.dumps(document), 'json', 'html5', '--standalone', '--mathml',
                         '--template=' + str(ROOT / 'common/slides.html'))
        for name, color in colors.items():
            result = result.replace('color: ' + name + '"', 'color: #' + color + '"')
        if '<iframe' in result or '<embed' in result:
            raise ValueError('HTML must not embed a PDF')
        output.mkdir(parents=True, exist_ok=True)
        (output / 'index.html').write_text(result)
        print(f'Generated {len(frames)} HTML slides: {output / "index.html"}')


if __name__ == '__main__':
    main()

import ast
import re
from typing import Generator, List, Tuple

from pheasant.script.config import Cell

AST_PATTERN = re.compile(r'<_ast\.(.+?) ')

Element = Tuple[str, int, int]


def cell_splitter(source: str) -> Generator[Tuple[Cell, str], None, None]:

    lines = source.split('\n')

    def content(begin: int, end: int) -> str:
        """Join the lines and add a new line at the end."""
        return '\n'.join(lines[begin:end + 1]) + '\n'

    splitter = source_splitter(source)
    for name, begin, end in splitter:
        if name == 'Markdown':
            yield Cell.MARKDOWN, content(begin, end)
        else:
            first = begin
            while name not in ['Markdown', 'Separator']:
                last = end
                name, begin, end = next(splitter)
            yield Cell.CODE, content(first, last)
            if name == 'Markdown':
                yield Cell.MARKDOWN, content(begin, end)


def source_splitter(source: str) -> Generator[Element, None, None]:
    node = ast.parse(source)
    names = [ast_name(obj) for obj in node.body]

    lines = source.split('\n')
    first_linenos = [obj.lineno - 1 for obj in node.body]  # 0-indexed
    last_linenos = [find_last_lineno(lines, no - 1)
                    for no in first_linenos[1:] + [len(lines) - 1]]

    if first_linenos[0] != 0:
        yield from markdown_trimmer(lines, 0, first_linenos[0] - 1)
    cursor = first_linenos[0]
    for name, first, last in zip(names, first_linenos, last_linenos):
        if cursor < first:
            yield from markdown_trimmer(lines, cursor, first - 1)
        yield name, first, last
        cursor = last + 1
    if cursor <= len(lines) - 1:
        yield from markdown_trimmer(lines, cursor, len(lines) - 1)


def markdown_trimmer(lines: List[str], first: int,
                     last: int) -> Generator[Element, None, None]:
    begin = end = -1
    for cursor in range(first, last + 1):
        if lines[cursor]:
            if begin == -1:
                begin = cursor
            end = cursor
    if begin != -1:
        if begin == end and lines[begin].startswith('# -'):
            yield 'Separator', begin, end
        else:
            yield 'Markdown', begin, end


def ast_name(node: ast.AST) -> str:
    match = re.match(AST_PATTERN, str(node))
    if match:
        return match.group(1)
    else:
        return 'Unknown'


def find_last_lineno(lines: List[str], no: int) -> int:

    def is_code(line: str) -> bool:
        return len(line) > 0 and not line.startswith('#')

    while True:
        if is_code(lines[no]) or no == -1:
            return no
        else:
            no -= 1

import io
from collections import OrderedDict
from dataclasses import field
from typing import Any, Dict, Iterable, Iterator, List, Optional, Union

from pheasant.core.base import Base
from pheasant.core.decorator import monitor
from pheasant.core.page import Page
from pheasant.core.parser import Parser
from pheasant.core.renderer import Renderer


class Converter(Base):
    parsers: Dict[str, Parser] = field(default_factory=OrderedDict)
    renderers: Dict[str, List[Renderer]] = field(default_factory=dict)
    pages: Dict[str, Page] = field(default_factory=dict)

    def __post_init__(self):
        super().__post_init__()
        self.init()

    def __post_repr__(self):
        return ", ".join(f"'{name}'" for name in self.parsers)

    def __getitem__(self, item):
        if isinstance(item, str):
            return self.parsers[item]
        elif isinstance(item, tuple):
            renderers = self.renderers[item[0]]
            for renderer in renderers:
                if renderer.name == item[1]:
                    return renderer
            else:
                raise KeyError

    def renderer_iter(self) -> Iterator[Renderer]:
        for renderers in self.renderers.values():
            yield from renderers

    def update_config(self, config: Dict[str, Any]):
        for renderer in self.renderer_iter():
            if renderer.name in config:
                renderer._update("config", config[renderer.name])

    def init(self) -> None:
        """Called from __post_init__."""
        pass

    def reset(self):
        for renderer in self.renderer_iter():
            renderer.reset()
        self.pages = {}

    def register(
        self,
        name: str,
        renderers: Union[Renderer, Iterable[Renderer]],
        # decorator: Optional[Decorator] = None,
    ):
        """Register renderer's processes

        Parameters
        ----------
        name
            The name of Parser
        renderers
            List of Renderer's instance or name of Renderer
        """
        if name in self.parsers:
            raise ValueError(f"Duplicated parser name '{name}'")
        parser = Parser(name)  # type: ignore
        if isinstance(renderers, Renderer):
            renderers = [renderers]
        for renderer in renderers:
            renderer.parser = parser
        self.parsers[name] = parser
        self.renderers[name] = list(renderers)

    def convert(
        self, source: str, names: Optional[Union[str, Iterable[str]]] = None
    ) -> str:
        """Convert source text.

        Parameters
        ----------
        source
            The source text to be converted.
        names
            Parser names to be used. If not specified. all of the registered
            parsers will be used.

        Returns
        -------
        Converted output text.
        """
        if isinstance(names, str):
            names = [names]
        for name in names or self.parsers:
            parser = self.parsers[name]
            source = parser.parse(source)

        return source

    @monitor(format=True)
    def convert_from_file(
        self, path: str, names: Optional[Union[str, Iterable[str]]] = None
    ) -> str:
        with io.open(path, "r", encoding="utf-8-sig", errors="strict") as f:
            source = f.read()

        break_str = "<!-- break -->"
        if break_str in source:
            source = source.split(break_str)[0]

        page = Page(path, source=source)  # type: ignore
        self.pages[path] = page
        page.output = self.convert(source, names)
        return page.output

    @monitor(format=True)
    def convert_from_output(
        self, path: str, names: Optional[Union[str, Iterable[str]]] = None
    ) -> str:
        page = self.pages[path]
        page.output = self.convert(page.output, names)
        return page.output

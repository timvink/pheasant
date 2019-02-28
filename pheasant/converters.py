from typing import Optional

from pheasant.config import config as pheasant_config
from pheasant.utils import read_source


def get_converters() -> list:
    return pheasant_config['converters']


def set_converters(converters: list) -> None:
    pheasant_config['converters'] = converters


def get_source_file() -> Optional[str]:
    return pheasant_config['source_file']


def get_converter_name(converter) -> str:
    return converter.__name__.split('.')[-1]


def update_config(converter, config: dict) -> None:
    if not hasattr(converter, 'config'):
        converter.config = {}

    if converter.config.get('configured', False):
        return

    name = get_converter_name(converter)
    if name in config:
        converter.config['enabled'] = True
        if isinstance(config[name], dict):
            for key, value in config[name].items():
                if isinstance(value, dict):
                    converter.config[key].update(value)
                else:
                    converter.config[key] = value
    else:
        converter.config['enabled'] = False

    if hasattr(converter, 'initialize'):
        converter.initialize()  # invoke converter's initializer

    converter.config['configured'] = True


def convert(source: str, config: Optional[dict] = None) -> str:
    pheasant_config['source_file'] = source
    source = read_source(source)
    for converter in pheasant_config['converters']:
        update_config(converter, config or pheasant_config)
        if converter.config['enabled']:
            source = converter.convert(source) or source

    return source

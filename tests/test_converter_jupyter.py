import os

import pytest
from pheasant import jupyter
from pheasant.jupyter.converter import initialize
from pheasant.converters import (convert, get_converter_name, get_converters,
                                 set_converters, update_config)
from pheasant.utils import read


@pytest.fixture
def root():
    root = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(root, 'resources/mkdocs/docs'))
    return root


@pytest.fixture
def stream_output():
    return read(__file__, 'mkdocs/docs/markdown_stream_output.md')


def test_converters():
    set_converters([jupyter])
    assert get_converters() == [jupyter]


def test_get_converter_name():
    assert get_converter_name(jupyter) == 'jupyter'


def test_jupyter_config():
    assert jupyter.config['format_version'] == 4
    assert jupyter.config['kernel_name'] == {'python': 'python3'}
    assert 'configured' not in jupyter.config


def test_jupyter_update_config():
    config = {'jupyter': {'kernel_name': {'julia': 'julia'}}}
    update_config(jupyter, config)
    assert jupyter.config['kernel_name'] == {'python': 'python3',
                                             'julia': 'julia'}
    assert jupyter.config['configured'] is True


paths = ['markdown_stream_input.md', 'notebook_stream_input.ipynb']


@pytest.mark.parametrize('path', paths)
def test_convert(root, stream_output, path):
    initialize()
    source = convert(os.path.join(root, path), {})
    jupyter.config['configured'] = False

    assert source == stream_output

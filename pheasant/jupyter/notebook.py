import codecs
import re

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

from .config import config


def convert(notebook):
    """
    Convert a notebook into a markdown string.

    Parameters
    ----------
    notebook : str or Notebook object
        If str, it is a filename.

    Returns
    -------
    str or Notebook object
    """
    if isinstance(notebook, str):
        with codecs.open(notebook, 'r', 'utf8') as file:
            notebook = nbformat.read(file, as_version=config['format_version'])

    # For 'native' notebook, add language info to each code-cell.
    if 'kernelspec' in notebook.metadata:
        language = notebook.metadata.kernelspec.language
        for cell in notebook.cells:
            if cell.cell_type == 'code':
                update_cell_metadata(cell, language)

    delete_dataframe_style(notebook)

    markdown = config['exporter'].from_notebook_node(notebook)[0]
    return drop_new_line_from_img_data(markdown)


def drop_new_line_from_img_data(markdown):
    re_compile = re.compile(r'<img .+?</img>', re.DOTALL)

    def replace(m):
        return m.group().replace('\n', '')

    return re_compile.sub(replace, markdown)


def delete_dataframe_style(notebook):
    re_compile = re.compile(r'<style scoped>.+?</style>',
                            re.DOTALL | re.MULTILINE)

    for cell in notebook.cells:
        if cell.cell_type == 'code':
            for output in cell.outputs:
                if 'data' in output and 'text/html' in output.data:
                    html = re_compile.sub('', output.data['text/html'])
                    output.data['text/html'] = html


def update_cell_metadata(cell, language, option=None):
    """
    Add pheasant original metadata. This metadata is used when notebook
    is exported to markdown.
    """
    # For notebook
    if option is None and 'pheasant' in cell.metadata:
        option = cell.metadata['pheasant']

    if option:
        if isinstance(option, str):
            options = [option.strip() for option in option.split(',')]
        else:
            options = option
    else:
        options = []

    pheasant_metadata = {'options': options, 'language': language}
    cell.metadata['pheasant'] = pheasant_metadata
    return cell


def execute(notebook, timeout=None):
    """
    Execute a notebook
    """
    timeout = timeout or config['timeout']
    ep = ExecutePreprocessor(timeout=timeout)
    ep.preprocess(notebook, {})

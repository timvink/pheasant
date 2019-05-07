from pheasant.core.pheasant import Pheasant
import time


def test_pheasant(tmpdir):
    f = tmpdir.join("example.md")
    f.write("# Title\n## Section\n```python\n1\n```\n")
    path = f.strpath

    converter = Pheasant()
    output = converter.convert(path)
    assert 'pheasant-header' in output
    assert 'cell jupyter input' in output

    now = time.time()
    assert converter.pages[path].converted_time < now
    time.sleep(0.1)
    converter.convert(path)
    assert converter.pages[path].converted_time > now

    converter.dirty = True
    now = time.time()
    output = converter.convert(path)
    assert converter.pages[path].converted_time < now
    assert 'class="python">1</code>' in output

    now = time.time()
    f.write("# Title\n## Section\n```python\n2\n```\n")
    output = converter.convert(path)
    assert converter.pages[path].converted_time > now
    assert 'class="python">2</code>' in output
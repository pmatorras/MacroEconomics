#Very simple smoke test so that it can be retrieved from the pyproject. Can be updated in the future
def test_imports():
    import sys
    assert "sys" in sys.modules

def test_basic_truth():
    assert 2 + 2 == 4
from core_logic import DockStats

def test_scores_and_order():
    ds = DockStats()
    ds.record("A", "A")
    ds.record("B", "C")
    order = ds.suggest_order()
    assert order.index("A") < order.index("C")
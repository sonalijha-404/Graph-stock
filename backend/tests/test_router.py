from app.services import router


def test_classify_stock_holders():
    intent, ent = router.classify("Who owns TCS?", {"TCS"}, {"IT"})
    assert intent == "STOCK_HOLDERS"
    assert ent["symbol"] == "TCS"


def test_classify_stock_impact():
    intent, ent = router.classify("What happens if TCS drops 10%?", {"TCS"}, {"IT"})
    assert intent == "STOCK_IMPACT"
    assert ent["change_percent"] == -10


def test_classify_multi():
    intent, ent = router.classify("Who owns both TCS and Infosys?", {"TCS", "INFY"}, {"IT"})
    assert intent == "MULTI_STOCK_HOLDERS"
    assert set(ent["symbols"]) == {"TCS", "INFY"}

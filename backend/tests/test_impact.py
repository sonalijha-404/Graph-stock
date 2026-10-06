from app.services.impact import HoldingRow, impact_value, stock_impact, sector_exposure_for_customer


def test_rahul_tcs_impact():
    rows = [
        HoldingRow("C001", "Rahul Sharma", "P001", "Rahul Growth", "H001", "TCS", 100, 4000.0, "IT"),
    ]
    assert impact_value(100, 4000, -10) == -40000
    results, calcs = stock_impact(rows, "TCS", -10)
    assert results[0]["estimated_impact"] == -40000
    assert len(calcs) == 1


def test_priya_tcs_impact():
    rows = [
        HoldingRow("C002", "Priya Nair", "P010", "Priya Balanced", "H010", "TCS", 10, 4000.0, "IT"),
        HoldingRow("C002", "Priya Nair", "P010", "Priya Balanced", "H011", "SBIN", 10, 800.0, "Banking"),
        HoldingRow("C002", "Priya Nair", "P011", "Priya Pharma", "H012", "SUNPHARMA", 10, 1500.0, "Pharma"),
    ]
    results, _ = stock_impact(rows, "TCS", -10)
    assert results[0]["estimated_impact"] == -4000


def test_rahul_it_exposure():
    rows = [
        HoldingRow("C001", "Rahul Sharma", "P001", "Rahul Growth", "H001", "TCS", 100, 4000.0, "IT"),
        HoldingRow("C001", "Rahul Sharma", "P001", "Rahul Growth", "H002", "INFY", 100, 2000.0, "IT"),
        HoldingRow("C001", "Rahul Sharma", "P001", "Rahul Growth", "H003", "HDFCBANK", 100, 2000.0, "Banking"),
    ]
    out = sector_exposure_for_customer(rows, "IT", 40.0)
    rahul = next(r for r in out if r["customer_name"] == "Rahul Sharma")
    assert rahul["sector_exposure_percent"] == 75.0

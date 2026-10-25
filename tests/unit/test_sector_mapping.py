from services.sector_mapping import sector_for_symbol


def test_sector_for_known_symbol():
    assert sector_for_symbol("RELIANCE") == "Energy"
    assert sector_for_symbol("hdfcbank") == "Financials"
    assert sector_for_symbol("CHENNPETRO") == "Energy"
    assert sector_for_symbol("DHANBANK") == "Financials"
    assert sector_for_symbol("NELCAST") == "Metals"
    assert sector_for_symbol("PNGSREVA") == "Consumer"
    assert sector_for_symbol("INDIAGLYCO") == "Chemicals"


def test_recently_observed_scanner_symbols_have_sector_mappings():
    assert sector_for_symbol("J&KBANK") == "Financials"
    assert sector_for_symbol("VEDL") == "Metals"
    assert sector_for_symbol("LODHA") == "Real Estate"
    assert sector_for_symbol("LINC") == "Consumer"
    assert sector_for_symbol("SWIGGY") == "Internet"
    assert sector_for_symbol("ETERNAL") == "Internet"
    assert sector_for_symbol("AARTECH") == "Industrials"
    assert sector_for_symbol("SSWL") == "Automobile Components"


def test_sector_for_unknown_symbol_is_unclassified():
    assert sector_for_symbol("NOT_A_REAL_SYMBOL") == "Unclassified"

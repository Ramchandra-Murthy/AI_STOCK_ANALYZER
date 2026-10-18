"""Regression tests for portfolio SQLite storage initialization."""


from portfolio import portfolio


def test_load_portfolio_initializes_missing_table(tmp_path, monkeypatch) -> None:
    database = tmp_path / "stock_data.db"
    monkeypatch.setattr(portfolio, "DATABASE", str(database))

    result = portfolio.load_portfolio()

    assert result.empty
    assert list(result.columns) == ["id", "symbol", "quantity", "buy_price"]
    assert database.exists()


def test_load_portfolio_reads_existing_rows(tmp_path, monkeypatch) -> None:
    database = tmp_path / "stock_data.db"
    monkeypatch.setattr(portfolio, "DATABASE", str(database))
    portfolio.create_portfolio_table()
    portfolio.add_stock("RELIANCE.NS", 2, 100.0)

    result = portfolio.load_portfolio()

    assert len(result) == 1
    assert result.iloc[0]["symbol"] == "RELIANCE.NS"
    assert result.iloc[0]["quantity"] == 2
    assert result.iloc[0]["buy_price"] == 100.0

class RiskManager:
    def __init__(self, capital: float, max_risk_pct: float = 1.0):
        self.capital = capital
        self.max_risk_amount = capital * (max_risk_pct / 100.0)

    def calculate_position_size(self, entry_price: float, atr: float, multiplier: float = 2.0) -> dict:
        stop_loss_price = entry_price - (multiplier * atr)
        risk_per_share = entry_price - stop_loss_price
        
        if risk_per_share <= 0:
            return {'Error': 'Invalid risk parameters'}
            
        shares = int(self.max_risk_amount / risk_per_share)
        total_investment = shares * entry_price
        
        return {
            'Entry Price': round(entry_price, 2),
            'Stop Loss': round(stop_loss_price, 2),
            'Shares to Buy': shares,
            'Total Capital Committed': round(total_investment, 2),
            'Total Risk Amount': round(shares * risk_per_share, 2)
        }

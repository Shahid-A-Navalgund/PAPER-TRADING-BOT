
class InsufficientFundsError(Exception):
    pass


class InsufficientPositionError(Exception):
    pass


class Portfolio:
    def __init__(self, cash: float):
        self.cash = cash
        self.positions: dict[str, dict] = {}
        self._open_fees: dict[str, float] = {}

    def equity(self, current_prices: dict[str, float]) -> float:
        total = self.cash
        for symbol, pos in self.positions.items():
            total += pos["qty"] * current_prices[symbol]
        return total

    def apply_buy(self, symbol: str, qty: float, price: float, fee: float):
        cost = qty * price
        if cost + fee > self.cash:
            raise InsufficientFundsError(
                f"Need {cost + fee:.2f} but only have {self.cash:.2f}"
            )
        self.cash -= (cost + fee)
        self.positions[symbol] = {"qty": qty, "avg_price": price}
        self._open_fees[symbol] = fee

    def apply_sell(self, symbol: str, qty: float, price: float, fee: float) -> float:
        position = self.positions.get(symbol)
        if position is None or position["qty"] < qty:
            raise InsufficientPositionError(f"No sufficient open position in {symbol}")
        proceeds = qty * price
        self.cash += proceeds - fee
        open_fee = self._open_fees.pop(symbol, 0.0)
        cost_basis = position["avg_price"] * qty
        pnl = proceeds - fee - cost_basis - open_fee
        del self.positions[symbol]
        return pnl

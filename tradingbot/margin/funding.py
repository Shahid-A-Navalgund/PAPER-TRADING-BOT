import requests

BASE_URL = "https://fapi.binance.com/fapi/v1"


class FundingFetchError(Exception):
    pass


def get_mark_price(symbol: str) -> float:
    response = requests.get(
        f"{BASE_URL}/premiumIndex",
        params={"symbol": symbol},
        timeout=10,
    )
    if response.status_code != 200:
        raise FundingFetchError(
            f"Binance mark price fetch failed for {symbol}: HTTP {response.status_code}"
        )
    data = response.json()
    return float(data["markPrice"])


def get_funding_rate(symbol: str) -> float:
    response = requests.get(
        f"{BASE_URL}/fundingRate",
        params={"symbol": symbol, "limit": 1},
        timeout=10,
    )
    if response.status_code != 200:
        raise FundingFetchError(
            f"Binance funding rate fetch failed for {symbol}: HTTP {response.status_code}"
        )
    rows = response.json()
    return float(rows[0]["fundingRate"])

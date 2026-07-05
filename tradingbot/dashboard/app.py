import pandas as pd
import streamlit as st

from tradingbot.engine.db import (
    init_db, get_all_trades, get_open_trades, get_equity_history, get_strategy_runs,
)

DB_PATH = "tradingbot.db"

st.set_page_config(page_title="Paper Trading Bot", layout="wide")
st.title("Paper Trading Bot — Live Dashboard")
st.caption("Real live prices, fake money. Every number here is honest — losses included.")

conn = init_db(DB_PATH)

equity_history = get_equity_history(conn)
if equity_history:
    df = pd.DataFrame(equity_history)
    latest_equity = df["equity"].iloc[-1]
    starting_equity = df["equity"].iloc[0]
    st.metric(
        "Current Equity",
        f"${latest_equity:,.2f}",
        f"{latest_equity - starting_equity:+,.2f}",
    )
    st.line_chart(df.set_index("timestamp")["equity"])
else:
    st.info("No equity history yet — start the loop with `python -m tradingbot.loop.main`.")

st.subheader("Open Positions")
open_trades = get_open_trades(conn)
if open_trades:
    st.dataframe(pd.DataFrame(open_trades))
else:
    st.write("No open positions.")

st.subheader("Trade Log")
all_trades = get_all_trades(conn)
if all_trades:
    st.dataframe(pd.DataFrame(all_trades))
else:
    st.write("No trades yet.")

st.subheader("Strategy Vetting (honest pass/fail)")
strategy_runs = get_strategy_runs(conn)
if strategy_runs:
    st.dataframe(pd.DataFrame(strategy_runs))
else:
    st.write("No strategy backtests recorded yet.")

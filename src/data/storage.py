import sqlite3
import pandas as pd


class MarketStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_table()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        return conn

    def _init_table(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS daily (
                    code TEXT NOT NULL,
                    date TEXT NOT NULL,
                    open REAL, high REAL, low REAL,
                    close REAL, volume REAL, amount REAL,
                    PRIMARY KEY (code, date)
                )
                """
            )

    def save(self, df: pd.DataFrame):
        df = df.copy()
        df["date"] = df["date"].astype(str)
        with self._connect() as conn:
            df.to_sql("daily", conn, if_exists="append", index=False,
                      method="multi")

    def load(self, code: str) -> pd.DataFrame:
        with self._connect() as conn:
            df = pd.read_sql_query(
                "SELECT * FROM daily WHERE code=? ORDER BY date", conn,
                params=(code,),
            )
        df["date"] = pd.to_datetime(df["date"])
        return df
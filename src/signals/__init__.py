def build_daily_advice(
    position: float,
    picks: list[str],
    weights: dict[str, float],
    caution: str,
) -> dict:
    return {
        "position": position,
        "picks": picks,
        "weights": weights,
        "caution": caution,
    }
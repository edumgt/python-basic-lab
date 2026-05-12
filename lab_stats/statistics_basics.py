from __future__ import annotations

import math
from collections.abc import Sequence


def calculate_mean(values: Sequence[float]) -> float:
    if not values:
        raise ValueError("데이터는 최소 1개 이상이어야 합니다.")

    return sum(values) / len(values)


def calculate_deviations(values: Sequence[float], mean: float) -> list[float]:
    if not values:
        raise ValueError("데이터는 최소 1개 이상이어야 합니다.")

    return [value - mean for value in values]


def calculate_squared_deviations(values: Sequence[float]) -> list[float]:
    mean = calculate_mean(values)
    deviations = calculate_deviations(values, mean)
    return [math.pow(deviation, 2) for deviation in deviations]


def calculate_variance(values: Sequence[float], sample: bool = False) -> float:
    if not values:
        raise ValueError("데이터는 최소 1개 이상이어야 합니다.")

    if sample and len(values) < 2:
        raise ValueError("표본 분산은 데이터가 최소 2개 이상 필요합니다.")

    squared_deviations = calculate_squared_deviations(values)
    divisor = len(values) - 1 if sample else len(values)
    return sum(squared_deviations) / divisor


def calculate_standard_deviation(values: Sequence[float], sample: bool = False) -> float:
    variance = calculate_variance(values, sample=sample)
    return math.sqrt(variance)


def print_statistics(values: Sequence[float]) -> None:
    mean = calculate_mean(values)
    deviations = calculate_deviations(values, mean)
    squared_deviations = calculate_squared_deviations(values)

    print("=== 편차 / 분산 / 표준편차 실습 ===")
    print(f"원본 데이터: {values}")
    print(f"평균: {mean:.2f}")
    print(f"편차: {[round(deviation, 2) for deviation in deviations]}")
    print(f"편차 제곱: {[round(value, 2) for value in squared_deviations]}")
    print(f"모집단 분산: {calculate_variance(values):.2f}")
    print(f"표본 분산: {calculate_variance(values, sample=True):.2f}")
    print(f"모집단 표준편차: {calculate_standard_deviation(values):.2f}")
    print(f"표본 표준편차: {calculate_standard_deviation(values, sample=True):.2f}")


def main() -> None:
    sample_scores = [72, 76, 80, 84, 88]
    print_statistics(sample_scores)


if __name__ == "__main__":
    main()

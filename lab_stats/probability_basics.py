from __future__ import annotations

import math


def count_ordered_cases(n: int, r: int) -> int:
    if n < 0 or r < 0 or r > n:
        raise ValueError("n과 r은 0 이상이며 r은 n보다 클 수 없습니다.")

    return math.perm(n, r)


def count_unordered_cases(n: int, r: int) -> int:
    if n < 0 or r < 0 or r > n:
        raise ValueError("n과 r은 0 이상이며 r은 n보다 클 수 없습니다.")

    return math.comb(n, r)


def probability(favorable: int, total: int) -> float:
    if favorable < 0 or total <= 0 or favorable > total:
        raise ValueError("확률 계산에는 0 <= favorable <= total 조건이 필요합니다.")

    return favorable / total


def addition_rule(prob_a: float, prob_b: float, prob_intersection: float) -> float:
    return prob_a + prob_b - prob_intersection


def multiplication_rule(prob_a: float, prob_b_given_a: float) -> float:
    return prob_a * prob_b_given_a


def print_probability_examples() -> None:
    print("=== 경우의 수 / 확률 / 덧셈 / 곱셈 실습 ===")
    print()

    ordered_cases = count_ordered_cases(5, 2)
    unordered_cases = count_unordered_cases(5, 2)
    print(f"5명 중 반장·부반장 뽑기(순서 중요): {ordered_cases}")
    print(f"5명 중 대표 2명 뽑기(순서 무관): {unordered_cases}")
    print()

    even_probability = probability(3, 6)
    print(f"주사위에서 짝수가 나올 확률: {even_probability:.4f} = 1/2")
    print()

    prob_heart = 13 / 52
    prob_king = 4 / 52
    prob_heart_king = 1 / 52
    addition_result = addition_rule(prob_heart, prob_king, prob_heart_king)
    print(f"카드 1장에서 하트 또는 K가 나올 확률: {addition_result:.4f} = 4/13")
    print()

    first_red = 3 / 5
    second_red_given_first_red = 2 / 4
    multiply_result = multiplication_rule(first_red, second_red_given_first_red)
    print(f"빨간 공 2개를 연속으로 뽑을 확률: {multiply_result:.4f} = 3/10")
    print()

    independent_result = multiplication_rule(1 / 2, 1 / 6)
    print(f"동전 앞면이 나오고 주사위가 6일 확률: {independent_result:.4f} = 1/12")


def main() -> None:
    print_probability_examples()


if __name__ == "__main__":
    main()

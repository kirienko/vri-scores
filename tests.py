from main import calculate_total, parse_ranking

def test_parse_ranking():
    message = """'**Ranking:**
1 SomePlayer
2 AnotherPlayer
5 Cool Guy
"""
    parsed = parse_ranking(message)
    assert parsed == {
        'SomePlayer': 1,
        'AnotherPlayer': 2,
        'Cool Guy': 5,
    }


def test_calculate_total():
    all_races = {
        1 : {'A':1, 'B':2, 'C':3, 'D':4},
        2 : {'A':4, 'B':5, 'C':2, 'E':3, 'F':1},
        3 : {'A':3, 'K':2, 'B':1},
    }
    total = calculate_total(all_races)
    # DNS = "Did not start" = len(all_races) + 1 = 8
    assert total == {
        'A': 8,     # 1 + 4 + 3
        'B': 8,     # 2 + 5 + 1
        'C': 13,    # 3 + 2 + DNS
        'D': 20,    # 4 + DNS + DNS
        'F': 17,    # DNS + 1 + DNS
        'E': 19,    # DNS + 3 + DNS
        'K': 18,    # DNS + DNS + 2
    }

from main import calculate_total, parse_ranking
from tie_break import sort_participants

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
        1 : {'A':1, 'B':2, 'C':3, 'D':4, 'K': 'DSQ'},
        2 : {'A':4, 'B':5, 'C':2, 'E':3, 'F':1},
        3 : {'A':3, 'K':2, 'B':1},
    }
    total = calculate_total(all_races)
    # DNS = "Did not start" = len(all_races) + 1 = 8
    # DSQ = DNF = len([k for k in race.keys() if isinstance(k, int)])
    assert total == {
        'A': 8,     # 1 + 4 + 3
        'B': 8,     # 2 + 5 + 1
        'C': 13,    # 3 + 2 + DNS
        'D': 20,    # 4 + DNS + DNS
        'F': 17,    # DNS + 1 + DNS
        'E': 19,    # DNS + 3 + DNS
        'K': 15,    # DSQ (5) + DNS + 2
    }

def test_render_table_image():
    import pandas as pd
    from main import render_table_image
    # Create the example race table DataFrame with sample data.
    df = pd.DataFrame({
        "Name": ["Some Player", "Cool Guy", "AnotherPlayer", "Чемпион", "水手", "船乗り (ふなのり) "],
        "1": [2, 5, 4, 3, 1, 6],
        "2": [1, 2, 3, 4, "DNS", 5],
        "3": [1, 2, 3, 4, "DNS", 5],
        "Total": [4, 9, 10, 11, 15, 16]
    })
    # Render the table image which should now include:
    #   - A new numbering column on the left (with an empty header).
    #   - Slightly increased row height.
    #   - Reduced width for "Race" and "Total" columns.
    #   - Left-aligned text in the first two columns.
    #   - A light lime (#CCFF99) background for odd rows.
    buf = render_table_image(df)
    data = buf.getvalue()
    # Save the PNG image to a file for inspection.
    with open("race_table.png", "wb") as f:
        f.write(data)
    # Assert that the image begins with the PNG signature.
    assert data.startswith(b'\x89PNG\r\n\x1a\n')


def test_tie_break_two_boats_by_best_scores():
    # Same totals (5) but A has the better single score (1 vs 2).
    all_races = {
        1: {'A': 1, 'B': 2},
        2: {'A': 4, 'B': 3},
    }
    totals = calculate_total(all_races)
    ordered = sort_participants(list(totals.keys()), all_races, totals)
    assert ordered == ['A', 'B']          # A wins on A8.1


def test_tie_break_two_boats_by_last_race():
    # Same totals (3) and identical sorted score lists [1,2];
    # tie should be decided by the last race: B (1) beats A (2).
    all_races = {
        1: {'A': 1, 'B': 2},
        2: {'A': 2, 'B': 1},
    }
    totals = calculate_total(all_races)
    ordered = sort_participants(list(totals.keys()), all_races, totals)
    assert ordered == ['B', 'A']          # B wins on A8.2 (last race)


def test_tie_break_three_boats():
    # Three-way tie, resolved by scores in the last race (race 3).
    all_races = {
        1: {'A': 1, 'B': 2, 'C': 3},
        2: {'A': 3, 'B': 1, 'C': 2},
        3: {'A': 2, 'B': 3, 'C': 1},
    }
    totals = calculate_total(all_races)
    ordered = sort_participants(list(totals.keys()), all_races, totals)
    assert ordered == ['C', 'A', 'B']     # C(1) < A(2) < B(3) in last race


def test_sort_participants_first_twenty_rows_from_scoreboard():
    # The first 20 rows in the shared scoreboard (races 1-5).
    # Each tuple: (rank, name, race scores for races 1..5, reported total from the table).
    raw_rows = [
        (1, "Foiled!", 1, 1, 2, 6, 6, 16),
        (2, "Yokko", 2, 2, 1, 11, 11, 27),
        (3, "kisPé", 3, 11, 8, 7, 8, 37),
        (4, "GER-7", 4, 4, 7, 12, 12, 39),
        (5, "Johannes Bahnsen", 5, 5, 4, 18, 15, 47),
        (6, "Tobias_ARVO8", 6, 6, 6, 13, 16, 47),
        (7, "Mats709", 7, 3, 5, 14, 19, 48),
        (8, "TauMeister:de", 8, 7, 3, 5, 29, 52),
        (9, "csero", 9, 13, 9, 8, 20, 59),
        (10, "Sir Toby", 10, 9, 10, 17, 21, 67),
        (11, "CNS_Franconia", 11, 12, 12, 24, 13, 72),
        (12, "Swedesailor SWEO!", 12, 11, 14, 19, 16, 72),
        (13, "Dr Krull", 13, 8, 13, 23, 20, 77),
        (14, "Erzpirat", 14, 14, 11, 21, 17, 77),
        (15, "???", 15, 15, 16, 16, 19, 81),  # names 15-20 illegible in the image
        (16, "???", 16, 19, 20, 10, 18, 83),
        (17, "???", 17, 16, 18, 20, 14, 85),
        (18, "???", 18, 18, 19, 9, 25, 89),
        (19, "???", 19, 17, 17, 22, 15, 90),
        (20, "???", 20, 20, 21, 26, 12, 99),
    ]

    assert len(raw_rows) == 20
    assert all(len(row) == 8 for row in raw_rows)

    all_races = {race_no: {} for race_no in range(1, 6)}
    participants_in_table_order = []
    totals = {}

    for rank, name, s1, s2, s3, s4, s5, expected_total in raw_rows:
        scores = [s1, s2, s3, s4, s5]
        assert sum(scores) == expected_total
        participant_key = f"{rank}. {name}"
        participants_in_table_order.append(participant_key)
        totals[participant_key] = expected_total
        for race_no, score in enumerate(scores, start=1):
            all_races[race_no][participant_key] = score

    # Shuffle the order to prove that the function sorts correctly.
    shuffled_participants = list(reversed(participants_in_table_order))
    ordered = sort_participants(shuffled_participants, all_races, totals)

    assert ordered == participants_in_table_order

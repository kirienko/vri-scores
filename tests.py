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

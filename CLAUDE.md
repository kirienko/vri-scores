# CLAUDE.md - AI Assistant Guide for vri-scores

## Project Overview

**vri-scores** is a Discord bot that extracts and tracks Virtual Regatta Inshore race results. It uses OCR to read race standings from screenshots, calculates series scores using low-point scoring (RRS Rule A4), applies tie-breaking rules (RRS Rule A8), and displays aggregated results as formatted tables.

### Core Functionality
- **OCR Extraction**: Uses Tesseract to extract rankings from race screenshots
- **Text Parsing**: Supports manual "Ranking:" text input with participant lists
- **Fuzzy Name Matching**: Corrects OCR errors using Levenshtein distance (max distance: 2)
- **Score Calculation**: Low-point scoring with DNS/DSQ/DNF handling
- **Tie-Breaking**: Implements World Sailing Rule A8 (best-to-worst, then last-race)
- **Discord Integration**: Emoji reactions (1️⃣-🔟) to label races, automatic table updates
- **Race Management**: `!reset` command to start new regattas

## Codebase Structure

```
vri-scores/
├── main.py                    # Discord bot logic, event handlers, table rendering
├── extract.py                 # OCR and text parsing for rankings
├── tie_break.py              # RRS A8 tie-breaking implementation
├── tests.py                   # pytest test suite
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Container configuration
├── docker-compose.yml         # Docker deployment setup
├── Rule_A8_series_ties.txt   # Official RRS A8 rule text reference
├── .github/workflows/         # CI/CD configuration
│   └── pytest_with_coverage.yml
└── README.md                  # User-facing documentation
```

### Module Responsibilities

#### `main.py` (344 lines)
- **Discord Event Handlers**: `on_message`, `on_reaction_add`
- **State Management**: `guild_race_tables`, `guild_all_races`, `guild_latest_table_message_id`
- **Score Calculation**: `calculate_total()`, `build_race_table()`
- **Rendering**: `render_table_image()` using matplotlib
- **Fuzzy Matching**: Levenshtein distance matching (max 2 edits) against known names
- **Table Management**: Deletes old table messages when posting new ones

#### `extract.py` (128 lines)
- **OCR Processing**: `extract_rankings_from_bytes()` with image preprocessing
- **Pattern Matching**: Two regex patterns for different ranking formats:
  - Pattern 1: `{number} - {name}` (e.g., "6 - Guest_1723161531080")
  - Pattern 2: `{number}. {flag} {name} {time/points}` (e.g., "6. 🇫🇷 Guest_1723161531080 +00:15.2")
- **Preprocessing**: Grayscale conversion, thresholding (< 160 → black), sharpening
- **Gap Filling**: Missing ranks filled with "???" in output

#### `tie_break.py` (53 lines)
- **A8.1 Implementation**: Best-to-worst score comparison
- **A8.2 Implementation**: Last-race tie-breaking
- **Scoring Translation**: Converts DNS/DSQ/DNF to numeric values
- **Sorting**: `sort_participants()` using `functools.cmp_to_key`

#### `tests.py` (96 lines)
- **Unit Tests**: `test_parse_ranking()`, `test_calculate_total()`
- **Integration Tests**: `test_tie_break_*()` scenarios
- **Visual Tests**: `test_render_table_image()` generates PNG output

## Key Components Deep Dive

### 1. Scoring System (RRS Low-Point A4)

```python
# Scoring rules:
DNS = len(all_participants) + 1         # Did Not Start
DSQ/DNF = len(actual_finishers) + 1    # Disqualified / Did Not Finish
```

**Example**:
- 6 total participants across all races
- Race 1: 5 finishers + 1 DSQ → DSQ = 6
- Race 2: 3 finishers + 3 DNS → DNS = 7

### 2. Tie-Breaking (RRS A8)

Implementation in `tie_break.py:14-37`:

**A8.1** - Best-to-worst comparison:
```python
# Sort each boat's scores, compare position by position
# First difference determines winner
```

**A8.2** - Last-race tie-breaking:
```python
# If still tied, compare last race, then next-to-last, etc.
for race_no in sorted(all_races.keys(), reverse=True):
    # Compare scores in this race
```

### 3. Fuzzy Name Matching

Located in `main.py:261-293`:

```python
max_distance = 2  # Max Levenshtein distance
# Matches OCR errors like "Guest_123" → "Guest_1234" (distance 1)
# Only matches against names seen in previous races
```

**Purpose**: Corrects OCR misreads while avoiding false positives.

### 4. Discord State Management

Per-channel state tracking using tuple keys:
```python
channel_key = (guild_id, channel_id)
guild_race_tables[channel_key] = pd.DataFrame(...)
guild_all_races[channel_key] = {race_number: {participant: position}}
guild_latest_table_message_id[channel_key] = message_id
```

### 5. Table Rendering

Uses matplotlib with specific styling (`main.py:185-239`):
- **Font**: Noto Sans CJK JP (supports Chinese/Japanese characters)
- **Layout**: Rank column + Name + Race columns + Total
- **Styling**: Odd rows have #CCFF99 background, bold Total column
- **Size**: Dynamic based on rows/columns (0.8 * 1.1 height factor)

## Development Workflows

### Setup (Local Development)

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install system dependencies
# Debian/Ubuntu:
sudo apt-get install tesseract-ocr fonts-noto-cjk

# macOS:
brew install tesseract
# Font installation varies by system

# Create token file
echo "YOUR_DISCORD_BOT_TOKEN" > token.txt

# Run bot
python main.py
```

### Setup (Docker)

```bash
# Build and run
docker-compose up --build

# The Dockerfile includes:
# - Python 3.13-slim base
# - Tesseract OCR with eng/rus/jpn language packs
# - Noto CJK fonts for multilingual support
```

### Running Tests

```bash
# Run all tests
pytest tests.py

# Run with coverage
pytest --cov=main tests.py

# Tests generate race_table.png for visual inspection
```

### CI/CD Pipeline

GitHub Actions workflow (`.github/workflows/pytest_with_coverage.yml`):
- **Trigger**: Push/PR to `main` branch
- **Environment**: Ubuntu latest, Python 3.12
- **Steps**: Install deps → Run pytest with coverage
- **Coverage Target**: `main` module

## Coding Conventions

### Naming Patterns
- **Functions**: Snake_case (`calculate_total`, `parse_ranking`)
- **Variables**: Snake_case (`guild_race_tables`, `channel_key`)
- **Constants**: UPPER_SNAKE_CASE (`VALID_PENALTIES`)
- **Private helpers**: Leading underscore (`_numeric_value`, `_compare_A8`)

### Code Organization
1. **Imports**: Grouped (standard lib → third-party → local)
2. **Configuration**: Global state variables at module level
3. **Helper Functions**: Defined before event handlers
4. **Event Handlers**: Decorated with `@client.event`
5. **Entry Point**: `if __name__ == '__main__'` block

### Error Handling
- **Discord API**: Try/except with logging for message operations
- **OCR Failures**: Silent (no reply if no rankings detected)
- **Missing Ranks**: Filled with "???" placeholder
- **Unknown Names**: Fuzzy matching or keep as-is

### Logging Strategy
```python
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')
# Used for: Race updates, fuzzy matches, message operations, errors
```

## Important Domain Logic

### Race Result Formats Supported

**Format 1** (dash separator):
```
1 - Guest_1723161531080
2 - AnotherPlayer
DSQ - SomePlayer
```

**Format 2** (dot + optional flag):
```
1. 🇫🇷 Guest_1723161531080 +00:15.2 29 pts
2. 🇺🇸 AnotherPlayer +00:30.1 25 pts
```

### Special Scores
- **DSQ**: Disqualified
- **DNF**: Did Not Finish
- **DNS**: Did Not Start (implicit - participant not in race dict)

All map to specific numeric values based on race participants.

### Race Numbering
- Uses Discord emoji reactions: 1️⃣ (race 1) through 🔟 (race 10)
- Stored as integer keys in `all_races` dict
- Race columns sorted numerically in output table

## Testing Strategy

### Test Coverage Areas
1. **Parsing**: `test_parse_ranking()` - Text format parsing
2. **Scoring**: `test_calculate_total()` - DNS/DSQ calculations
3. **Rendering**: `test_render_table_image()` - PNG generation
4. **Tie-Breaking**: Multiple scenarios (A8.1, A8.2, three-way ties)

### Test Data Patterns
```python
# Standard format:
all_races = {
    1: {'A': 1, 'B': 2, 'C': 3},        # Race 1 results
    2: {'A': 4, 'B': 5, 'C': 2},        # Race 2 results
}
```

### Adding New Tests
1. Create test function starting with `test_`
2. Use explicit assertions with expected values
3. Include edge cases (ties, special scores, missing participants)
4. Run `pytest tests.py` to verify

## Common Development Tasks

### Adding Support for New Ranking Format

1. **Update regex in `extract.py`**:
   ```python
   # Add new pattern to parse_rankings_from_text()
   ranking_pattern_new = re.compile(r'your_pattern_here')
   ```

2. **Add test case in `tests.py`**:
   ```python
   def test_parse_new_format():
       message = """Your test input"""
       parsed = parse_ranking(message)
       assert parsed == expected_output
   ```

### Modifying Tie-Breaking Logic

1. **Edit `tie_break.py`**: Update `_compare_A8()` or `_cmp()`
2. **Update tests**: Add new test scenarios in `tests.py`
3. **Document changes**: Update `Rule_A8_series_ties.txt` if needed
4. **Verify**: Run `pytest tests.py` to ensure existing behavior preserved

### Changing Table Styling

1. **Locate rendering code**: `main.py:185-239` (`render_table_image()`)
2. **Modify matplotlib parameters**:
   - Colors: `set_facecolor()` calls
   - Fonts: `plt.rcParams['font.family']`
   - Layout: `figsize`, cell alignment
3. **Test visually**: Run `pytest` and check `race_table.png`

### Adding New Discord Commands

1. **Add command handler in `on_message()`**:
   ```python
   if message.content.strip() == "!yourcommand":
       # Handle command logic
       await message.reply("Response")
       return
   ```

2. **Update state if needed**: Modify `guild_*` dictionaries
3. **Document**: Update README.md with new command

## Dependencies

### Core Libraries
- **discord**: Discord API integration (v2.x)
- **aiohttp**: Async HTTP for image downloads
- **pytesseract**: OCR wrapper for Tesseract
- **Pillow (PIL)**: Image processing and preprocessing
- **pandas**: DataFrame manipulation for tables
- **matplotlib**: Table rendering to PNG
- **rapidfuzz**: Levenshtein distance for fuzzy matching
- **pytest**: Testing framework

### System Dependencies
- **tesseract-ocr**: OCR engine (required)
- **fonts-noto-cjk**: CJK character support (required for multilingual names)

## Git Workflow Conventions

### Branch Strategy
- **main**: Production-ready code
- Feature branches: Use descriptive names (e.g., `feature/medal-races`)

### Commit Messages
- Use present tense ("Add feature" not "Added feature")
- Reference issues when applicable
- Examples from history:
  - "Add support for the RRS A8 rule for tie-breaking"
  - "Add fuzzy name detection using Levenshtein distance"

### Pre-Commit Checks
1. Run tests: `pytest tests.py`
2. Verify no import errors: `python -c "import main, extract, tie_break"`
3. Check for syntax errors in new code

## Known Limitations & Future Work

### Not Yet Supported (from README.md)
- Medal races
- Worst race(s) exclusion (discard rules)
- Non-integer scores

### OCR Challenges
- Recognition quality varies with screenshot clarity
- "Fast and cheap OCR" trade-off acknowledged
- Fuzzy matching mitigates but doesn't eliminate errors

### Design Constraints
- **Single table per channel**: Old tables deleted when new one posted
- **No auto-update on edit**: Must re-react to update race results
- **Token storage**: `token.txt` file required (not in version control)

## Troubleshooting Guide

### "No rankings detected in image"
- Check image clarity and contrast
- Verify Tesseract is installed: `tesseract --version`
- Test preprocessing: Inspect grayscale/threshold values in `extract.py:85-92`

### Fuzzy matching too aggressive/conservative
- Adjust `max_distance` in `main.py:262` (default: 2)
- Lower = stricter matching, higher = more corrections

### Table rendering issues
- **Font errors**: Ensure `fonts-noto-cjk` installed
- **Layout problems**: Adjust `figsize` multipliers in `main.py:204`
- **Colors**: Modify `set_facecolor()` values

### Docker container not starting
- Check token.txt is mounted or created
- Verify Tesseract languages installed (eng, rus, jpn)
- Review logs: `docker-compose logs vri-scores-bot`

## File Change Impact Matrix

| File Modified | Requires Tests | May Affect | Risk Level |
|---------------|----------------|------------|------------|
| `extract.py` | Yes | OCR accuracy, parsing | Medium |
| `tie_break.py` | Yes | Race standings order | High |
| `main.py` scoring | Yes | Total calculations | High |
| `main.py` rendering | Optional | Visual output only | Low |
| `main.py` Discord events | Manual testing | Bot behavior | Medium |
| `tests.py` | No | Test coverage | Low |
| `requirements.txt` | CI test | Dependencies | Medium |
| Dockerfile | Build test | Deployment | Medium |

## Best Practices for AI Assistants

### Before Making Changes
1. **Read the affected files**: Use Read tool on relevant modules
2. **Check tests**: Understand existing test coverage
3. **Verify dependencies**: Check if change affects multiple modules
4. **Review domain logic**: Understand RRS rules if modifying scoring/tie-breaking

### When Adding Features
1. **Start with tests**: Write test cases first (TDD approach)
2. **Follow existing patterns**: Match naming conventions and code structure
3. **Update documentation**: Modify README.md and this file
4. **Consider state management**: How does it affect per-channel data?

### When Fixing Bugs
1. **Reproduce first**: Add test case that demonstrates the bug
2. **Fix minimally**: Change only what's necessary
3. **Verify fix**: Ensure test passes and existing tests still pass
4. **Document**: Add comment if logic is non-obvious

### Code Review Checklist
- [ ] Functions have clear single responsibility
- [ ] Error cases handled (Discord API, OCR failures, missing data)
- [ ] Logging added for important operations
- [ ] Tests cover new/modified code paths
- [ ] No hardcoded values (use constants or config)
- [ ] Unicode/multilingual support maintained
- [ ] Consistent with existing code style

## Quick Reference

### Key Functions
- `parse_ranking()` → Parse "Ranking:" text to dict
- `calculate_total()` → Sum race scores with DNS/DSQ handling
- `build_race_table()` → Create sorted DataFrame with tie-breaking
- `sort_participants()` → Apply A8 rules to tied boats
- `extract_rankings_from_bytes()` → OCR + preprocessing pipeline
- `render_table_image()` → DataFrame to PNG with styling

### Key Variables
- `guild_race_tables[channel_key]` → DataFrame of current standings
- `guild_all_races[channel_key]` → Dict of all race results {race_num: {participant: position}}
- `guild_latest_table_message_id[channel_key]` → Last posted table message ID
- `emoji_to_int` → Maps emoji reactions to race numbers

### State Reset Triggers
- `!reset` command → Clears all channel state except last message
- Bot restart → All in-memory state lost (no persistence)

### File Paths to Check
- `/home/user/vri-scores/` → Repository root
- `token.txt` → Discord bot token (not in git)
- `race_table.png` → Generated by tests for visual inspection

---

**Last Updated**: 2025-12-25
**Repository**: https://github.com/kirienko/vri-scores (inferred)
**Python Version**: 3.12+ (tested), 3.13 (Docker)
**Discord.py Version**: 2.x (intents required)

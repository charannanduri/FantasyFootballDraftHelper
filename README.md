# Fantasy Football Draft Helper

A simple CLI tool to track available players during your fantasy draft while you draft in ESPN (or any platform). It reads a CSV draft board (exported from your own source), shows the top 3 overall and top 5 by position, and lets you remove players as they’re drafted. Includes an undo command.

## Features
- Track availability: remove players as they’re drafted elsewhere
- Quick recommendations:
  - Top 3 overall (prefers overall Rank when available)
  - Top 5 by position (QB, RB, WR, TE, K, DST)
- Flexible name matching (full/partial/last name)
- Handles duplicate last names with a numbered selection
- Undo last removal(s)
- Save remaining board to a CSV

## Quickstart

1) Clone the repo
```bash
git clone https://github.com/<your-username>/FantasyFootballDraft.git
cd FantasyFootballDraft
```

2) (Recommended) Create and activate a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

3) Install dependencies
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

4) Place your draft board CSV in the project folder (not committed)
- The tool defaults to `custom_ranked_draftboard.csv`
- Or you can pass a specific path when running

5) Run the tool
```bash
# Default CSV name in repo root
python draft_helper.py

# Or specify a CSV path explicitly
python draft_helper.py /path/to/your/custom_ranked_draftboard.csv
```

## Commands (while running)
- top: show top 3 overall available
- QB / RB / WR / TE / K / DST: show top 5 available at that position
- <name> or remove <name>: remove a drafted player (handles duplicates by prompting)
- undo [n]: restore last removed player(s), default n=1
- save <file.csv>: save remaining board to a CSV
- quit: exit

## CSV expectations
The script tries to normalize common column names. It works best if your CSV includes some of the following:
- Full Name, Position, Team Abbrev/Team
- Adjusted Projected Points / Projected Fantasy Points
- Rank (overall) and Positional Rank if available

If `Rank` is present, the overall top 3 uses it; otherwise, it falls back to points.

## Notes
- CSV files are ignored by `.gitignore` and won’t be committed by default.
- This tool doesn’t draft for you; it only tracks availability while you draft elsewhere. 
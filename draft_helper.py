
# draft_helper.py
# Quick interactive draft assistant for CSV export from ChatGPT step.
# Usage:
#   python3 draft_helper.py /path/to/custom_ranked_draftboard_sortable.csv
# If no path is given, it looks for 'custom_ranked_draftboard_sortable.csv' in the current folder.

import sys
import re
import pandas as pd

DEFAULT_FILE = "custom_ranked_draftboard.csv"

def normalize_name(name: str) -> str:
    # Lowercase, remove non-letters, drop suffixes like Jr., Sr., III
    n = re.sub(r"[^a-zA-Z'\s]", '', name).strip().lower()
    # remove common suffix tokens
    toks = [t for t in n.split() if t not in {'jr', 'sr', 'ii', 'iii', 'iv', 'v'}]
    return ' '.join(toks)

def last_name(name: str) -> str:
    n = normalize_name(name)
    parts = n.split()
    return parts[-1] if parts else n

def load_df(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Expected columns from the earlier export:
    # 'Full Name','Position','Team Abbrev','Adjusted Projected Points','Projected Fantasy Points','ADP','Positional Rank','Auction Value','Rank','ADP Trend'
    # Fallbacks if columns differ slightly
    rename_map = {
        'Full Name': 'Full Name',
        'Position': 'Position',
        'Team Abbrev': 'Team',
        'Adjusted Projected Points': 'AdjPts',
        'Projected Fantasy Points': 'ProjPts',
        'ADP': 'ADP',
        'Positional Rank': 'PosRank',
        'Auction Value': 'Auc$',
        'Rank': 'Rank',
        'ADP Trend': 'ADP Trend',
    }
    # Normalize columns present
    cols = {}
    for k,v in rename_map.items():
        if k in df.columns:
            cols[k] = v
    df = df.rename(columns=cols)

    # Keep only relevant columns for display
    keep = [c for c in ['Full Name','Position','Team','AdjPts','ProjPts','ADP','PosRank','Auc$','Rank'] if c in df.columns]
    df = df[keep].copy()

    # Sorting key (highest first)
    sort_key = 'AdjPts' if 'AdjPts' in df.columns else ('ProjPts' if 'ProjPts' in df.columns else None)
    if sort_key is None:
        raise ValueError('Could not find Adjusted or Projected points in the file.')

    # Clean types
    for col in ['AdjPts','ProjPts','ADP']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.sort_values(by=sort_key, ascending=False).reset_index(drop=True)

    # Add helper columns
    df['__name_norm'] = df['Full Name'].apply(normalize_name)
    df['__lname'] = df['Full Name'].apply(last_name)
    df['__available'] = True

    return df, sort_key

def show_top(df, sort_key, n=3, pos=None):
    avail = df[df['__available']]
    if pos:
        avail = avail[avail['Position'].str.upper() == pos.upper()]
    # Choose selection logic: overall uses Rank if available; position uses points
    if pos:
        top = avail.nlargest(n, sort_key)
    else:
        if 'Rank' in avail.columns:
            top = avail.nsmallest(n, 'Rank')
        else:
            top = avail.nlargest(n, sort_key)
    if top.empty:
        print("No players available" + (f" at {pos}" if pos else ''))
        return
    display_cols = [c for c in ['Full Name','Position','Team',sort_key,'ADP','PosRank','Rank'] if c in top.columns]
    print("\n" + (f"Top {n} available ({pos}):" if pos else f"Top {n} available:"))
    print(top[display_cols].to_string(index=False))

def mark_drafted(df, query: str):
    # If query is quoted, try exact full-name match first
    q = query.strip()
    candidates = None

    if ' ' in q and any(ch.isalpha() for ch in q):
        # Try full-name contains match (case-insensitive)
        qn = normalize_name(q)
        mask = df['__available'] & df['__name_norm'].str.contains(qn, regex=False)
        candidates = df[mask]

    if candidates is None or candidates.empty:
        # Fall back to last-name match
        ql = re.sub(r"[^a-zA-Z]", '', q).lower()
        mask = df['__available'] & (df['__lname'] == ql)
        candidates = df[mask]

    if candidates.empty:
        print(f"No available player matched '{query}'. Try typing more of the name.")
        return None

    if len(candidates) == 1:
        idx = candidates.index[0]
        df.loc[idx, '__available'] = False
        print(f"Removed from available: {df.loc[idx, 'Full Name']} ({df.loc[idx, 'Position']}, {df.loc[idx, 'Team']})")
        return idx

    # If multiple, ask user to choose using a simple 1..N list
    print("Multiple matches found. Select the number of the player to remove:")
    display_cols = [c for c in ['Full Name','Position','Team','AdjPts','ProjPts','ADP','PosRank'] if c in candidates.columns]
    tmp = candidates[display_cols].copy().reset_index()  # keep original df index in 'index'
    tmp.insert(0, '#', range(1, len(tmp) + 1))  # 1-based numbering for display
    print(tmp[['#'] + display_cols].to_string(index=False))
    while True:
        sel = input("# > ").strip()
        if not sel.isdigit():
            print("Enter a number from the list (e.g., 1, 2, 3 ...).")
            continue
        sel_num = int(sel)
        if 1 <= sel_num <= len(tmp):
            real_idx = tmp.iloc[sel_num - 1]['index']  # map from display number to real df index
            df.loc[real_idx, '__available'] = False
            print(f"Removed from available: {df.loc[real_idx, 'Full Name']} ({df.loc[real_idx, 'Position']}, {df.loc[real_idx, 'Team']})")
            return real_idx
        print("Out of range. Please select a valid number from the list.")

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_FILE
    df, sort_key = load_df(path)

    print("Loaded players:", len(df))
    print("Commands:")
    print("  <name>              -> remove player from available (last name or part/full name)")
    print("  remove <name>       -> same as above; explicitly remove by name")
    print("  QB/RB/WR/TE/K/DST   -> show top 5 available at that position")
    print("  top                 -> show top 3 overall available")
    print("  list <pos>          -> same as typing the position code (shows 5)")
    print("  save <file.csv>     -> save remaining board to CSV")
    print("  undo [n]            -> restore last removed player(s), default n=1")
    print("  help                -> show commands")
    print("  quit                -> exit\n")

    show_top(df, sort_key, n=3)

    # history stack of removed indices for undo
    history = []

    while True:
        try:
            cmd = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not cmd:
            continue

        up = cmd.upper()
        if up in {"QB","RB","WR","TE","K","DST"}:
            show_top(df, sort_key, n=5, pos=up)
            continue

        if up == "TOP":
            show_top(df, sort_key, n=3)
            continue

        if up.startswith("LIST "):
            pos = up.split(None,1)[1].strip()
            show_top(df, sort_key, n=5, pos=pos)
            continue

        # undo command
        if up == "UNDO" or up.startswith("UNDO "):
            count = 1
            if up.startswith("UNDO "):
                arg = cmd.split(None,1)[1].strip()
                if arg.isdigit():
                    count = int(arg)
                else:
                    print("Usage: undo [n]")
                    continue
            restored = 0
            while count > 0 and history:
                idx = history.pop()
                if idx in df.index and not bool(df.loc[idx, '__available']):
                    df.loc[idx, '__available'] = True
                    print(f"Restored: {df.loc[idx, 'Full Name']} ({df.loc[idx, 'Position']}, {df.loc[idx, 'Team']})")
                    restored += 1
                count -= 1
            if restored == 0:
                print("Nothing to undo.")
            show_top(df, sort_key, n=3)
            continue

        # explicit remove command
        if up.startswith("REMOVE ") or up.startswith("RM "):
            q = cmd.split(None,1)[1].strip()
            idx = mark_drafted(df, q)
            if idx is not None:
                history.append(idx)
            show_top(df, sort_key, n=3)
            continue

        if up.startswith("SAVE "):
            out = cmd.split(None,1)[1].strip()
            avail = df[df['__available']].copy()
            # Drop helper cols
            for c in ['__name_norm','__lname','__available']:
                if c in avail.columns:
                    del avail[c]
            avail.to_csv(out, index=False)
            print(f"Saved remaining board to {out}")
            continue

        if up in {"HELP","H","?"}:
            print("Commands:")
            print("  <name>              -> remove player from available (last name or part/full name)")
            print("  remove <name>       -> same as above; explicitly remove by name")
            print("  QB/RB/WR/TE/K/DST   -> show top 5 available at that position")
            print("  top                 -> show top 3 overall available")
            print("  list <pos>          -> same as typing the position code (shows 5)")
            print("  save <file.csv>     -> save remaining board to CSV")
            print("  undo [n]            -> restore last removed player(s), default n=1")
            print("  quit                -> exit")
            continue

        if up in {"QUIT","EXIT","Q"}:
            print("Bye!")
            break

        # Otherwise, treat the input as a name (last name or more of name) to remove from availability
        idx = mark_drafted(df, cmd)
        if idx is not None:
            history.append(idx)
        show_top(df, sort_key, n=3)

if __name__ == "__main__":
    main()

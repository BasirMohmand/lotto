import io
import math
import json
import time
import sqlite3
import uuid
from collections import Counter
from datetime import datetime, date
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# ============================================================
# LOTTOSTAT ENTERPRISE 3.16 — MOBILE-FRIENDLY LAYOUT
# Historical analysis and transparent ticket-generation tools.
# Lottery draws are independent; historical patterns do not
# predict or improve the probability of a future draw.
# ============================================================

st.set_page_config(
    page_title="LottoStat Enterprise 3.16",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="collapsed",
)

LOTTO_MAX_50_DATE = pd.Timestamp("2019-05-14")
LOTTO_MAX_52_DATE = pd.Timestamp("2026-04-14")
LOTTO_MAX_LAUNCH_DATE = pd.Timestamp("2009-09-25")
NUMBER_COLUMNS = [f"Num{i}" for i in range(1, 8)]
GAME_CONFIG = {
    "Lotto Max": {"draw_size": 7, "current_max": 52, "lines": 4},
    "Lotto 6/49": {"draw_size": 6, "current_max": 49, "lines": 3},
}

# ---------------------------- STYLING ----------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Courier+Prime:wght@400;700&display=swap');
html, body, [class*="css"] {font-family:'Plus Jakarta Sans',sans-serif!important;background:#f8fafc;}
#MainMenu, footer, header {visibility:hidden;}
.block-container {max-width:1450px!important;padding-top:1.1rem!important;}
.header-title {font-size:clamp(30px,4vw,48px);font-weight:800;background:linear-gradient(135deg,#0f172a,#2563eb);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-align:center;letter-spacing:-1.8px;margin-bottom:3px;}
.header-subtitle {font-size:12px;color:#2563eb;font-weight:800;letter-spacing:3px;text-transform:uppercase;text-align:center;margin-bottom:25px;}
.status-bar {display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;background:#fff;padding:12px 20px;border-radius:14px;border:1px solid #e2e8f0;margin-bottom:22px;font-size:12px;font-weight:700;color:#64748b;}
.status-dot {height:8px;width:8px;background:#10b981;border-radius:50%;display:inline-block;margin-right:7px;}
.stTabs [data-baseweb="tab-list"] {gap:8px;background:#f1f5f9;padding:7px;border-radius:14px;border:1px solid #e2e8f0;}
.stTabs [data-baseweb="tab"] {border-radius:9px;padding:10px 18px;font-weight:700;}
.ticket-card {background:#fff;border:1px solid #e2e8f0;border-top:5px solid #2563eb;border-radius:18px;padding:20px;box-shadow:0 12px 28px rgba(15,23,42,.06);height:100%;margin-bottom:12px;}
.ticket-card.purple {border-top-color:#c026d3;}
.ticket-card.teal {border-top-color:#0d9488;}
.ticket-heading {display:flex;justify-content:space-between;gap:8px;border-bottom:2px dashed #cbd5e1;padding-bottom:12px;margin-bottom:16px;font-family:'Courier Prime',monospace;font-size:12px;font-weight:700;text-transform:uppercase;color:#0f172a;}
.ball-row {display:flex;flex-wrap:wrap;gap:8px;justify-content:center;margin:12px 0 18px;}
@keyframes ballRollIn {0%{opacity:0;transform:translateX(-55px) rotate(-240deg) scale(.55)}70%{opacity:1;transform:translateX(5px) rotate(18deg) scale(1.08)}100%{opacity:1;transform:translateX(0) rotate(0) scale(1)}}
.rolling-ball {animation:ballRollIn .42s cubic-bezier(.2,.8,.2,1) both;}
.ball {display:inline-flex;align-items:center;justify-content:center;width:42px;height:42px;border-radius:50%;color:white;font-weight:800;background:linear-gradient(135deg,#1e3a8a,#3b82f6);box-shadow:0 4px 10px rgba(37,99,235,.24);border:1px solid #93c5fd;}
.purple .ball {background:linear-gradient(135deg,#86198f,#c026d3);border-color:#f0abfc;box-shadow:0 4px 10px rgba(192,38,211,.24);}
.teal .ball {background:linear-gradient(135deg,#0f766e,#14b8a6);border-color:#99f6e4;box-shadow:0 4px 10px rgba(13,148,136,.24);}
.line-label {font-family:'Courier Prime',monospace;color:#94a3b8;font-size:11px;font-weight:700;margin:10px 0 2px;}
.metric-grid {display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin-top:12px;}
.metric {background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:10px;text-align:center;}
.metric small {display:block;color:#64748b;font-size:9px;font-weight:800;letter-spacing:.6px;text-transform:uppercase;}
.metric b {display:block;color:#0f172a;font-size:17px;margin-top:3px;}
.note {background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;padding:12px 14px;color:#1e3a8a;font-size:12px;}
.warning-note {background:#fffbeb;border:1px solid #fde68a;border-radius:10px;padding:12px 14px;color:#92400e;font-size:12px;}
.footer {text-align:center;color:#94a3b8;font-size:11px;margin-top:35px;padding-top:18px;border-top:1px solid #e2e8f0;}
div[data-testid="stButton"] button[kind="primary"] {background:linear-gradient(135deg,#2563eb,#1d4ed8);border:0;border-radius:11px;font-weight:800;letter-spacing:.4px;padding:12px;}

/* ---------------- MOBILE LAYOUT ---------------- */
@media (max-width: 768px) {
  .block-container {padding: .75rem .8rem 2rem!important; max-width:100%!important;}
  .header-title {font-size:30px; letter-spacing:-1px; line-height:1.15; margin-top:8px;}
  .header-subtitle {font-size:9px; letter-spacing:1.4px; line-height:1.5; margin:8px 0 18px;}
  .status-bar {display:grid; grid-template-columns:1fr; gap:7px; padding:11px 13px; margin-bottom:14px; font-size:11px;}
  .stTabs [data-baseweb="tab-list"] {display:flex; flex-wrap:nowrap; overflow-x:auto; gap:4px; padding:5px; scrollbar-width:thin;}
  .stTabs [data-baseweb="tab"] {flex:0 0 auto; padding:9px 11px; font-size:12px; white-space:nowrap;}
  div[data-testid="stHorizontalBlock"] {flex-wrap:wrap!important; gap:.65rem!important;}
  div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {flex:1 1 100%!important; min-width:100%!important; width:100%!important;}
  .ticket-card {padding:14px 12px; border-radius:14px; margin-bottom:10px;}
  .ticket-heading {font-size:10px; padding-bottom:9px; margin-bottom:11px;}
  .ball-row {gap:6px; margin:10px 0 13px;}
  .ball {width:36px; height:36px; font-size:13px;}
  .metric-grid {gap:5px;}
  .metric {padding:8px 4px;}
  .metric small {font-size:8px; letter-spacing:.2px;}
  .metric b {font-size:15px;}
  .note, .warning-note {font-size:11px; padding:10px; line-height:1.5;}
  div[data-testid="stButton"] button {width:100%; min-height:46px; white-space:normal; line-height:1.25;}
  div[data-testid="stDataFrame"], div[data-testid="stTable"] {overflow-x:auto!important;}
  h1, h2, h3 {line-height:1.2!important;}
  [data-testid="stSidebar"] {min-width: min(85vw, 320px)!important;}
}
@media (max-width: 380px) {
  .block-container {padding-left:.55rem!important; padding-right:.55rem!important;}
  .header-title {font-size:26px;}
  .ball {width:33px;height:33px;font-size:12px;}
  .metric-grid {grid-template-columns:repeat(3,minmax(0,1fr));}
}
</style>
""", unsafe_allow_html=True)


# ---------------------------- SAVED TICKETS ----------------------------
APP_DIR = Path(__file__).resolve().parent
TICKET_DB = APP_DIR / "saved_tickets.sqlite3"


def init_ticket_db():
    with sqlite3.connect(TICKET_DB) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS ticket_batches (
            batch_id TEXT PRIMARY KEY,
            game TEXT NOT NULL,
            draw_date TEXT NOT NULL,
            generated_at TEXT NOT NULL,
            generation_seed INTEGER,
            tickets_json TEXT NOT NULL,
            winning_numbers_json TEXT,
            checked_at TEXT
        )""")


def save_ticket_batch(game, draw_date, seed, tickets):
    batch_id = uuid.uuid4().hex[:12].upper()
    payload = {name: [[int(n) for n in line] for line in lines]
               for name, lines in tickets.items()}
    with sqlite3.connect(TICKET_DB) as conn:
        conn.execute(
            "INSERT INTO ticket_batches (batch_id, game, draw_date, generated_at, generation_seed, tickets_json) VALUES (?, ?, ?, ?, ?, ?)",
            (batch_id, game, draw_date.isoformat(), datetime.now().isoformat(timespec="seconds"),
             int(seed), json.dumps(payload))
        )
    return batch_id


def load_ticket_batches(game=None):
    with sqlite3.connect(TICKET_DB) as conn:
        conn.row_factory = sqlite3.Row
        if game:
            rows = conn.execute("SELECT * FROM ticket_batches WHERE game=? ORDER BY generated_at DESC", (game,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM ticket_batches ORDER BY generated_at DESC").fetchall()
    return [dict(row) for row in rows]


def update_ticket_batch_result(batch_id, winning_numbers):
    with sqlite3.connect(TICKET_DB) as conn:
        conn.execute(
            "UPDATE ticket_batches SET winning_numbers_json=?, checked_at=? WHERE batch_id=?",
            (json.dumps([int(n) for n in winning_numbers]), datetime.now().isoformat(timespec="seconds"), batch_id)
        )


init_ticket_db()

# ---------------------------- DATA ----------------------------
def lotto_max_pool_size(draw_date):
    """Historical LOTTO MAX main-number pool for the date of the draw."""
    date = pd.Timestamp(draw_date)
    if date < LOTTO_MAX_LAUNCH_DATE:
        return 0
    if date < LOTTO_MAX_50_DATE:
        return 49
    if date < LOTTO_MAX_52_DATE:
        return 50
    return 52


def game_pool_size(game, draw_date):
    return 49 if game == "Lotto 6/49" else lotto_max_pool_size(draw_date)


def read_and_prepare(raw_df: pd.DataFrame):
    required = {"Date", *NUMBER_COLUMNS}
    missing = required.difference(raw_df.columns)
    if missing:
        raise ValueError(f"CSV is missing required columns: {', '.join(sorted(missing))}")

    data = raw_df.copy()
    data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
    for col in NUMBER_COLUMNS:
        data[col] = pd.to_numeric(data[col], errors="coerce")

    issues = []
    valid_rows = []
    invalid_date_rows = data["Date"].isna()
    for idx in data.index[invalid_date_rows]:
        issues.append((idx, "missing or invalid draw date"))
    data = data.loc[~invalid_date_rows].copy()
    for idx, row in data.iterrows():
        present = [pd.notna(row[c]) for c in NUMBER_COLUMNS]
        size = sum(present)
        if size not in (6, 7):
            issues.append((idx, f"expected 6 or 7 main numbers; found {size}"))
            continue
        # Require the number columns to be contiguous (Num1..Num6/7).
        if present[:size] != [True] * size or any(present[size:]):
            issues.append((idx, "number columns are not contiguous"))
            continue
        raw_values = [row[c] for c in NUMBER_COLUMNS[:size]]
        if any(not float(v).is_integer() for v in raw_values):
            issues.append((idx, "non-integer number in draw"))
            continue
        values = [int(v) for v in raw_values]
        game = "Lotto Max" if size == 7 else "Lotto 6/49"
        max_allowed = game_pool_size(game, row["Date"])
        if max_allowed == 0:
            issues.append((idx, "Lotto Max date predates game launch"))
            continue
        if len(set(values)) != size:
            issues.append((idx, "duplicate number in draw"))
            continue
        if any(v < 1 or v > max_allowed for v in values):
            issues.append((idx, f"number outside valid {game} range 1-{max_allowed}"))
            continue
        valid_rows.append(idx)

    data = data.loc[valid_rows].copy().reset_index(drop=True)
    data["DrawSize"] = data[NUMBER_COLUMNS].notna().sum(axis=1)
    data["Game"] = np.where(data["DrawSize"].eq(7), "Lotto Max", "Lotto 6/49")
    data = data.sort_values("Date").reset_index(drop=True)
    duplicate_game_dates = data.duplicated(subset=["Date", "Game"], keep=False)
    if duplicate_game_dates.any():
        for idx in data.index[duplicate_game_dates]:
            issues.append((idx, "duplicate draw date for the same game"))
        data = data.loc[~duplicate_game_dates].copy().reset_index(drop=True)

    data["Numbers"] = data.apply(
        lambda r: tuple(int(r[c]) for c in NUMBER_COLUMNS[:int(r["DrawSize"])]),
        axis=1,
    )
    data["Sum"] = data["Numbers"].apply(sum)
    data["OddCount"] = data["Numbers"].apply(lambda ns: sum(n % 2 for n in ns))
    data["LowCount"] = data.apply(
        lambda r: sum(n <= (game_pool_size(r["Game"], r["Date"]) // 2) for n in r["Numbers"]),
        axis=1,
    )
    return data, issues


@st.cache_data(show_spinner=False)
def load_local_csv(path_string: str):
    return pd.read_csv(path_string)


def get_source_data():
    uploaded = st.sidebar.file_uploader("Upload / replace olg_data.csv", type=["csv"])
    if uploaded is not None:
        return pd.read_csv(io.BytesIO(uploaded.getvalue())), "Uploaded CSV"
    local_path = Path(__file__).with_name("olg_data.csv")
    if local_path.exists():
        return load_local_csv(str(local_path)), "olg_data.csv"
    return None, "No CSV found"


# ---------------------------- STATISTICS ----------------------------
def number_counts(draws, max_number):
    counts = np.zeros(max_number + 1, dtype=int)
    for draw in draws:
        for n in draw:
            if 1 <= n <= max_number:
                counts[n] += 1
    return counts


def exposure_adjusted_frequency(history, history_dates, game, max_number, draw_size, alpha=2.0):
    """Return observed counts, expected counts and smoothed observed/expected index.

    Each number is only exposed on draws where the official game rules allowed it.
    This prevents 50, 51 and 52 from looking artificially cold because they did
    not exist in earlier LOTTO MAX eras.
    """
    observed = np.zeros(max_number + 1, dtype=float)
    expected = np.zeros(max_number + 1, dtype=float)
    for numbers, draw_date in zip(history, history_dates):
        pool = min(max_number, game_pool_size(game, draw_date))
        if pool < 1:
            continue
        for n in numbers:
            if 1 <= int(n) <= pool:
                observed[int(n)] += 1
        expected[1:pool + 1] += draw_size / pool
    # A small neutral prior stabilizes scores for numbers with limited exposure.
    index = np.ones(max_number + 1, dtype=float)
    index[1:] = (observed[1:] + alpha) / (expected[1:] + alpha)
    if index[1:].mean() > 0:
        index[1:] /= index[1:].mean()
    return observed, expected, index


def normalized_entropy(counts):
    values = np.asarray(counts, dtype=float)
    values = values[1:] if len(values) > 1 else values
    values = np.maximum(values, 0)
    total = values.sum()
    if total <= 0 or len(values) <= 1:
        return 0.0
    p = values / total
    p = p[p > 0]
    entropy = -(p * np.log2(p)).sum()
    return float(100 * entropy / np.log2(len(values)))


def pair_counts(draws):
    result = Counter()
    for draw in draws:
        nums = sorted(draw)
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                result[(nums[i], nums[j])] += 1
    return result


def triple_counts(draws):
    result = Counter()
    for draw in draws:
        for triple in __import__("itertools").combinations(sorted(draw), 3):
            result[triple] += 1
    return result


def pick_weighted(pool, weights, size, rng):
    pool = np.asarray(pool, dtype=int)
    w = np.asarray(weights, dtype=float)
    w = np.maximum(w, 1e-9)
    probs = w / w.sum()
    return sorted(rng.choice(pool, size=size, replace=False, p=probs).tolist())


def make_ticket(history, history_dates, game, max_number, draw_size, strategy, rng):
    """Generate one selection using exposure-adjusted historical descriptions."""
    pool = np.arange(1, max_number + 1)
    if not history:
        return sorted(rng.choice(pool, size=draw_size, replace=False).tolist())

    all_obs, all_exp, all_index = exposure_adjusted_frequency(
        history, history_dates, game, max_number, draw_size
    )
    recent_obs, recent_exp, recent_index = exposure_adjusted_frequency(
        history[-100:], history_dates[-100:], game, max_number, draw_size
    )
    medium_obs, medium_exp, medium_index = exposure_adjusted_frequency(
        history[-250:], history_dates[-250:], game, max_number, draw_size
    )

    if strategy == "Statistical Edge":
        weights = 0.55 * all_index[1:] + 0.45 * recent_index[1:]
        return pick_weighted(pool, weights, draw_size, rng)

    if strategy == "Contrarian Maximizer":
        # Human-choice popularity proxy only; not measured player-pick data.
        weights = np.ones(max_number, dtype=float)
        weights[pool <= 31] *= 0.68
        weights[(pool % 5) == 0] *= 0.90
        chosen = []
        remaining = pool.copy()
        for _ in range(draw_size):
            w = weights[remaining - 1].copy()
            if chosen:
                for i, candidate in enumerate(remaining):
                    if any(abs(int(candidate) - old) == 1 for old in chosen):
                        w[i] *= 0.72
            next_num = int(rng.choice(remaining, p=w / w.sum()))
            chosen.append(next_num)
            remaining = remaining[remaining != next_num]
        return sorted(chosen)

    # Explainable frequency blend. Pair co-occurrence is intentionally not used
    # as a probability boost because raw pair counts are exposure-confounded.
    weights = (
        0.25 * all_index[1:]
        + 0.35 * medium_index[1:]
        + 0.40 * recent_index[1:]
    )
    return pick_weighted(pool, weights, draw_size, rng)


def generate_ticket(history, history_dates, game, max_number, draw_size, strategy, line_count, seed):
    rng = np.random.default_rng(seed)
    lines = []
    seen = set()
    attempts = 0
    while len(lines) < line_count and attempts < line_count * 100:
        line = tuple(make_ticket(history, history_dates, game, max_number, draw_size, strategy, rng))
        if line not in seen:
            seen.add(line)
            lines.append(list(line))
        attempts += 1
    while len(lines) < line_count:
        line = tuple(sorted(rng.choice(np.arange(1, max_number + 1), draw_size, replace=False).tolist()))
        if line not in seen:
            seen.add(line)
            lines.append(list(line))
    return lines


def popularity_proxy_score(line):
    """Higher score means more common-looking patterns under a simple heuristic."""
    birthday_count = sum(n <= 31 for n in line)
    consecutive_pairs = sum(1 for a, b in zip(line, line[1:]) if b == a + 1)
    round_numbers = sum(n % 5 == 0 for n in line)
    return birthday_count + 1.5 * consecutive_pairs + 0.35 * round_numbers


def render_ticket_card(title, lines, color_class, max_number, entropy=None):
    html = [f'<div class="ticket-card {color_class}">']
    html.append(
        f'<div class="ticket-heading"><span>STRATEGY: {title}</span>'
        f'<span>{datetime.now().strftime("%H:%M")}</span></div>'
    )
    for idx, line in enumerate(lines, start=1):
        html.append(f'<div class="line-label">LINE {idx}</div><div class="ball-row">')
        html.extend([f'<span class="ball">{int(n):02d}</span>' for n in line])
        html.append("</div>")
    sums = [sum(line) for line in lines]
    spreads = [max(line) - min(line) for line in lines]
    proxy = np.mean([popularity_proxy_score(line) for line in lines])
    html.append(
        '<div class="metric-grid">'
        f'<div class="metric"><small>Average sum</small><b>{np.mean(sums):.0f}</b></div>'
        f'<div class="metric"><small>Average range</small><b>{np.mean(spreads):.1f}</b></div>'
        f'<div class="metric"><small>Pattern proxy</small><b>{proxy:.1f}</b></div>'
        '</div></div>'
    )
    st.markdown("".join(html), unsafe_allow_html=True)


# ---------------------------- WALK-FORWARD BACKTEST ----------------------------
def _strategy_weights(history, history_dates, game, max_number, draw_size, strategy):
    """Precompute one date's strategy weights once for reuse across replicates."""
    pool = np.arange(1, max_number + 1)
    if strategy == "Contrarian Maximizer":
        weights = np.ones(max_number, dtype=float)
        weights[pool <= 31] *= 0.68
        weights[(pool % 5) == 0] *= 0.90
        return weights
    _, _, all_index = exposure_adjusted_frequency(
        history, history_dates, game, max_number, draw_size
    )
    _, _, recent_index = exposure_adjusted_frequency(
        history[-100:], history_dates[-100:], game, max_number, draw_size
    )
    if strategy == "Statistical Edge":
        return 0.55 * all_index[1:] + 0.45 * recent_index[1:]
    _, _, medium_index = exposure_adjusted_frequency(
        history[-250:], history_dates[-250:], game, max_number, draw_size
    )
    return 0.25 * all_index[1:] + 0.35 * medium_index[1:] + 0.40 * recent_index[1:]


def _weighted_line(max_number, draw_size, weights, strategy, rng):
    pool = np.arange(1, max_number + 1)
    if strategy != "Contrarian Maximizer":
        return tuple(sorted(pick_weighted(pool, weights, draw_size, rng)))
    chosen = []
    remaining = pool.copy()
    for _ in range(draw_size):
        w = weights[remaining - 1].copy()
        if chosen:
            for j, candidate in enumerate(remaining):
                if any(abs(int(candidate) - old) == 1 for old in chosen):
                    w[j] *= 0.72
        chosen.append(int(rng.choice(remaining, p=w / w.sum())))
        remaining = remaining[remaining != chosen[-1]]
    return tuple(sorted(chosen))


def _ticket_set(max_number, draw_size, line_count, weights, strategy, rng):
    lines, seen = [], set()
    for _ in range(line_count * 100):
        if len(lines) == line_count:
            break
        if strategy == "Random Baseline":
            line = tuple(sorted(rng.choice(np.arange(1, max_number + 1), draw_size, replace=False).tolist()))
        else:
            line = _weighted_line(max_number, draw_size, weights, strategy, rng)
        if line not in seen:
            seen.add(line)
            lines.append(line)
    while len(lines) < line_count:
        line = tuple(sorted(rng.choice(np.arange(1, max_number + 1), draw_size, replace=False).tolist()))
        if line not in seen:
            seen.add(line)
            lines.append(line)
    return lines


def walk_forward_backtest(game_df, strategy_names, test_draws=180, min_history=100, random_replicates=200, end_idx=None):
    """Fair walk-forward Monte Carlo: every strategy and random use identical dates/line counts.

    If end_idx is supplied, only rows before that endpoint are visible to the test.
    This allows separate, non-overlapping historical evaluation windows.
    """
    ordered = game_df.sort_values("Date").reset_index(drop=True)
    if end_idx is not None:
        ordered = ordered.iloc[:int(end_idx)].copy().reset_index(drop=True)
    if len(ordered) <= min_history:
        return pd.DataFrame(), min_history, pd.DataFrame()
    start = max(min_history, len(ordered) - test_draws)
    strategies = list(strategy_names) + ["Random Baseline"]
    records = []
    # Store one accumulated scorecard per independent replicate and strategy.
    accum = {(name, rep): {"Draws with 3+": 0, "3+ line matches": 0,
                            "4+ draws": 0, "5+ draws": 0,
                            "Best matches total": 0, "Total matches": 0,
                            "Ticket lines": 0}
             for name in strategies for rep in range(random_replicates)}
    for idx in range(start, len(ordered)):
        history_df = ordered.iloc[:idx]
        actual = set(ordered.iloc[idx]["Numbers"])
        draw_date = ordered.iloc[idx]["Date"]
        game = ordered.iloc[idx]["Game"]
        max_number = game_pool_size(game, draw_date)
        draw_size = 6 if game == "Lotto 6/49" else 7
        line_count = 3 if draw_size == 6 else 4
        history = history_df["Numbers"].tolist()
        history_dates = history_df["Date"].tolist()
        prepared = {name: _strategy_weights(history, history_dates, game, max_number, draw_size, name)
                    for name in strategy_names}
        prepared["Random Baseline"] = None
        for name in strategies:
            for rep in range(random_replicates):
                # Same replicate index and date across all strategies; independent reproducible streams.
                seed = 7300001 + rep * 10000019 + idx * 1009 + strategies.index(name) * 9176
                rng = np.random.default_rng(seed)
                lines = _ticket_set(max_number, draw_size, line_count, prepared[name], name, rng)
                hits = [len(set(line) & actual) for line in lines]
                score = accum[(name, rep)]
                score["Draws with 3+"] += int(any(h >= 3 for h in hits))
                score["3+ line matches"] += int(sum(h >= 3 for h in hits))
                score["4+ draws"] += int(any(h >= 4 for h in hits))
                score["5+ draws"] += int(any(h >= 5 for h in hits))
                score["Best matches total"] += max(hits)
                score["Total matches"] += sum(hits)
                score["Ticket lines"] += line_count
    test_count = len(ordered) - start
    for (name, rep), score in accum.items():
        records.append({"Strategy": name, "Replicate": rep, "Test draws": test_count,
                        "Coverage 3+ (%)": 100 * score["Draws with 3+"] / test_count,
                        "Coverage 4+ (%)": 100 * score["4+ draws"] / test_count,
                        "Coverage 5+ (%)": 100 * score["5+ draws"] / test_count,
                        "3+ line rate (%)": 100 * score["3+ line matches"] / score["Ticket lines"],
                        "Average best matches": score["Best matches total"] / test_count,
                        "Total number matches": score["Total matches"]})
    results = pd.DataFrame(records)
    return results[results["Strategy"].isin(strategy_names)].copy(), start, results[results["Strategy"].eq("Random Baseline")].copy()


# ---------------------------- APP START ----------------------------
with st.sidebar:
    st.markdown("## LottoStat")
    raw_data, source_label = get_source_data()
    with st.expander("Advanced data settings", expanded=False):
        analysis_window = st.selectbox("Analysis window", ["All available history", "Last 5 years", "Last 1 year"], index=0)
        st.caption("The analysis window affects historical analysis and generation inputs.")
    st.divider()
    st.caption("Three transparent selection models")
    st.caption(f"Data: {source_label}")

if raw_data is None:
    st.error("Could not find olg_data.csv. Place it beside app.py or upload it in the sidebar.")
    st.stop()

try:
    data, data_issues = read_and_prepare(raw_data)
except Exception as exc:
    st.error(f"Could not read the historical database: {exc}")
    st.stop()

st.markdown('<div class="header-title">LottoStat Enterprise</div>', unsafe_allow_html=True)
st.markdown('<div class="header-subtitle">Simple ticket generation · Clear analysis · Your saved picks</div>', unsafe_allow_html=True)

# Main-page game selector: easier to find than the former sidebar-only control.
game_col, info_col = st.columns([1, 3])
with game_col:
    game_choice = st.selectbox("🎯 Select Lottery Game", ["Lotto Max", "Lotto 6/49"], index=0, key="main_game_choice")
with info_col:
    st.caption("Choose Lotto Max or Lotto 6/49 here. All three tabs and their analysis update to the selected game.")

game_df = data[data["Game"] == game_choice].copy()
if analysis_window != "All available history" and not game_df.empty:
    years = 5 if analysis_window == "Last 5 years" else 1
    cutoff = game_df["Date"].max() - pd.DateOffset(years=years)
    game_df = game_df[game_df["Date"] >= cutoff].copy()

if game_df.empty:
    st.error(f"No valid historical rows were found for {game_choice}.")
    st.stop()

latest_date = game_df["Date"].max()
current_max = game_pool_size(game_choice, latest_date)
draw_size = GAME_CONFIG[game_choice]["draw_size"]
line_count = GAME_CONFIG[game_choice]["lines"]
history = game_df["Numbers"].tolist()
history_dates = game_df["Date"].tolist()
observed_freq, expected_freq, frequency_index = exposure_adjusted_frequency(
    history, history_dates, game_choice, current_max, draw_size
)
entropy_score = normalized_entropy(frequency_index)

st.markdown(
    f'<div class="status-bar"><span><i class="status-dot"></i> ENGINE READY</span>'
    f'<span>{game_choice} · {current_max} number range · {draw_size} numbers per line</span>'
    f'<span>{len(game_df):,} draws · Latest: {latest_date:%d %b %Y}</span></div>',
    unsafe_allow_html=True,
)
if data_issues:
    st.warning(f"{len(data_issues)} invalid rows were excluded during validation. Check your CSV before relying on the analysis.")

if game_choice == "Lotto Max":
    st.markdown(
        '<div class="warning-note"><b>Rule-change handling:</b> Lotto Max draws from September 25, 2009 through May 10, 2019 use 7/49; '
        'May 14, 2019 through April 10, 2026 use 7/50; April 14, 2026 onward uses 7/52. Frequencies are exposure-adjusted '
        'so numbers are compared only across draws in which they were eligible.</div>', unsafe_allow_html=True
    )

if game_choice == "Lotto 6/49":
    st.markdown(
        '<div class="warning-note"><b>Data limitation:</b> Your CSV contains six numbers per 6/49 draw. '
        'It does not include the bonus number, so this application analyzes main-number matches only '
        'and cannot calculate bonus-match prize tiers.</div>', unsafe_allow_html=True
    )

tab1, tab2, tab3 = st.tabs(["🎟️ Ticket Optimizer", "🔬 Backtest Simulator", "📈 Deep Analytics"])

# ---------------------------- TAB 1 ----------------------------
with tab1:
    st.markdown("### Create your tickets")
    st.caption(f"Currently generating for **{game_choice}** — {draw_size} numbers per line, from 1 to {current_max}.")
    st.markdown(
        '<div class="note"><b>One click, three approaches.</b> LottoStat creates three different number sets using transparent selection rules. '
        'These are structured selections, not predictions; every valid combination has the same draw probability.</div>',
        unsafe_allow_html=True
    )

    with st.expander("Ticket settings", expanded=False):
        requested_lines = st.number_input(
            "Number of lines in each strategy", min_value=1, max_value=12,
            value=1, step=1, help="Each strategy generates this many separate lines."
        )
        st.caption("Default: 1 line per strategy. Increase this only when you want more selections.")

    generate_label = "GENERATE LOTTO MAX" if game_choice == "Lotto Max" else "GENERATE LOTTO 6/49"
    if st.button(generate_label, type="primary", use_container_width=True):
        seed = int(np.random.SeedSequence().generate_state(1)[0])
        strategies = [
            ("Statistical Edge", "stat"),
            ("Contrarian Maximizer", "contra"),
            ("AI Statistical Blend", "ai"),
        ]
        generated = {}
        for i, (name, key) in enumerate(strategies):
            generated[key] = generate_ticket(
                history, history_dates, game_choice, current_max, draw_size,
                name, int(requested_lines), seed + i * 7919
            )

        # Reveal each strategy from left to right, then move to the next
        # strategy. Each new ball rolls in from the left; saved values stay exact.
        reveal_area = st.empty()
        reveal_specs = [
            ("stat", "STATISTICAL EDGE", "#2563eb"),
            ("contra", "CONTRARIAN MAXIMIZER", "#b21cc4"),
            ("ai", "STATISTICAL BLEND", "#0d9488"),
        ]
        for key, title, color in reveal_specs:
            revealed_lines = [[] for _ in generated[key]]
            total_balls = sum(len(line) for line in generated[key])
            ball_number = 0
            for line_idx, line in enumerate(generated[key]):
                for number in line:
                    revealed_lines[line_idx].append(number)
                    ball_number += 1
                    with reveal_area.container():
                        st.markdown(f"#### {title}")
                        st.caption(f"Revealing selection {ball_number} of {total_balls}")
                        for idx, shown in enumerate(revealed_lines, start=1):
                            st.markdown(f"**LINE {idx}**")
                            balls = " ".join(
                                f'<span class="rolling-ball" style="display:inline-flex;align-items:center;'
                                f'justify-content:center;width:42px;height:42px;margin:4px;border-radius:50%;'
                                f'background:{color};color:white;font-weight:800;box-shadow:0 4px 12px {color}55;">'
                                f'{n:02d}</span>' for n in shown
                            )
                            st.markdown(balls or '<span style="color:#cbd5e1">Waiting for numbers…</span>', unsafe_allow_html=True)
                    time.sleep(0.16)
            time.sleep(0.35)
        reveal_area.empty()

        st.session_state["generated_tickets"] = generated
        st.session_state["generated_game"] = game_choice
        st.session_state["generated_max"] = current_max
        st.session_state["generated_entropy"] = entropy_score
        st.session_state["generated_seed"] = seed
        st.session_state["generated_line_count"] = int(requested_lines)

    if "generated_tickets" in st.session_state and st.session_state.get("generated_game") == game_choice:
        generated = st.session_state["generated_tickets"]
        st.markdown("#### Your generated selections")
        card_cols = st.columns(3, gap="medium")
        card_specs = [
            ("stat", "STATISTICAL EDGE", "blue", "Uses long-term and recent historical frequency patterns."),
            ("contra", "CONTRARIAN", "purple", "Avoids some common-looking human number choices."),
            ("ai", "STATISTICAL BLEND", "teal", "Blends long-, medium- and short-term frequency patterns."),
        ]
        for col, (key, title, color, description) in zip(card_cols, card_specs):
            with col:
                st.caption(description)
                render_ticket_card(title, generated[key], color, current_max, entropy_score)
        st.caption(
            f"{st.session_state.get('generated_line_count', line_count)} lines per strategy · "
            f"Generated {datetime.now().strftime('%d %b %Y at %H:%M')} · Reference seed: {st.session_state.get('generated_seed')}"
        )
        st.markdown("#### Save these tickets")
        save_col, date_col = st.columns([1, 2], vertical_alignment="bottom")
        with date_col:
            intended_draw_date = st.date_input(
                "Draw date", value=date.today(), key="ticket_draw_date"
            )
        with save_col:
            if st.button("SAVE TICKET SET", type="primary", use_container_width=True):
                saved_id = save_ticket_batch(
                    game_choice, intended_draw_date, st.session_state.get("generated_seed", 0), generated
                )
                st.session_state["last_saved_ticket_batch"] = saved_id
                st.success(f"Saved. Batch ID: {saved_id}")
        if st.session_state.get("last_saved_ticket_batch"):
            st.caption(f"Last saved batch: {st.session_state['last_saved_ticket_batch']}")
        with st.expander("How the three approaches work"):
            st.write("**Statistical Edge:** blends all-time and recent exposure-adjusted frequency indices.")
            st.write("**Contrarian:** reduces selection weight for birthday-range and some common-looking patterns. Actual player-choice data is not available, so this is only a heuristic.")
            st.write("**Statistical Blend:** combines all-time, medium-term and recent frequency indices. It is an explainable statistical formula, not a trained predictive AI model.")
            st.warning("Historical patterns do not make a number more likely in the next independent draw. These approaches do not improve the mathematical odds.")
    else:
        st.info("Choose your lottery game above, then select **Generate My Tickets** to create your three sets.")

    st.divider()
    st.markdown("### Saved tickets & draw checker")
    st.caption("Your saved batches stay on this computer when you close and reopen LottoStat.")
    saved_batches = load_ticket_batches(game_choice)
    if saved_batches:
        summary_rows = []
        for batch in saved_batches:
            summary_rows.append({
                "Batch ID": batch["batch_id"], "Draw date": batch["draw_date"],
                "Saved": batch["generated_at"], "Status": "Checked" if batch["winning_numbers_json"] else "Waiting for draw"
            })
        st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)
        selected_batch_id = st.selectbox(
            "Select a saved batch", [b["batch_id"] for b in saved_batches],
            format_func=lambda bid: next(
                f"{bid} · Draw {next(x['draw_date'] for x in saved_batches if x['batch_id']==bid)}"
                for _ in [0]
            ), key="saved_batch_select"
        )
        selected_batch = next(b for b in saved_batches if b["batch_id"] == selected_batch_id)
        saved_tickets = json.loads(selected_batch["tickets_json"])
        if selected_batch["winning_numbers_json"]:
            winning = json.loads(selected_batch["winning_numbers_json"])
            st.info("Winning main numbers already recorded: " + ", ".join(f"{n:02d}" for n in winning))
        else:
            st.write("Enter the official main winning numbers after the draw.")
            winning_text = st.text_input(
                f"Winning numbers ({draw_size} numbers, 1–{game_pool_size(game_choice, selected_batch['draw_date'])})",
                key=f"winning_numbers_{selected_batch_id}", placeholder="Separate numbers with commas"
            )
            if st.button("CHECK SAVED TICKETS", key=f"check_{selected_batch_id}", type="primary"):
                try:
                    winning = [int(part.strip()) for part in winning_text.split(",") if part.strip()]
                    pool = game_pool_size(game_choice, selected_batch["draw_date"])
                    if len(winning) != draw_size or len(set(winning)) != draw_size or any(n < 1 or n > pool for n in winning):
                        st.error(f"Enter exactly {draw_size} different main numbers from 1 to {pool}.")
                    else:
                        update_ticket_batch_result(selected_batch_id, winning)
                        st.session_state[f"checked_{selected_batch_id}"] = winning
                        st.rerun()
                except ValueError:
                    st.error("Enter numbers separated by commas, using digits only.")
        if selected_batch["winning_numbers_json"] or st.session_state.get(f"checked_{selected_batch_id}"):
            winning = json.loads(selected_batch["winning_numbers_json"]) if selected_batch["winning_numbers_json"] else st.session_state[f"checked_{selected_batch_id}"]
            results = []
            strategy_display_names = {
                "stat": "Statistical Edge", "statistical edge": "Statistical Edge",
                "contra": "Contrarian Maximizer", "contrarian maximizer": "Contrarian Maximizer",
                "ai": "AI Statistical Blend", "ai statistical blend": "AI Statistical Blend",
            }
            for strategy_key, lines in saved_tickets.items():
                strategy_name = strategy_display_names.get(str(strategy_key).strip().lower(), str(strategy_key))
                for line_no, line in enumerate(lines, start=1):
                    matches = sorted(set(line) & set(winning))
                    results.append({
                        "Strategy": strategy_name, "Line": line_no,
                        "Your numbers": " – ".join(f"{n:02d}" for n in line),
                        "Matches": len(matches),
                        "Matched numbers": ", ".join(f"{n:02d}" for n in matches) or "—"
                    })
            results_df = pd.DataFrame(results)
            if not results_df.empty:
                st.markdown("#### Match summary")
                summary = (results_df.groupby("Strategy", sort=False)
                    .agg(**{
                        "Ticket lines": ("Line", "count"),
                        "Total matched numbers": ("Matches", "sum"),
                        "Best line matches": ("Matches", "max"),
                        "Lines with 3+ matches": ("Matches", lambda values: int((values >= 3).sum())),
                        "Lines with 4+ matches": ("Matches", lambda values: int((values >= 4).sum())),
                        "Lines with 5+ matches": ("Matches", lambda values: int((values >= 5).sum())),
                    }).reset_index())
                st.dataframe(summary, use_container_width=True, hide_index=True)
                with st.expander("View line-by-line results"):
                    st.dataframe(results_df, use_container_width=True, hide_index=True)
            st.caption("This checker compares main numbers only. Official prize eligibility depends on the complete game rules and any bonus or add-on results.")
    else:
        st.info("No saved batches for this game yet. Generate tickets and save a set above.")

# ---------------------------- TAB 2 ----------------------------
with tab2:
    st.markdown("### Walk-forward historical simulation")
    st.write(
        "Each test draw is evaluated using only earlier draws. All three strategies and the random "
        "baseline receive the same test dates, number of ticket lines, and number of independent simulations."
    )
    test_count = st.slider("Number of most recent draws to test", min_value=50, max_value=300, value=180, step=10)
    min_train = st.slider("Minimum prior draws before testing starts", min_value=50, max_value=500, value=150, step=25)
    replicate_count = st.select_slider("Independent simulations per strategy", options=[50, 100, 200, 300, 500], value=200)
    st.markdown("---")
    st.markdown("## 🧪 INDEPENDENT HOLDOUT TEST")
    st.caption(
        "This test reserves the most recent historical draws as a separate evaluation window. "
        "The strategy formulas remain fixed; the holdout results must not be used to tune them. "
        "For each draw, weights are calculated only from earlier draws."
    )
    holdout_draws = st.slider("Holdout window (most recent draws)", min_value=50, max_value=200, value=100, step=10, key="holdout_draws")
    holdout_replicates = st.select_slider(
        "Holdout simulations per model", options=[100, 200, 300, 500], value=300, key="holdout_replicates"
    )
    if st.button("RUN INDEPENDENT HOLDOUT TEST", type="secondary", use_container_width=True):
        holdout_strategies = ["Statistical Edge", "Contrarian Maximizer", "AI Statistical Blend"]
        with st.spinner(f"Testing the reserved {holdout_draws} most recent draws..."):
            holdout_bt, holdout_start, holdout_random = walk_forward_backtest(
                game_df, holdout_strategies, holdout_draws, min_train,
                random_replicates=holdout_replicates
            )
        st.session_state["holdout_result"] = holdout_bt
        st.session_state["holdout_random"] = holdout_random
        st.session_state["holdout_game"] = game_choice
        st.session_state["holdout_replicates_done"] = holdout_replicates
        st.session_state["holdout_draw_count"] = holdout_draws

    holdout_bt = st.session_state.get("holdout_result")
    if holdout_bt is not None and st.session_state.get("holdout_game") == game_choice and not holdout_bt.empty:
        holdout_random_df = st.session_state.get("holdout_random", pd.DataFrame())
        holdout_all = pd.concat([holdout_bt, holdout_random_df], ignore_index=True)
        holdout_summary = holdout_all.groupby("Strategy", sort=False).agg(
            Simulations=("Replicate", "count"),
            Test_draws=("Test draws", "first"),
            Coverage_3_plus=("Coverage 3+ (%)", "mean"),
            Coverage_4_plus=("Coverage 4+ (%)", "mean"),
            Coverage_5_plus=("Coverage 5+ (%)", "mean"),
            Average_best_matches=("Average best matches", "mean")
        ).reset_index()
        holdout_summary = holdout_summary.rename(columns={
            "Test_draws": "Test Draws",
            "Coverage_3_plus": "Coverage 3+ (%)",
            "Coverage_4_plus": "Coverage 4+ (%)",
            "Coverage_5_plus": "Coverage 5+ (%)",
            "Average_best_matches": "Average Best Matches"
        })
        holdout_summary.insert(0, "Rank (3+)", holdout_summary["Coverage 3+ (%)"].rank(
            method="min", ascending=False
        ).astype(int))
        holdout_summary = holdout_summary.sort_values(
            ["Coverage 3+ (%)", "Average Best Matches"], ascending=False
        )
        st.markdown(
            f"**Holdout results — {st.session_state.get('holdout_draw_count')} draws, "
            f"{st.session_state.get('holdout_replicates_done')} simulations per model**"
        )
        st.dataframe(holdout_summary.round(3), use_container_width=True, hide_index=True)
        if st.session_state.get("backtest_result") is not None:
            st.warning(
                "The standard walk-forward backtest and this holdout both use recent historical draws. "
                "Their test windows may overlap, so do not treat them as two independent confirmations."
            )
        holdout_diffs = []
        for strategy in ["Statistical Edge", "Contrarian Maximizer", "AI Statistical Blend"]:
            values = holdout_bt.loc[holdout_bt["Strategy"] == strategy, "Coverage 3+ (%)"].to_numpy(float)
            random_values = holdout_random_df["Coverage 3+ (%)"].to_numpy(float)
            if len(values) and len(random_values):
                holdout_diffs.append({
                    "Strategy": strategy,
                    "3+ coverage difference vs random (pp)": values.mean() - random_values.mean(),
                    "95% lower": np.quantile(
                        [np.mean(np.random.default_rng(91000 + i).choice(values, len(values), replace=True))
                         - np.mean(np.random.default_rng(92000 + i).choice(random_values, len(random_values), replace=True))
                         for i in range(2000)], 0.025
                    ),
                    "95% upper": np.quantile(
                        [np.mean(np.random.default_rng(93000 + i).choice(values, len(values), replace=True))
                         - np.mean(np.random.default_rng(94000 + i).choice(random_values, len(random_values), replace=True))
                         for i in range(2000)], 0.975
                    ),
                })
        st.markdown("#### Holdout comparison against random")
        st.dataframe(pd.DataFrame(holdout_diffs).round(3), use_container_width=True, hide_index=True)
        st.warning(
            "Treat this as a reserved historical evaluation only if you have not used these draws to tune "
            "the strategies. Do not adjust strategy rules after viewing these results and then reuse this "
            "same holdout as independent evidence."
        )

    st.markdown("---")
    st.markdown("### Three-period historical stability test")
    st.caption(
        "This test evaluates three consecutive, non-overlapping 60-draw periods that end BEFORE "
        "the reserved holdout window above. It also sits outside the most-recent walk-forward window "
        "when that window is 180 draws. Each period uses only draws available before each test draw."
    )
    stability_period_draws = 60
    if st.button("RUN THREE-PERIOD STABILITY TEST", use_container_width=True):
        stability_strategies = ["Statistical Edge", "Contrarian Maximizer", "AI Statistical Blend"]
        ordered_for_stability = game_df.sort_values("Date").reset_index(drop=True)
        reserved_holdout = int(holdout_draws)
        reserved_recent_window = max(int(holdout_draws), int(test_count))
        validation_end = len(ordered_for_stability) - reserved_recent_window
        endpoints = [validation_end - 2 * stability_period_draws,
                     validation_end - stability_period_draws,
                     validation_end]
        if endpoints[0] < min_train + stability_period_draws:
            st.error(
                "There are not enough historical draws to create three separate 60-draw periods "
                "before the selected holdout. Reduce the holdout size or minimum prior draws, "
                "or select a longer analysis window."
            )
        else:
            stability_parts = []
            with st.spinner(
                f"Testing three separate periods with {replicate_count} simulations per model in each period..."
            ):
                for period_no, endpoint in enumerate(endpoints, start=1):
                    period_result, _, period_random = walk_forward_backtest(
                        ordered_for_stability, stability_strategies,
                        test_draws=stability_period_draws, min_history=min_train,
                        random_replicates=replicate_count, end_idx=endpoint
                    )
                    period_result = period_result.copy()
                    period_random = period_random.copy()
                    period_result["Period"] = f"Period {period_no}"
                    period_random["Period"] = f"Period {period_no}"
                    stability_parts.extend([period_result, period_random])
            stability_frame = pd.concat(stability_parts, ignore_index=True)
            st.session_state["nonoverlap_stability_result"] = stability_frame
            st.session_state["nonoverlap_stability_game"] = game_choice
            st.session_state["nonoverlap_stability_holdout"] = reserved_holdout
            st.session_state["nonoverlap_stability_gap"] = reserved_recent_window
            st.session_state["nonoverlap_stability_replicates"] = replicate_count

    stability_frame = st.session_state.get("nonoverlap_stability_result")
    if stability_frame is not None and st.session_state.get("nonoverlap_stability_game") == game_choice:
        stability_summary = (stability_frame.groupby(["Period", "Strategy"], sort=False)
            .agg(Simulations=("Replicate", "count"),
                 **{"Test draws": ("Test draws", "first"),
                    "Coverage 3+ (%)": ("Coverage 3+ (%)", "mean"),
                    "Coverage 4+ (%)": ("Coverage 4+ (%)", "mean"),
                    "Coverage 5+ (%)": ("Coverage 5+ (%)", "mean"),
                    "Average best matches": ("Average best matches", "mean")})
            .reset_index())
        st.markdown(
            f"**Three-period results — 60 draws per period, "
            f"{st.session_state.get('nonoverlap_stability_replicates')} simulations per model**"
        )
        st.dataframe(stability_summary.round(3), use_container_width=True, hide_index=True)
        random_periods = stability_frame[stability_frame["Strategy"] == "Random Baseline"]
        strategy_periods = stability_frame[stability_frame["Strategy"] != "Random Baseline"]
        difference_rows = []
        rng_boot = np.random.default_rng(20261118)
        for (period, strategy), group in strategy_periods.groupby(["Period", "Strategy"], sort=False):
            strategy_values = group["Coverage 3+ (%)"].to_numpy(float)
            random_values = random_periods.loc[random_periods["Period"] == period, "Coverage 3+ (%)"].to_numpy(float)
            observed_diff = float(strategy_values.mean() - random_values.mean())
            # Independent bootstrap because the strategy and random streams are independently seeded.
            boot_diffs = np.empty(4000, dtype=float)
            for b in range(len(boot_diffs)):
                a = rng_boot.choice(strategy_values, size=len(strategy_values), replace=True)
                r = rng_boot.choice(random_values, size=len(random_values), replace=True)
                boot_diffs[b] = a.mean() - r.mean()
            lo, hi = np.quantile(boot_diffs, [0.025, 0.975])
            difference_rows.append({
                "Period": period,
                "Strategy": strategy,
                "3+ coverage difference vs random (pp)": observed_diff,
                "95% lower": float(lo),
                "95% upper": float(hi),
                "Evidence vs random": "Interval above zero" if lo > 0 else (
                    "Interval below zero" if hi < 0 else "Inconclusive (includes zero)"
                )
            })
        difference_frame = pd.DataFrame(difference_rows)
        st.markdown("#### Strategy difference versus random in each period")
        st.dataframe(difference_frame.round(3), use_container_width=True, hide_index=True)

        st.markdown("#### Consistency score and combined ranking")
        consistency_rows = []
        for strategy in ["Statistical Edge", "Contrarian Maximizer", "AI Statistical Blend"]:
            rows = difference_frame[difference_frame["Strategy"] == strategy]
            positive_periods = int((rows["3+ coverage difference vs random (pp)"] > 0).sum())
            convincing_periods = int((rows["95% lower"] > 0).sum())
            mean_difference = float(rows["3+ coverage difference vs random (pp)"].mean())
            consistency_rows.append({
                "Strategy": strategy,
                "Periods above random": f"{positive_periods}/3",
                "Periods with 95% interval above zero": f"{convincing_periods}/3",
                "Mean 3+ difference vs random (pp)": mean_difference,
                "Combined rank": 0
            })
        consistency_frame = pd.DataFrame(consistency_rows)
        consistency_frame["Combined rank"] = consistency_frame[
            "Mean 3+ difference vs random (pp)"
        ].rank(method="min", ascending=False).astype(int)
        consistency_frame = consistency_frame.sort_values(
            ["Combined rank", "Periods above random"], ascending=[True, False]
        )
        st.dataframe(consistency_frame.round(3), use_container_width=True, hide_index=True)
        st.caption(
            "Combined ranking uses the equally weighted mean of the three period-level 3+ coverage differences. "
            "The consistency score counts positive period averages; it is descriptive, not a probability of winning."
        )
        if (difference_frame["95% lower"] <= 0).all():
            st.warning(
                "No strategy has a 95% bootstrap interval entirely above zero in every period. "
                "Positive average differences alone are not sufficient evidence of an advantage over random."
            )
        st.info(
            "These three evaluation windows do not overlap each other, the reserved holdout window, "
            "or the selected most-recent walk-forward test window. The intervals quantify Monte Carlo "
            "simulation uncertainty for these historical periods; they do not capture all uncertainty about "
            "future lottery draws. Do not tune the strategies using these results and then reuse the same "
            "periods as independent evidence."
        )

    if st.button("RUN WALK-FORWARD BACKTEST", type="primary", use_container_width=True):
        strategy_names = ["Statistical Edge", "Contrarian Maximizer", "AI Statistical Blend"]
        with st.spinner(f"Running {replicate_count:,} simulations for each strategy and the random baseline..."):
            bt, start_idx, random_replicates_df = walk_forward_backtest(
                game_df, strategy_names, test_count, min_train, random_replicates=replicate_count
            )
        st.session_state["backtest_result"] = bt
        st.session_state["backtest_random"] = random_replicates_df
        st.session_state["backtest_game"] = game_choice
        st.session_state["backtest_start"] = start_idx
        st.session_state["backtest_replicates"] = replicate_count

    bt = st.session_state.get("backtest_result")
    if bt is not None and st.session_state.get("backtest_game") == game_choice and not bt.empty:
        random_df = st.session_state.get("backtest_random", pd.DataFrame())
        combined = pd.concat([bt, random_df], ignore_index=True)
        metric_cols = ["Coverage 3+ (%)", "Coverage 4+ (%)", "Coverage 5+ (%)",
                       "3+ line rate (%)", "Average best matches", "Total number matches"]
        summary_rows = []
        for strategy, group in combined.groupby("Strategy", sort=False):
            row = {"Strategy": strategy, "Simulations": len(group), "Test draws": int(group["Test draws"].iloc[0])}
            for metric in metric_cols:
                row[metric] = group[metric].mean()
            summary_rows.append(row)
        summary = pd.DataFrame(summary_rows)
        st.markdown(f"**Results: {st.session_state.get('backtest_replicates', 200)} independent simulations per model**")
        st.dataframe(summary.round(3), use_container_width=True, hide_index=True)

        st.markdown("#### Monte Carlo 95% intervals")
        ci_rows = []
        for strategy, group in combined.groupby("Strategy", sort=False):
            for metric in ["Coverage 3+ (%)", "Coverage 4+ (%)", "Coverage 5+ (%)", "Average best matches"]:
                ci_rows.append({"Strategy": strategy, "Metric": metric,
                                "Mean": group[metric].mean(),
                                "95% lower": group[metric].quantile(0.025),
                                "95% upper": group[metric].quantile(0.975)})
        st.dataframe(pd.DataFrame(ci_rows).round(3), use_container_width=True, hide_index=True)

        # Independent Monte Carlo comparison against the random baseline.
        # Strategy and random streams use distinct seeds, so replicate indices are NOT paired.
        st.markdown("#### Strategy vs. random — independent simulation comparison")
        st.caption(
            "Each model is compared over the same historical test dates and ticket counts, but its "
            "Monte Carlo streams are independent. Intervals are obtained by independently resampling "
            "each model's replicates; they describe simulation uncertainty, not future winning odds."
        )
        comparison_rows = []
        compare_metrics = ["Coverage 3+ (%)", "Coverage 4+ (%)", "Coverage 5+ (%)",
                           "3+ line rate (%)", "Average best matches"]
        rng_boot = np.random.default_rng(20261118)
        bootstrap_count = 5000
        for strategy in ["Statistical Edge", "Contrarian Maximizer", "AI Statistical Blend"]:
            strat_group = bt[bt["Strategy"] == strategy]
            for metric in compare_metrics:
                strat_values = strat_group[metric].to_numpy(dtype=float)
                random_values = random_df[metric].to_numpy(dtype=float)
                if len(strat_values) == 0 or len(random_values) == 0:
                    continue
                observed_difference = strat_values.mean() - random_values.mean()
                boot_differences = np.empty(bootstrap_count, dtype=float)
                for b in range(bootstrap_count):
                    strat_sample = rng_boot.choice(strat_values, size=len(strat_values), replace=True)
                    random_sample = rng_boot.choice(random_values, size=len(random_values), replace=True)
                    boot_differences[b] = strat_sample.mean() - random_sample.mean()
                # All-pairs probability of superiority; avoids arbitrary matching by replicate ID.
                superiority = 100.0 * np.mean(
                    strat_values[:, None] > random_values[None, :]
                )
                comparison_rows.append({
                    "Strategy": strategy,
                    "Metric": metric,
                    "Mean difference vs random": observed_difference,
                    "95% lower": np.quantile(boot_differences, 0.025),
                    "95% upper": np.quantile(boot_differences, 0.975),
                    "Chance strategy replicate exceeds random (%)": superiority,
                })
        comparison_df = pd.DataFrame(comparison_rows)
        st.dataframe(comparison_df.round(3), use_container_width=True, hide_index=True)
        st.caption(
            "Positive differences favor the named strategy; negative differences favor random selection. "
            "The last column is the proportion of all strategy/random replicate pairs where the strategy "
            "score is higher. It is not a win probability for a lottery ticket. These are exploratory "
            "comparisons across multiple metrics; small apparent advantages require validation on other "
            "historical windows."
        )

        chart_df = summary.copy()
        fig = px.bar(chart_df, x="Strategy", y="Coverage 3+ (%)", color="Strategy",
                     title="Mean percentage of test draws with at least one 3+ line",
                     color_discrete_map={"Statistical Edge": "#2563eb", "Contrarian Maximizer": "#c026d3",
                                         "AI Statistical Blend": "#0d9488", "Random Baseline": "#64748b"})
        fig.update_layout(showlegend=False, plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            f"Tested {int(combined['Test draws'].iloc[0])} historical draws with no future-data leakage. "
            "Intervals describe Monte Carlo variation between simulated ticket sets, not future winning odds. "
            "Small differences are not evidence that a strategy can predict independent lottery draws."
        )
    else:
        st.info("Run the walk-forward backtest to compare all three strategies with random selection.")

# ---------------------------- TAB 3 ----------------------------
with tab3:
    st.markdown("### Historical number analytics")
    st.caption(f"Analysis uses {len(game_df):,} {game_choice} draws in the selected date window.")
    freq_df = pd.DataFrame({
        "Number": np.arange(1, current_max + 1),
        "Observed appearances": observed_freq[1:].astype(int),
        "Expected appearances": expected_freq[1:],
        "Frequency index (1 = expected)": frequency_index[1:],
    })
    col1, col2, col3 = st.columns(3)
    col1.metric("Historical draws", f"{len(game_df):,}")
    col2.metric("Frequency-index entropy", f"{entropy_score:.1f}%")
    col3.metric("Number range", f"1–{current_max}")
    st.caption("Frequency-index entropy describes how evenly the smoothed observed/expected indices are distributed across the current number pool. It is a descriptive database statistic, not a measure of ticket quality or win probability.")

    left, right = st.columns(2)
    with left:
        st.markdown("#### Exposure-adjusted number frequency")
        st.caption("Index 1.00 = expected under a uniform draw, adjusted for the dates each number was eligible. Above 1 = more appearances than expected in this archive; not a prediction.")
        fig_freq = px.bar(freq_df, x="Number", y="Frequency index (1 = expected)", color="Frequency index (1 = expected)", color_continuous_scale="Blues")
        fig_freq.update_layout(coloraxis_showscale=False, plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig_freq, use_container_width=True)
    with right:
        st.markdown("#### Winning sum distribution")
        sums = pd.DataFrame({"Sum": [sum(x) for x in history]})
        fig_sum = px.histogram(sums, x="Sum", nbins=30, color_discrete_sequence=["#2563eb"])
        fig_sum.update_layout(plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig_sum, use_container_width=True)

    st.markdown("#### Most frequent numbers")
    hot = freq_df.sort_values("Frequency index (1 = expected)", ascending=False).head(10)
    cold = freq_df.sort_values("Frequency index (1 = expected)", ascending=True).head(10)
    c_hot, c_cold = st.columns(2)
    with c_hot:
        st.write("**Highest relative to expected**")
        st.dataframe(hot, hide_index=True, use_container_width=True)
    with c_cold:
        st.write("**Lowest relative to expected**")
        st.dataframe(cold, hide_index=True, use_container_width=True)

    st.markdown("#### Recent 100 draws vs full history")
    st.caption("This compares descriptive exposure-adjusted frequency indices. A value above 1.00 means more appearances than expected in that window; it does not mean the number is more likely in the next draw.")
    recent_n = min(100, len(history))
    recent_history = history[-recent_n:]
    recent_dates = history_dates[-recent_n:]
    recent_obs, recent_exp, recent_idx = exposure_adjusted_frequency(
        recent_history, recent_dates, game_choice, current_max, draw_size
    )
    comparison_df = pd.DataFrame({
        "Number": np.arange(1, current_max + 1),
        "Full-history index": frequency_index[1:],
        "Recent-window index": recent_idx[1:],
    })
    comparison_df["Recent minus full"] = comparison_df["Recent-window index"] - comparison_df["Full-history index"]
    comparison_df["Recent observed"] = recent_obs[1:].astype(int)
    recent_left, recent_right = st.columns(2)
    with recent_left:
        st.write("**Largest recent increases vs full history**")
        st.dataframe(comparison_df.sort_values("Recent minus full", ascending=False).head(10).round(3), hide_index=True, use_container_width=True)
    with recent_right:
        st.write("**Largest recent decreases vs full history**")
        st.dataframe(comparison_df.sort_values("Recent minus full", ascending=True).head(10).round(3), hide_index=True, use_container_width=True)
    st.caption(f"Recent window: {recent_n} draws ending {recent_dates[-1]:%Y-%m-%d}. These comparisons are descriptive only; short-term variation is expected in random draws.")

    st.markdown("#### Number pairs and triples")
    # Pair/triple raw counts are shown for the current rules era only, avoiding
    # cross-era exposure bias (especially for 50, 51 and 52).
    current_era_start = (LOTTO_MAX_52_DATE if game_choice == "Lotto Max" and current_max == 52
                         else LOTTO_MAX_50_DATE if game_choice == "Lotto Max" and current_max == 50
                         else LOTTO_MAX_LAUNCH_DATE if game_choice == "Lotto Max"
                         else pd.Timestamp("1982-01-01"))
    pair_triple_history = game_df.loc[game_df["Date"] >= current_era_start, "Numbers"].tolist()
    pc = pair_counts(pair_triple_history)
    tc = triple_counts(pair_triple_history)
    st.caption(f"Pair and triple counts use the current rules era only ({len(pair_triple_history):,} draws).")
    p1, p2 = st.columns(2)
    with p1:
        st.write("**Most frequent pairs**")
        pair_df = pd.DataFrame(
            [{"Pair": f"{a} – {b}", "Draws together": count} for (a, b), count in pc.most_common(15)]
        )
        st.dataframe(pair_df, hide_index=True, use_container_width=True)
    with p2:
        st.write("**Most frequent triples**")
        triple_df = pd.DataFrame(
            [{"Triple": f"{a} – {b} – {c}", "Draws together": count} for (a, b, c), count in tc.most_common(15)]
        )
        st.dataframe(triple_df, hide_index=True, use_container_width=True)

    st.markdown("#### Draw composition")
    composition = pd.DataFrame({
        "Odd numbers": [sum(n % 2 for n in row) for row in history],
        "Low numbers": [sum(n <= game_pool_size(game_choice, d) // 2 for n in row)
                        for row, d in zip(history, history_dates)],
    })
    c3, c4 = st.columns(2)
    with c3:
        odd_df = composition["Odd numbers"].value_counts().sort_index().rename_axis("Odd count").reset_index(name="Draws")
        fig_odd = px.bar(odd_df, x="Odd count", y="Draws", title="Odd / even composition")
        st.plotly_chart(fig_odd, use_container_width=True)
    with c4:
        low_df = composition["Low numbers"].value_counts().sort_index().rename_axis("Low count").reset_index(name="Draws")
        fig_low = px.bar(low_df, x="Low count", y="Draws", title="Low / high composition")
        st.plotly_chart(fig_low, use_container_width=True)

    with st.expander("Database audit, validation and interpretation"):
        st.write(f"Valid rows loaded: {len(data):,}. Rows excluded: {len(data_issues):,}.")
        game_audit = data.groupby("Game").agg(Draws=("Date", "count"), First_draw=("Date", "min"), Latest_draw=("Date", "max")).reset_index()
        st.dataframe(game_audit, hide_index=True, use_container_width=True)
        if game_choice == "Lotto Max":
            era_audit = pd.DataFrame([
                {"Rule era": "7/49", "Draws": int((game_df["Date"] < LOTTO_MAX_50_DATE).sum())},
                {"Rule era": "7/50", "Draws": int(((game_df["Date"] >= LOTTO_MAX_50_DATE) & (game_df["Date"] < LOTTO_MAX_52_DATE)).sum())},
                {"Rule era": "7/52", "Draws": int((game_df["Date"] >= LOTTO_MAX_52_DATE).sum())},
            ])
            st.dataframe(era_audit, hide_index=True, use_container_width=True)
        st.write("The CSV has no explicit Game field. Six-number rows are classified as Lotto 6/49 and seven-number rows as Lotto Max. This matches the structure of the supplied file.")
        st.write("Lotto Max rule eras: 1–49 from September 25, 2009 through May 10, 2019; 1–50 from May 14, 2019 through April 10, 2026; 1–52 from April 14, 2026 onward. Historical frequency scores use expected appearances based on each number's eligible draws.")
        st.write("The ticket cards show line-level sum, range and a descriptive pattern proxy. The shared historical entropy metric is shown only in Deep Analytics because it belongs to the database, not to an individual strategy.")
        st.write("The CSV contains main numbers only. Bonus numbers and historical prize amounts are not present.")

st.markdown(
    '<div class="footer">For entertainment only. Lottery draws are random and independent. '
    'Historical statistics do not predict future winning numbers. Please play responsibly.</div>',
    unsafe_allow_html=True,
)

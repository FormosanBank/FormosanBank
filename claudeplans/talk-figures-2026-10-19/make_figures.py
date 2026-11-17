"""Talk figures: size and provenance of FormosanBank (data = origin/main d7951d180).

Inputs (exported read-only with git archive into talk/src/):
  statistics/*_corpora_stats.csv    current counts per corpus x language x dialect
  statistics/language_history.csv   per-commit counts, today's counting rules
  corpus_classification.csv         source type / era per corpus (my classification, editable)
Outputs: talk/out/NN_name.{png,pdf} and talk/out/figure_data.json
"""
import csv, json, sys, collections, datetime as dt, pathlib, statistics
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / "src"
OUT = HERE / "out"; OUT.mkdir(exist_ok=True)
sys.path.insert(0, str(SRC / "docs/tools"))
import site_stats  # noqa: E402

# ---------- style (generic; the Keynote was never available to me) ----------
plt.rcParams.update({
    "font.family": "STIXGeneral", "mathtext.fontset": "stix",
    "font.size": 15, "axes.titlesize": 17, "axes.labelsize": 16,
    "xtick.labelsize": 13, "ytick.labelsize": 13, "legend.fontsize": 13,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.edgecolor": "#333333", "axes.linewidth": 1.0,
    "figure.facecolor": "white", "axes.facecolor": "white",
    "savefig.facecolor": "white", "pdf.fonttype": 42,
})
CRIMSON, INK, GREEN, BLUE, GOLD, GREY = "#B5123A", "#1F2A44", "#2E8B57", "#2F6DB5", "#C98A00", "#9AA0A6"
SERIES = {"words": ("Total words", INK), "zho": ("Translated into Mandarin", CRIMSON),
          "transcribed": ("In transcribed sentences (audio)", BLUE), "glossed": ("Glossed words", GREEN)}
TYPE_COLORS = {
    "Crowdsourced web": "#7E8EA6", "Dictionaries & word lists": "#2F6DB5",
    "Textbooks & learning materials": "#C98A00", "Grammars & linguistic fieldwork": "#2E8B57",
    "Religious texts": "#7B3F99", "Recorded speech": "#B5123A",
    "Government & other public writing": "#5F6B73",
}
TYPE_ORDER = list(TYPE_COLORS)
ERA_ORDER = ["Dutch period (1600s)", "1800-1949", "1950-1999", "2000-2015", "2016-2026", "mixed / unclear"]
GOALS = {}  # the maintainer's goals were NOT available; add them here to draw goal lines
def human(x, _=None):
    if x <= 0: return "0"
    for v, s in ((1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "k")):
        if x >= v:
            q = x / v
            return f"{q:.0f}{s}" if q >= 10 or q == int(q) else f"{q:.1f}{s}"
    return f"{x:.0f}"

def logx(ax, which="x"):
    getattr(ax, f"set_{which}scale")("log")
    axis = ax.xaxis if which == "x" else ax.yaxis
    axis.set_major_locator(LogLocator(base=10))
    axis.set_major_formatter(FuncFormatter(human))
    axis.set_minor_formatter(NullFormatter())

DATA = {}
def save(fig, name, data):
    fig.savefig(OUT / f"{name}.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUT / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)
    DATA[name] = data
    print("wrote", name)

# ---------- load ----------
rows = site_stats.load_stats(SRC / "statistics")
cls = {r["corpus"]: r for r in csv.DictReader(open(HERE / "corpus_classification.csv"))}
missing = sorted({r["corpus"] for r in rows} - set(cls))
assert not missing, f"unclassified corpora: {missing}"
history = list(csv.DictReader(open(SRC / "statistics/language_history.csv")))

def f(r, k): return float(r.get(k) or 0)
lang = collections.defaultdict(collections.Counter)
corpus = collections.defaultdict(collections.Counter)
for r in rows:
    L, C = r["language_name"], r["corpus"]
    for k, src in (("words", "word_count"), ("zho", "zho_transl_count"), ("eng", "eng_transl_count"),
                   ("glossed", "glossed_words"), ("transcribed", "transcribed_words")):
        lang[L][k] += f(r, src); corpus[C][k] += f(r, src)
    lang[L]["audio_h"] += f(r, "transcribed_audio_seconds") / 3600
    corpus[C]["audio_h"] += f(r, "transcribed_audio_seconds") / 3600
    corpus[C]["untranscribed_h"] += f(r, "untranscribed_audio_seconds") / 3600
    if C == "Wikipedias": lang[L]["wiki"] += f(r, "word_count")
    lang[L]["type:" + cls[C]["source_type"]] += f(r, "word_count")
LANGS = sorted(lang, key=lambda l: -lang[l]["words"])
TOTAL = sum(lang[l]["words"] for l in LANGS)
print("languages", len(LANGS), "total words", int(TOTAL))

# end-of-day history (UTC date of each commit; last commit of a day wins)
def day(s): return dt.datetime.fromisoformat(s).astimezone(dt.timezone.utc).date()
per_commit = collections.OrderedDict()
for x in history:
    per_commit.setdefault(x["commit"], {"date": day(x["date"]), "rows": []})["rows"].append(x)
def series(filter_fn=lambda x: True):
    out = collections.OrderedDict()
    for c in per_commit.values():
        tot = collections.Counter()
        for x in c["rows"]:
            if filter_fn(x):
                tot["words"] += int(x["words"]); tot["zho"] += int(x["zho_transl_count"])
                tot["glossed"] += int(x["glossed_words"]); tot["transcribed"] += int(x["transcribed_words"])
        out[c["date"]] = tot  # later commits on the same day overwrite
    return out

# ======================= F01 overall growth =======================
s = series()
dates = list(s); today = dt.date(2026, 10, 19)
fig, ax = plt.subplots(figsize=(10, 6))
for key in ("words", "zho", "transcribed", "glossed"):
    label, color = SERIES[key]
    ys = [s[d][key] for d in dates] + [s[dates[-1]][key]]
    xs = dates + [today]
    ax.step(xs, [y if y > 0 else float("nan") for y in ys], where="post", color=color, lw=3, label=label)
    ax.annotate(f"{human(ys[-1])}", (today, ys[-1]), xytext=(6, 0), textcoords="offset points",
                va="center", color=color, fontsize=14, fontweight="bold")
ax.axvline(dt.date(2024, 12, 7), color=GREY, ls=":", lw=1.2)
ax.text(dt.date(2024, 12, 12), 1.9e7, "first corpora published (Dec 2024)", fontsize=12, color="#555", va="bottom")
logx(ax, "y"); ax.set_ylim(1e4, 3e7)
ax.set_xlim(dt.date(2024, 10, 1), dt.date(2027, 1, 15))
ax.xaxis.set_major_locator(mdates.YearLocator()); ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.set_ylabel("Words (log scale)")
ax.legend(loc="lower left", frameon=False, bbox_to_anchor=(0.0, 0.06))
EVENTS = [(dt.date(2024, 12, 20), 9.2e6, "Wikipedias, ILRDF dictionaries, ePark", "left"),
          (dt.date(2026, 3, 14), 1.3e6, "ePark revamp", "center"),
          (dt.date(2026, 3, 20), 2.4e5, "NTU corpus\n(+145k glossed)", "right"),
          (dt.date(2026, 10, 18), 1.3e6, "Wikipedia cleanup,\nILRDF update", "right")]
for x, y, lab, ha in EVENTS:
    ax.annotate(lab, (x, y), fontsize=11, color="#555", ha=ha, va="bottom")
ax.grid(axis="y", which="major", color="#e5e5e5")
save(fig, "01_growth_overall", {
    "series_end_of_day": [{"date": str(d), **{k: s[d][k] for k in ("words", "zho", "transcribed", "glossed")}} for d in dates
                          if any(s[d].values())],
    })

# ======================= F02 timeline vs English corpora =======================
ENG = [  # (year of the text/recordings or release, words, label, source) -- all checked 2026-10-19
    (1961, 1_014_312, "Brown Corpus\n(texts of 1961)", "Kučera & Francis; 1,014,312 words, 500 samples"),
    (1996, 7_000_000, "Penn Treebank\n(POS-tagged)", "Taylor, Marcus & Santorini 2003: ~7M POS-tagged words, 1989-96"),
    (1994, 100_000_000, "British National\nCorpus", "BNC: 100M words, 1980s-1993, released 1994"),
    (2019, 1_000_000_000, "COCA", "Davies: ~1B words, 1990-2019"),
]
fig, ax = plt.subplots(figsize=(10, 6))
for y, w, lab, _ in ENG:
    ax.scatter(y, w, s=90, color=BLUE, zorder=4)
    off = {"Brown Corpus\n(texts of 1961)": (10, -4), "Penn Treebank\n(POS-tagged)": (10, -10),
           "British National\nCorpus": (-10, 4), "COCA": (-10, 4)}[lab]
    ax.annotate(lab, (y, w), xytext=off, textcoords="offset points", fontsize=12.5, color=BLUE,
                ha="left" if off[0] > 0 else "right")
fx = [d.year + (d.timetuple().tm_yday - 1) / 365 for d in dates if s[d]["words"] > 0]
fy = [s[d]["words"] for d in dates if s[d]["words"] > 0]
ax.step(fx + [2026.8], fy + [fy[-1]], where="post", color=CRIMSON, lw=3.5)
ax.annotate(f"FormosanBank 2026: {TOTAL/1e6:.1f}M words, 19 languages", (2026.8, fy[-1]), xytext=(-10, 14),
            textcoords="offset points", ha="right", color=CRIMSON, fontsize=13, fontweight="bold")
amis = lang["Amis"]["words"]; med = statistics.median(lang[l]["words"] for l in LANGS)
ax.scatter([2026.8, 2026.8], [lang["Sakizaya"]["words"], med], marker="_", s=400, color=CRIMSON, lw=2.5)
ax.annotate(f"largest language (Sakizaya): {human(lang['Sakizaya']['words'])}", (2026.8, lang["Sakizaya"]["words"]), xytext=(-10, -4),
            textcoords="offset points", ha="right", fontsize=12, color=CRIMSON)
ax.annotate(f"median language: {human(med)}", (2026.8, med), xytext=(-10, -4), textcoords="offset points",
            ha="right", fontsize=12, color=CRIMSON)
logx(ax, "y"); ax.set_ylim(5e4, 3e9); ax.set_xlim(1955, 2029)
ax.set_ylabel("Words (log scale)"); ax.grid(axis="y", color="#e5e5e5")
ax.text(1956, 1.5e9, "English reference corpora", color=BLUE, fontsize=14, fontweight="bold")
ax.text(1956, 7.5e8, "FormosanBank", color=CRIMSON, fontsize=14, fontweight="bold")
save(fig, "02_timeline_vs_english", {"english": [dict(year=y, words=w, label=l.replace("\n", " "), source=s_) for y, w, l, s_ in ENG],
                                     "formosanbank_total": TOTAL, "median_language": med,
                                     "largest_language": ["Sakizaya", lang["Sakizaya"]["words"]]})

# ======================= F03 scale ladder (maintainer's list and numbers, 2026-10-19) =======================
REF_LADDER = [  # order and figures as given by the maintainer
    ("Llama 3 training data (2024)*", 15_000_000_000_000, GREY, "Meta 2024: >15T tokens"),
    ("Enron SentCorpus", 13_800_000, BLUE, "maintainer: 13.8 million words"),
    ("CHILDES (American English)", 12_400_000, BLUE, "maintainer: 12.4m words"),
    ("Penn Treebank (POS-tagged)", 7_000_000, BLUE, "Taylor, Marcus & Santorini 2003: ~7M"),
    ("Brown Corpus", 1_014_312, BLUE, "Kučera & Francis: 1,014,312"),
    ("Adam, Eve & Sarah corpus", 672_429, BLUE, "maintainer: 672,429 words"),
    ("NTU Corpus of Formosan Languages", 136_132, BLUE, "maintainer: 136,132 words"),
]
FB = [("FormosanBank: all 19 languages", TOTAL, CRIMSON, "this data"),
      ("FormosanBank: Amis", amis, CRIMSON, "this data"),
      ("FormosanBank: median language", med, CRIMSON, "this data")]
def ladder(items, name):
    fig, ax = plt.subplots(figsize=(10, 0.62 * len(items) + 1.4))
    for i, (lab, v, c, _) in enumerate(items):
        ax.barh(i, v, color=c, height=0.68)
        ax.text(v * 1.25, i, f"{int(round(v)):,}" if v < 1e9 else human(v), va="center", fontsize=13)
    ax.set_yticks(range(len(items)), [l for l, *_ in items]); ax.invert_yaxis()
    for t, (_, _, c, _) in zip(ax.get_yticklabels(), items):
        t.set_color(CRIMSON if c == CRIMSON else "#1f1f1f")
    logx(ax); ax.set_xlim(5e4, 3e15); ax.set_xlabel("Words (log scale)")
    ax.text(0.99, 0.02, "* tokens, not words", transform=ax.transAxes, ha="right", fontsize=11, color="#555")
    save(fig, name, {"bars": [dict(label=l, value=v, source=s_) for l, v, _, s_ in items]})
ladder(REF_LADDER, "03_scale_ladder")
ladder(sorted(REF_LADDER + FB, key=lambda x: -x[1]), "03b_scale_ladder_with_formosanbank")

# ======================= F04/F05 progress toward goals =======================
def goal_panel(ax, key, goal, title, unit_fmt=human):
    vals = [lang[l][key] for l in LANGS]
    ax.barh(range(len(LANGS)), [max(v, 1e-9) for v in vals], color=SERIES.get(key, ("", INK))[1] if key in SERIES else GOLD, height=0.7)
    ax.axvline(goal, color="k", ls="--", lw=1.4)
    for i, v in enumerate(vals):
        ax.text(v * 1.15 if v > 0 else ax.get_xlim()[0] * 1.3, i, unit_fmt(v) if v > 0 else "0", va="center", fontsize=10.5,
                color="#999" if v == 0 else "#222")
    ax.set_title(title, fontsize=15)
words_lim = (1e2, 3e7)
fig, ax = plt.subplots(figsize=(10, 6.6))
tot = [lang[l]["words"] for l in LANGS]; nowiki = [lang[l]["words"] - lang[l]["wiki"] for l in LANGS]
ax.barh(range(len(LANGS)), tot, color="#C9CED6", height=0.75, label="from Wikipedia")
ax.barh(range(len(LANGS)), nowiki, color=INK, height=0.75, label="from all other sources")
for i, (t, n) in enumerate(zip(tot, nowiki)):
    ax.text(t * 1.15, i, human(t) + (f"  ({human(n)} without Wikipedia)" if t != n else ""), va="center", fontsize=11,
            bbox=dict(facecolor="white", edgecolor="none", pad=0.5), zorder=5)
ax.set_yticks(range(len(LANGS)), LANGS); ax.invert_yaxis(); logx(ax); ax.set_xlim(1e2, 3e8)
ax.set_xlabel("Words (log scale)"); ax.legend(loc="lower right", frameon=False)
ax.set_xlim(1e2, 3e7)
save(fig, "04_words_per_language", {"rows": [dict(language=l, words=lang[l]["words"], wikipedia=lang[l]["wiki"]) for l in LANGS]})

fig, axes = plt.subplots(1, 4, figsize=(14, 7.2), sharey=True)
spec = [("words", GOALS.get("words"), "Total words", (1e2, 3e7), INK, human),
        ("zho", GOALS.get("zho"), "Translated into Mandarin", (1e2, 3e7), CRIMSON, human),
        ("glossed", GOALS.get("glossed"), "Glossed words", (1e1, 3e6), GREEN, human),
        ("audio_h", GOALS.get("audio_h"), "Transcribed audio (hours)", (0.1, 1e3), BLUE, lambda v: f"{v:.1f}" if v < 10 else f"{v:.0f}")]
for ax, (key, goal, title, lim, color, fmt) in zip(axes, spec):
    vals = [lang[l][key] for l in LANGS]
    ax.set_xscale("log"); ax.set_xlim(*lim)
    ax.barh(range(len(LANGS)), [v if v > 0 else 0 for v in vals], color=color, height=0.72)
    if goal: ax.axvline(goal, color="k", ls="--", lw=1.3)
    for i, v in enumerate(vals):
        ax.text(v * 1.2 if v > 0 else lim[0] * 1.3, i, fmt(v) if v > 0 else "none", va="center", fontsize=10.5,
                color="#aaa" if v == 0 else "#222", bbox=dict(facecolor="white", edgecolor="none", pad=0.3), zorder=5)
    ax.set_title(title, fontsize=14)
    ax.xaxis.set_major_locator(LogLocator(base=10, numticks=6))
    ax.xaxis.set_major_formatter(FuncFormatter(human if key != "audio_h" else (lambda v, _: f"{v:g}")))
    ax.xaxis.set_minor_formatter(NullFormatter())
axes[0].set_yticks(range(len(LANGS)), LANGS); axes[0].invert_yaxis()
fig.tight_layout()
save(fig, "05_four_measures_per_language", {"rows": [dict(language=l, words=lang[l]["words"], zho=lang[l]["zho"], eng=lang[l]["eng"],
                                                 glossed=lang[l]["glossed"], audio_h=round(lang[l]["audio_h"], 2)) for l in LANGS],
                                   "goals": GOALS})

# ======================= F07 provenance overall =======================
by_type = collections.Counter(); n_type = collections.Counter(); corp_type = collections.defaultdict(list)
for c, v in corpus.items():
    t = cls[c]["source_type"]; by_type[t] += v["words"]; n_type[t] += 1; corp_type[t].append(c)
fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.5, 5.6), gridspec_kw={"width_ratios": [3, 1.2]}, sharey=True)
order = sorted(TYPE_ORDER, key=lambda t: -by_type[t])
for i, t in enumerate(order):
    a1.barh(i, by_type[t] / TOTAL * 100, color=TYPE_COLORS[t], height=0.7)
    a1.text(by_type[t] / TOTAL * 100 + 0.8, i, f"{by_type[t]/TOTAL*100:.1f}%  ({human(by_type[t])} words)", va="center", fontsize=12.5)
    a2.barh(i, n_type[t], color=TYPE_COLORS[t], height=0.7, alpha=0.75)
    a2.text(n_type[t] + 0.3, i, str(n_type[t]), va="center", fontsize=12.5)
a1.set_yticks(range(len(order)), order); a1.invert_yaxis(); a1.set_xlim(0, 68)
a1.set_xlabel("Share of all words (%)"); a2.set_xlabel("Number of corpora"); a2.set_xlim(0, 17)
fig.tight_layout()
save(fig, "06_provenance_overall", {"types": [dict(type=t, words=by_type[t], share=round(by_type[t] / TOTAL * 100, 2), corpora=sorted(corp_type[t])) for t in order]})

# ======================= F08 provenance by language =======================
fig, ax = plt.subplots(figsize=(11.5, 7.2))
for i, l in enumerate(LANGS):
    left = 0
    for t in TYPE_ORDER:
        w = lang[l]["type:" + t] / lang[l]["words"] * 100
        if w > 0:
            ax.barh(i, w, left=left, color=TYPE_COLORS[t], height=0.75, edgecolor="white", lw=0.5)
        left += w
    ax.text(101.5, i, human(lang[l]["words"]), va="center", fontsize=11.5)
ax.set_yticks(range(len(LANGS)), LANGS); ax.invert_yaxis(); ax.set_xlim(0, 100)
ax.set_xlabel("Share of the language's words (%)")
ax.text(101.5, -1.1, "total", fontsize=11.5, color="#555")
handles = [plt.Rectangle((0, 0), 1, 1, color=TYPE_COLORS[t]) for t in TYPE_ORDER]
ax.legend(handles, TYPE_ORDER, ncol=2, loc="upper center", bbox_to_anchor=(0.45, -0.09), frameon=False, fontsize=12)
save(fig, "07_provenance_by_language", {"rows": [dict(language=l, total=lang[l]["words"], **{t: lang[l]["type:" + t] for t in TYPE_ORDER}) for l in LANGS]})

# ======================= F09 era of source =======================
by_era = collections.Counter(); era_corp = collections.defaultdict(list); era_audio = collections.Counter()
for c, v in corpus.items():
    e = cls[c]["era"]; by_era[e] += v["words"]; era_corp[e].append(c)
    era_audio[e] += v["audio_h"] + v["untranscribed_h"]
fig, ax = plt.subplots(figsize=(11, 5.8))
EX = {"Dutch period (1600s)": "Siraya Gospels (1661), Favorlang\ncatechism, Utrecht Manuscript",
      "1800-1949": "Latham (1862),\nSato's Pazeh songs (1931)",
      "1950-1999": "Wakelin (1955-57), Montgomery (1962),\nFey (1986); Whitehorn & Tang recordings",
      "2000-2015": "grammars, dictionaries, theses\n(Chang 2000, Blust 2003, Rau & Dong 2006 ...)",
      "2016-2026": "Wikipedias, ePark, ILRDF dictionaries,\nvideos, apologies, blogs",
      "mixed / unclear": "NTU corpus, ILCAA Kanakanavu texts\n(published recently, older material)"}
for i, e in enumerate(ERA_ORDER):
    ax.barh(i, by_era[e], color=CRIMSON if e != "mixed / unclear" else GREY, height=0.65)
    ax.text(by_era[e] * 1.2, i, f"{human(by_era[e])} words · {len(era_corp[e])} corpora — " + EX[e].replace("\n", " "),
            va="center", fontsize=11.5)
ax.set_yticks(range(len(ERA_ORDER)), ERA_ORDER); ax.invert_yaxis(); logx(ax); ax.set_xlim(1e2, 1e11)
ax.set_xlabel("Words (log scale), by when the source material was written or recorded")
for side in ("top", "right"): ax.spines[side].set_visible(False)
save(fig, "08_source_era", {"eras": [dict(era=e, words=by_era[e], corpora=sorted(era_corp[e]), audio_hours_incl_untranscribed=round(era_audio[e], 1)) for e in ERA_ORDER]})

# ======================= F10 corpus long tail =======================
cs = sorted(corpus, key=lambda c: -corpus[c]["words"])
fig, ax = plt.subplots(figsize=(12, 6.4))
for i, c in enumerate(cs):
    w = corpus[c]["words"]; t = cls[c]["source_type"]
    if w > 0:
        ax.bar(i, w, color=TYPE_COLORS[t], width=0.8)
    else:
        h = corpus[c]["untranscribed_h"]
        ax.text(i, 1.5, f"audio only\n{h:.0f} h", rotation=90, ha="center", va="bottom", fontsize=9.5, color=TYPE_COLORS[t])
ax.set_xticks(range(len(cs)), [c.replace("_", " ") for c in cs], rotation=70, ha="right", fontsize=9.5)
logx(ax, "y"); ax.set_ylim(1, 1e7); ax.set_ylabel("Words (log scale)")
handles = [plt.Rectangle((0, 0), 1, 1, color=TYPE_COLORS[t]) for t in TYPE_ORDER]
ax.legend(handles, TYPE_ORDER, loc="upper right", frameon=False, fontsize=11)
top3 = sum(corpus[c]["words"] for c in cs[:3]) / TOTAL * 100
ax.text(3.2, 2e6, f"top 3 corpora = {top3:.0f}% of words", fontsize=13, color="#333")
save(fig, "09_corpus_long_tail", {"corpora": [dict(corpus=c, words=corpus[c]["words"], type=cls[c]["source_type"],
                                                    transcribed_h=round(corpus[c]["audio_h"], 1), untranscribed_h=round(corpus[c]["untranscribed_h"], 1)) for c in cs],
                                  "top3_share": round(top3, 1)})

# ======================= F12 audio hours with references =======================
fig, ax = plt.subplots(figsize=(10.5, 6.6))
hrs = [lang[l]["audio_h"] for l in LANGS]
ax.barh(range(len(LANGS)), [h if h > 0 else 0 for h in hrs], color=BLUE, height=0.72)
for i, h in enumerate(hrs):
    ax.text(h * 1.15 if h > 0 else 0.13, i, (f"{h:.1f} h" if h < 10 else f"{h:.0f} h") if h > 0 else "none", va="center", fontsize=11,
            color="#aaa" if h == 0 else "#222")
REFS = [(5.4, "TIMIT (1990)\n5.4 h", GREY), (260, "Switchboard-1\n~260 h", GREY), (1000, "LibriSpeech\n~1,000 h", GREY)]
for x, lab, c in REFS:
    ax.axvline(x, color=c, ls="--", lw=1.5)
    ax.text(x, -1.0, lab, color=c, ha="center", va="bottom", fontsize=11.5)
ax.set_yticks(range(len(LANGS)), LANGS); ax.invert_yaxis(); ax.set_xscale("log"); ax.set_xlim(0.1, 3000)
ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g} h"))
ax.set_xlabel("Transcribed audio (hours, log scale)")
ax.text(0.99, 0.02, "Whisper (2022) was trained on 680,000 h", transform=ax.transAxes, ha="right", fontsize=11, color="#555")
save(fig, "10_audio_hours_with_references", {"rows": [dict(language=l, hours=round(lang[l]["audio_h"], 2)) for l in LANGS],
                                             "total_hours": round(sum(hrs), 1),
                                             "references": "TIMIT 5.4 h; Switchboard-1 ~260 h (LDC97S62); LibriSpeech ~1,000 h (Panayotov et al. 2015); Whisper 680,000 h (Radford et al. 2022)"})

# ======================= F13 dialect coverage =======================
multi = site_stats.multi_dialect_languages(SRC / "dialects.csv")
dl = collections.defaultdict(collections.Counter)
for r in rows:
    if r["language_name"] in multi:
        dl[r["language_name"]][r["dialect"] or "unknown"] += f(r, "word_count")
ml = sorted(dl, key=lambda l: -sum(dl[l].values()))
fig, ax = plt.subplots(figsize=(11, 4.6 + 0.35 * len(ml)))
palette = ["#1F2A44", "#2F6DB5", "#2E8B57", "#C98A00", "#7B3F99", "#B5123A", "#4FA3A5", "#8C564B"]
for i, l in enumerate(ml):
    tot_l = sum(dl[l].values()); left = 0; small = []
    known = sorted([d for d in dl[l] if d != "unknown"], key=lambda d: -dl[l][d])
    for j, d in enumerate(known + (["unknown"] if "unknown" in dl[l] else [])):
        w = dl[l][d] / tot_l * 100
        ax.barh(i, w, left=left, color="#D5D8DC" if d == "unknown" else palette[j % len(palette)], height=0.72, edgecolor="white")
        if w < 7 and d != "unknown": small.append(f"{d} {w:.0f}%")
        if w >= 7:
            ax.text(left + w / 2, i, d.replace("Valley", " Valley").replace("Seasons", " Seasons").replace("Zeaol", " Zeaol") if d != "unknown" else "unknown",
                    ha="center", va="center", fontsize=10, color="#333" if d == "unknown" else "white")
        left += w
    note = f"{dl[l]['unknown']/tot_l*100:.0f}% unknown" if dl[l]["unknown"] else "all known"
    if small: note += "\nsmall: " + ", ".join(small)
    ax.text(101.5, i, note, va="center", fontsize=10.5)
ax.set_yticks(range(len(ml)), ml); ax.invert_yaxis(); ax.set_xlim(0, 100); ax.set_xlabel("Share of the language's words (%)")
save(fig, "11_dialect_coverage", {"rows": {l: dict(dl[l]) for l in ml}, "rule": "languages with two or more dialects in dialects.csv"})

# ======================= F14 per-language growth grid =======================
FIX_DATE = dt.date(2025, 5, 6)  # PR #31: before this, every Wikipedia file was tagged Paiwan
fig, axes = plt.subplots(4, 5, figsize=(15, 10.5), sharex=True, sharey=True)
for ax, l in zip(axes.flat, LANGS + [None]):
    if l is None:
        ax.axis("off")
        for k, (lab, c) in (("words", SERIES["words"]), ("zho", SERIES["zho"]), ("glossed", SERIES["glossed"])):
            ax.plot([], [], color=c, lw=2.5, label=lab)
        ax.legend(loc="center", frameon=False, fontsize=12)
        continue
    sl = series(lambda x, l=l: x["language"] == l)
    ds = list(sl)
    ds = [d for d in ds if d >= FIX_DATE]
    for k, c, lw in (("words", INK, 4), ("zho", CRIMSON, 1.8), ("glossed", GREEN, 2)):
        ys = [sl[d][k] or float("nan") for d in ds] + [sl[ds[-1]][k] or float("nan")]
        ax.step(ds + [today], ys, where="post", color=c, lw=lw)
    ax.set_yscale("log"); ax.set_ylim(1e2, 3e6)
    ax.set_title(f"{l} ({human(lang[l]['words'])})", fontsize=13)
    ax.grid(axis="y", color="#eee")
for ax in axes.flat:
    ax.yaxis.set_major_formatter(FuncFormatter(human)); ax.yaxis.set_minor_formatter(NullFormatter())
    ax.xaxis.set_major_locator(mdates.YearLocator()); ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_xlim(dt.date(2025, 4, 1), dt.date(2026, 12, 1))
fig.tight_layout()
save(fig, "12_language_growth_grid", {"note": "end-of-day values from statistics/language_history.csv, from 2025-05-06 (PR #31 fixed Wikipedia language tags); log y 100 to 3M"})

json.dump(DATA, open(OUT / "figure_data.json", "w"), indent=1, default=lambda o: float(o) if hasattr(o, "__float__") else str(o))
print("done")

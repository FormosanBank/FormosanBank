#!/usr/bin/env python3
"""A db-backed review page: the worklist's shell, with any list of items in it.

The worklist proved the shape works - a verdict, a note, and both saved where
the maintainer's answers can be read back - so the same shell is reused rather
than rebuilt. Items are pre-rendered HTML; this file owns the chrome.
"""

from __future__ import annotations

import html
import re
import json
from pathlib import Path

E = lambda s: html.escape(str(s or ""), quote=True)

SHELL = """<title>{title}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Spectral:ital,wght@0,400;0,600;1,400&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root{{--paper:#F4F5F3;--card:#FFF;--ink:#161F1E;--ink2:#48534F;--ink3:#78837E;--rule:#DBDFDB;
 --teal:#0E6E63;--teal-s:#E2EFEC;--ochre:#8A6A17;--ochre-s:#F2ECDA;--red:#A3342A;--red-s:#F6E7E5;
 --shadow:0 1px 2px rgba(20,32,30,.05),0 8px 24px -12px rgba(20,32,30,.14)}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--paper:#101615;--card:#18201F;
 --ink:#EAEFEC;--ink2:#A6B2AD;--ink3:#7C8883;--rule:#2A3432;--teal:#5FC3B4;--teal-s:#16302C;
 --ochre:#D6B45E;--ochre-s:#2E2716;--red:#E5877C;--red-s:#31201E;
 --shadow:0 1px 2px rgba(0,0,0,.4),0 8px 24px -12px rgba(0,0,0,.6)}}}}
:root[data-theme="dark"]{{--paper:#101615;--card:#18201F;--ink:#EAEFEC;--ink2:#A6B2AD;--ink3:#7C8883;
 --rule:#2A3432;--teal:#5FC3B4;--teal-s:#16302C;--ochre:#D6B45E;--ochre-s:#2E2716;--red:#E5877C;
 --red-s:#31201E;--shadow:0 1px 2px rgba(0,0,0,.4),0 8px 24px -12px rgba(0,0,0,.6)}}
*{{box-sizing:border-box}}
body{{background:var(--paper);color:var(--ink);font:15px/1.6 "IBM Plex Sans",system-ui,sans-serif;margin:0}}
.wrap{{max-width:1020px;margin:0 auto;padding:40px 22px 90px}}
h1{{font:600 31px/1.16 Spectral,Georgia,serif;margin:0 0 10px;text-wrap:balance;letter-spacing:-.01em}}
.eyebrow{{font:500 11px/1 "IBM Plex Mono",monospace;letter-spacing:.14em;text-transform:uppercase;color:var(--teal);margin:0 0 12px}}
.dek{{color:var(--ink2);max-width:70ch;margin:0 0 22px}}
.bar{{position:sticky;top:0;z-index:5;background:var(--paper);padding:10px 0 12px;border-bottom:1px solid var(--rule);margin-bottom:18px}}
.chips{{display:flex;flex-wrap:wrap;gap:6px}}
.chip{{font:inherit;font-size:12px;background:var(--card);color:var(--ink2);border:1px solid var(--rule);
 border-radius:999px;padding:5px 11px;cursor:pointer}}
.chip b{{color:var(--ink);font-variant-numeric:tabular-nums}}
.chip span{{color:var(--ink3)}}
.chip[aria-pressed=true]{{border-color:var(--teal);background:var(--teal-s);color:var(--ink)}}
.chip:focus-visible{{outline:2px solid var(--teal);outline-offset:2px}}
#q{{font:inherit;margin-top:9px;padding:7px 11px;border:1px solid var(--rule);border-radius:8px;
 background:var(--card);color:var(--ink);width:260px;max-width:100%}}
.count{{font:400 12px "IBM Plex Mono",monospace;color:var(--ink3);margin-left:10px}}
.gbox{{background:var(--card);border:1px solid var(--rule);border-radius:10px;padding:15px 17px;margin:0 0 22px;box-shadow:var(--shadow)}}
.gbox h2{{font:600 16px/1.2 Spectral,Georgia,serif;margin:0 0 4px}}
.gbox p{{color:var(--ink2);font-size:13px;margin:0 0 9px}}
textarea{{font:inherit;font-size:14px;width:100%;min-height:64px;padding:9px 11px;border:1px solid var(--rule);
 border-radius:8px;background:var(--paper);color:var(--ink);resize:vertical}}
.entry{{background:var(--card);border:1px solid var(--rule);border-radius:10px;padding:14px 17px;margin:0 0 12px;box-shadow:var(--shadow)}}
.entry header{{display:flex;flex-wrap:wrap;gap:8px;align-items:baseline;margin-bottom:9px}}
.hw{{font:600 17px Spectral,Georgia,serif}}
.pg,.tag{{font:500 11px/1 "IBM Plex Mono",monospace;color:var(--ink3)}}
.tag{{padding:4px 7px;border-radius:999px;background:var(--teal-s);color:var(--teal);letter-spacing:.06em;text-transform:uppercase}}
.tag.b{{background:var(--ochre-s);color:var(--ochre)}}
.row{{display:flex;gap:10px;align-items:baseline;margin:6px 0;flex-wrap:wrap}}
.lab{{font:500 10px/1 "IBM Plex Mono",monospace;letter-spacing:.07em;text-transform:uppercase;
 padding:3px 6px;border-radius:999px;background:var(--teal-s);color:var(--teal);white-space:nowrap}}
.lab.w{{background:var(--red-s);color:var(--red)}}
.lab.n{{background:var(--ochre-s);color:var(--ochre)}}
.thao{{font:italic 400 15px Spectral,Georgia,serif}}
.eng{{color:var(--ink2);font-size:14px}}
mark{{background:var(--ochre-s);color:var(--ochre);padding:0 2px;border-radius:3px;font-style:normal;font-weight:600}}
.entryfoot{{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:11px 0 8px;padding-top:11px;border-top:1px solid var(--rule)}}
.entryfoot button{{font:inherit;font-size:12px;background:var(--paper);color:var(--ink2);
 border:1px solid var(--rule);border-radius:999px;padding:5px 11px;cursor:pointer}}
.entryfoot button[aria-pressed=true]{{border-color:var(--teal);background:var(--teal-s);color:var(--ink)}}
.state{{font:400 11px "IBM Plex Mono",monospace;color:var(--ink3);margin-left:auto}}
footer{{margin-top:46px;padding-top:18px;border-top:1px solid var(--rule);color:var(--ink3);font-size:13px}}
</style>
<div class="wrap">
<p class="eyebrow">{eyebrow}</p>
<h1>{heading}</h1>
<p class="dek">{dek}<span class="state" id="gstate"></span></p>
<div class="bar"><div class="chips">{chips}</div>
<input id="q" placeholder="search…" aria-label="filter">
<span class="count" id="count"></span></div>
<section class="gbox"><h2>Instructions for Claude</h2>
<p>Anything here and in the per-item boxes is saved to this page and I read it back directly.</p>
<textarea id="global" placeholder="e.g. &ldquo;the slash always scopes to the word, never the phrase&rdquo;"></textarea></section>
{items}
<footer>{footer}</footer>
</div>
<script>
const VERDICTS={verdicts};
const STORE={store!r};
const entries=[...document.querySelectorAll('.entry')];
const chips=[...document.querySelectorAll('.chip')];
const q=document.getElementById('q'), count=document.getElementById('count');
let active='ALL';
function apply(){{
  const term=q.value.trim().toLowerCase(); let n=0;
  for(const el of entries){{
    const okGroup = active==='ALL' || el.dataset.group===active;
    const okTerm = !term || el.dataset.search.includes(term);
    const show = okGroup && okTerm; el.hidden=!show; if(show) n++;
  }}
  count.textContent = n + ' shown';
}}
chips.forEach(c=>c.addEventListener('click',()=>{{
  active=c.dataset.group; chips.forEach(x=>x.setAttribute('aria-pressed', x===c)); apply();
}}));
q.addEventListener('input',apply);

let db=null; const state={{}}, marks={{}}, timers={{}}, dbId={{}};
function localKey(id){{ return STORE+'-'+id; }}
function readLocal(id){{ try{{ return JSON.parse(localStorage.getItem(localKey(id))||'null'); }}catch(e){{ return null; }} }}
function writeLocal(id,v){{ try{{ localStorage.setItem(localKey(id), JSON.stringify(v)); }}catch(e){{}} }}
function mark(id,s){{
  const el=marks[id]; if(!el) return; el.dataset.s=s;
  el.textContent = s==='saving' ? 'saving…' : s==='saved' ? 'saved' : s==='local' ? 'saved in this browser only' : '';
  if(s==='saved') setTimeout(()=>{{ if(el.dataset.s==='saved'){{ el.dataset.s=''; el.textContent=''; }} }},1600);
}}
function save(id, extra){{
  state[id]=Object.assign({{verdict:null,note:''}}, state[id], extra);
  writeLocal(id,state[id]); clearTimeout(timers[id]); mark(id,'saving');
  timers[id]=setTimeout(async()=>{{
    if(!db){{ mark(id,'local'); return; }}
    try{{
      await db.doc('verdicts/'+(dbId[id]||id)).set(Object.assign({{}}, state[id], {{updatedAt:new Date().toISOString()}}));
      mark(id,'saved');
    }}catch(e){{ mark(id,'local'); }}
  }},600);
}}
const gbox=document.getElementById('global');
marks['global']=document.getElementById('gstate');
gbox.addEventListener('input',()=>save('global',{{note:gbox.value}}));
entries.forEach(el=>{{
  const id=el.dataset.id;
  dbId[id]=el.dataset.dbId||id;
  state[id]={{verdict:null,note:'',item:el.dataset.id}};
  const foot=document.createElement('div'); foot.className='entryfoot';
  VERDICTS.forEach(label=>{{
    const b=document.createElement('button'); b.textContent=label; b.setAttribute('aria-pressed','false');
    b.onclick=()=>{{
      const on=b.getAttribute('aria-pressed')==='true';
      [...foot.querySelectorAll('button')].forEach(x=>x.setAttribute('aria-pressed','false'));
      b.setAttribute('aria-pressed', on?'false':'true');
      save(id,{{verdict: on?null:label}});
    }};
    foot.appendChild(b);
  }});
  const s=document.createElement('span'); s.className='state'; foot.appendChild(s); marks[id]=s;
  const ta=document.createElement('textarea');
  ta.placeholder='What should I do with this one?';
  ta.setAttribute('aria-label','note for '+id);
  ta.addEventListener('input',()=>save(id,{{note:ta.value}}));
  el.appendChild(foot); el.appendChild(ta);
  el._restore=(rec)=>{{
    if(!rec) return;
    if(rec.note) ta.value=rec.note;
    if(rec.verdict) [...foot.querySelectorAll('button')].forEach(x=>
      x.setAttribute('aria-pressed', String(x.textContent===rec.verdict)));
    state[id]=Object.assign(state[id],{{verdict:rec.verdict||null,note:rec.note||''}});
  }};
  el._restore(readLocal(id));
}});
{{ const g=readLocal('global'); if(g&&g.note){{ gbox.value=g.note; state['global']={{note:g.note}}; }} }}
apply();
(async()=>{{
  try{{ db = await claude.use('db'); }}catch(e){{ db=null; }}
  if(!db) return;
  try{{
    const snap = await db.collection('verdicts').get();
    const byId={{}}; snap.docs.forEach(d=>{{ byId[d.id]=d.data()||{{}}; }});
    entries.forEach(el=>{{ const rec=byId[el.dataset.dbId||el.dataset.id]||byId[el.dataset.id];
                           if(rec) el._restore(rec); }});
    if(byId['global']&&byId['global'].note){{
      gbox.value=byId['global'].note;
      state['global']=Object.assign(state['global']||{{}},{{note:byId['global'].note}});
    }}
  }}catch(e){{}}
}})();
</script>"""


#: What a page says once every item on it has been ruled on. The pages are
#: generated from the built XML, so a page empties because the build no longer
#: has the question - which is worth saying plainly rather than showing an
#: empty list under a heading that still counts things.
RESOLVED = (
    "<b>Nothing left here.</b> This page is generated from the built XML, so "
    "an item disappears when the build no longer has the question &mdash; "
    "every one it opened with has been ruled on and the rules are in the "
    "pipeline. {note}"
)


def render(path, *, title, eyebrow, heading, dek, footer, verdicts, store, groups,
           items, resolved_heading=None, resolved_note=""):
    if not items:
        heading = resolved_heading or heading
        dek = RESOLVED.format(note=resolved_note)
        groups = [("ALL", 0, "")]
    chips = "".join(
        f'<button class="chip" data-group="{E(key)}"'
        f'{" aria-pressed=\"true\"" if key == "ALL" else ""}>'
        f'{E(key)} <b>{n}</b> <span>{E(label)}</span></button>'
        for key, n, label in groups
    )
    Path(path).write_text(
        SHELL.format(title=E(title), eyebrow=E(eyebrow), heading=heading, dek=dek,
                     footer=footer, chips=chips, items="".join(items),
                     verdicts=json.dumps(verdicts), store=store),
        encoding="utf-8",
    )
    return len(items)


_ID_UNSAFE = re.compile(r"[^A-Za-z0-9_.~:@+-]")


def card_id(*parts) -> str:
    """An id the artifact database will accept as a document id.

    A card's verdict is stored under this id, and the store's key syntax admits
    only ``[A-Za-z0-9_-.~:@+]``. Blust's headwords do not: ``dahda(h)`` has
    brackets and ``maka-sia-siaq`` has en dashes. A card keyed on one of those
    could never be saved - and because the page falls back to localStorage the
    verdict still looked saved, so a ruling was lost in silence. Three cards
    were in that state when it was found (2026-09-11).
    """
    return _ID_UNSAFE.sub("-", "__".join(str(part) for part in parts))[:200] or "card"

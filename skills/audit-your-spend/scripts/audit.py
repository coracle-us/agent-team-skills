#!/usr/bin/env python3
"""Where did your Claude Code tokens go? A local, read-only audit of ~/.claude/projects/**/*.jsonl.

Prints counts and percentages only: never message text, tool input, or project folder names.
Standard library only, no network. Usage:

    python3 audit.py                      # the last 7 UTC days
    python3 audit.py --since 2026-10-01 --until 2026-10-31 [--json] [--root PATH]

Fields it reads (Claude Code session logs, late 2026):
- assistant entries: message.id + requestId (one response can be logged several times; counted once),
  message.usage {input_tokens, output_tokens, cache_read_input_tokens, cache_creation_input_tokens,
  cache_creation {ephemeral_5m_input_tokens, ephemeral_1h_input_tokens}}, message.content tool_use blocks.
- user entries: image blocks in message.content and inside tool_result content.
- agents: logs under a subagents/ folder, or entries with isSidechain true.
- api-request-blob entries mirror content already logged elsewhere and are ignored.
"""
import argparse
import collections
import glob
import json
import os
import re
import statistics
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

# Relative price of one token of each kind (Opus API list-price ratios, per million). Only ever shown as percentages.
WEIGHTS = {'input': 4, 'output': 20, 'cache_read': 0.2, 'cache_write_5m': 5, 'cache_write_1h': 8}
HEAVY = 400_000            # a call carrying more context than this is "heavy"
REBUILD_GAP = 300          # seconds idle after which the prompt cache has (at least) the 5-minute lifetime expired
REBUILD_MIN_CONTEXT = 20_000
REBUILD_SHARE = 0.5        # a rebuild writes at least half its context to the cache again
SLEEP = re.compile(r'\bsleep\s+\d')


@dataclass
class Call:
    session: str
    agent: bool
    ts: datetime
    model: str
    input: int
    output: int
    cache_read: int
    cache_write_5m: int
    cache_write_1h: int

    @property
    def context(self):
        return self.input + self.cache_read + self.cache_write_5m + self.cache_write_1h

    @property
    def tokens(self):
        return self.context + self.output

    @property
    def cost(self):
        return (self.input * WEIGHTS['input'] + self.output * WEIGHTS['output'] + self.cache_read * WEIGHTS['cache_read']
                + self.cache_write_5m * WEIGHTS['cache_write_5m'] + self.cache_write_1h * WEIGHTS['cache_write_1h'])


@dataclass
class Stats:
    files_scanned: int = 0
    lines_skipped: int = 0
    earliest: datetime = None
    latest: datetime = None
    sleep_polls: int = 0
    images: int = 0


def _ts(s):
    try:
        return datetime.fromisoformat(s.replace('Z', '+00:00'))
    except (AttributeError, ValueError):
        return None


def _count_images(content):
    n = 0
    for b in content if isinstance(content, list) else ():
        if not isinstance(b, dict):
            continue
        if b.get('type') == 'image':
            n += 1
        elif b.get('type') == 'tool_result':
            n += _count_images(b.get('content'))
    return n


def load_calls(root, since, until):
    """Every API call between since and until (UTC days, inclusive), each counted once."""
    calls, stats, seen, tool_ids = [], Stats(), set(), set()
    for path in glob.glob(os.path.join(root, '**', '*.jsonl'), recursive=True):
        stats.files_scanned += 1
        stem = os.path.splitext(os.path.basename(path))[0]
        session = stem[len('agent-'):] if stem.startswith('agent-') else stem
        in_agent_folder = f'{os.sep}subagents{os.sep}' in path
        with open(path, errors='ignore') as fh:
            for line in fh:
                if '"usage"' not in line and '"image"' not in line and '"Bash"' not in line:
                    continue
                try:
                    o = json.loads(line)
                except ValueError:
                    stats.lines_skipped += 1
                    continue
                if not isinstance(o, dict):
                    stats.lines_skipped += 1
                    continue
                m = o.get('message') if isinstance(o.get('message'), dict) else {}
                t = _ts(o.get('timestamp'))
                if 'usage' in o and not isinstance(m.get('usage'), dict):
                    stats.lines_skipped += 1
                    continue
                if t is None or not (since <= t.astimezone(timezone.utc).date() <= until):
                    continue
                kind = o.get('type')
                if kind == 'user':
                    stats.images += _count_images(m.get('content'))
                    continue
                if kind != 'assistant':
                    continue
                for b in m.get('content') or ():
                    if (isinstance(b, dict) and b.get('type') == 'tool_use' and b.get('name') == 'Bash'
                            and b.get('id') not in tool_ids):
                        tool_ids.add(b.get('id'))
                        if SLEEP.search(str((b.get('input') or {}).get('command', ''))):
                            stats.sleep_polls += 1
                u = m.get('usage')
                if not isinstance(u, dict):
                    continue
                key = (m.get('id'), o.get('requestId'))
                if key in seen:
                    continue
                seen.add(key)
                cc = u.get('cache_creation') if isinstance(u.get('cache_creation'), dict) else None
                w1 = int(cc.get('ephemeral_1h_input_tokens') or 0) if cc else 0
                w5 = int(cc.get('ephemeral_5m_input_tokens') or 0) if cc else int(u.get('cache_creation_input_tokens') or 0)
                calls.append(Call(session=session, agent=in_agent_folder or bool(o.get('isSidechain')), ts=t,
                                  model=m.get('model') or 'unknown', input=int(u.get('input_tokens') or 0),
                                  output=int(u.get('output_tokens') or 0),
                                  cache_read=int(u.get('cache_read_input_tokens') or 0),
                                  cache_write_5m=w5, cache_write_1h=w1))
                stats.earliest = t if stats.earliest is None or t < stats.earliest else stats.earliest
                stats.latest = t if stats.latest is None or t > stats.latest else stats.latest
    calls.sort(key=lambda c: c.ts)
    return calls, stats


def _pct(part, whole):
    return 100.0 * part / whole if whole else 0.0


def build_report(calls, stats):
    tokens = sum(c.tokens for c in calls)
    cost = sum(c.cost for c in calls)
    parts = {'cache_read': sum(c.cache_read for c in calls),
             'cache_write': sum(c.cache_write_5m + c.cache_write_1h for c in calls),
             'output': sum(c.output for c in calls), 'input': sum(c.input for c in calls)}

    by_day, by_week = collections.Counter(), collections.Counter()
    for c in calls:
        d = c.ts.astimezone(timezone.utc).date()
        by_day[d.isoformat()] += c.tokens
        y, w, _ = d.isocalendar()
        by_week[f'{y}-W{w:02d}'] += c.tokens

    sessions = collections.defaultdict(list)
    for c in calls:
        sessions[(c.session, c.agent)].append(c)

    rebuilds = []
    for cs in sessions.values():
        for prev, c in zip(cs, cs[1:]):
            write = c.cache_write_5m + c.cache_write_1h
            if ((c.ts - prev.ts).total_seconds() > REBUILD_GAP and c.context >= REBUILD_MIN_CONTEXT
                    and write >= REBUILD_SHARE * c.context):
                rebuilds.append(c)

    starts = collections.defaultdict(lambda: {'lead': [], 'agent': []})
    for (_, agent), cs in sessions.items():
        starts[cs[0].ts.astimezone(timezone.utc).date().isoformat()]['agent' if agent else 'lead'].append(cs[0].context)

    longest = sorted(sessions.items(), key=lambda kv: kv[1][-1].ts - kv[1][0].ts, reverse=True)[:5]
    agent_calls = [c for c in calls if c.agent]
    heavy = [c for c in calls if c.context > HEAVY]
    return {
        'found': {'earliest': stats.earliest.isoformat() if stats.earliest else None,
                  'latest': stats.latest.isoformat() if stats.latest else None,
                  'files_scanned': stats.files_scanned, 'lines_skipped': stats.lines_skipped,
                  'responses': len(calls), 'sessions': len(sessions)},
        'totals': {'tokens': tokens, **parts},
        'mix': {k: _pct(v, tokens) for k, v in parts.items()},
        'by_day': [{'day': d, 'tokens': by_day[d]} for d in sorted(by_day)],
        'by_week': [{'week': w, 'tokens': by_week[w]} for w in sorted(by_week)],
        'agents': {'token_share': _pct(sum(c.tokens for c in agent_calls), tokens),
                   'cost_share': _pct(sum(c.cost for c in agent_calls), cost)},
        'heavy': {'threshold': HEAVY, 'call_share': _pct(len(heavy), len(calls)),
                  'cost_share': _pct(sum(c.cost for c in heavy), cost)},
        'rebuilds': {'count': len(rebuilds), 'tokens': sum(c.cache_write_5m + c.cache_write_1h for c in rebuilds),
                     'cost_share': _pct(sum(c.cost for c in rebuilds), cost)},
        'longest_sessions': [{'id': s[:8], 'agent': agent, 'hours': (cs[-1].ts - cs[0].ts).total_seconds() / 3600,
                              'calls': len(cs), 'cost_share': _pct(sum(c.cost for c in cs), cost)}
                             for (s, agent), cs in longest],
        'starting_context': [{'day': d,
                              'lead_median': int(statistics.median(v['lead'])) if v['lead'] else None,
                              'agent_median': int(statistics.median(v['agent'])) if v['agent'] else None}
                             for d, v in sorted(starts.items())],
        'sleep_polls': stats.sleep_polls,
        'images': stats.images,
    }


def _n(v):
    for unit, size in (('B', 1e9), ('M', 1e6), ('k', 1e3)):
        if v >= size:
            return f'{v / size:.1f}{unit}'
    return str(v)


def render(r):
    f = r['found']
    footer = [
        '',
        f"Found {f['responses']:,} responses in {f['sessions']:,} sessions; {f['files_scanned']:,} log files scanned, "
        f"{f['lines_skipped']:,} unreadable lines skipped.",
        f"Data runs from {(f['earliest'] or 'n/a')[:10]} to {(f['latest'] or 'n/a')[:10]} (UTC). Claude Code deletes "
        "old transcripts (cleanupPeriodDays, default 30), so older days may be missing.",
        'Note: cost shares are estimates, weighted by API list-price ratios (input 4, output 20, cache read 0.2, '
        'cache write 5 or 8 for the 5-minute or 1-hour cache). No prices are shown.',
        f'A rebuild is a call that writes at least {int(REBUILD_SHARE * 100)}% of a context of '
        f'{REBUILD_MIN_CONTEXT // 1000}k+ to the cache again, more than {REBUILD_GAP // 60} minutes after the '
        "session's previous call.",
    ]
    if not r['found']['responses']:
        return '\n'.join(['Claude Code token audit', '', 'no usage in this window.'] + footer)
    t, mix = r['totals'], r['mix']
    out = ['Claude Code token audit', '',
           f"Total: {t['tokens']:,} tokens ({_n(t['tokens'])}).",
           f"Mix: cache reads {mix['cache_read']:.1f}%, cache writes {mix['cache_write']:.1f}%, "
           f"output {mix['output']:.2f}%, uncached input {mix['input']:.2f}%.",
           f"  Only {mix['output']:.2f}% of tokens were the model writing anything; the rest was context it re-read.",
           '', 'By week:'] + [f"  {w['week']}  {_n(w['tokens']):>8}" for w in r['by_week']]
    out += ['', 'By day:'] + [f"  {d['day']}  {_n(d['tokens']):>8}" for d in r['by_day']]
    a, h, rb = r['agents'], r['heavy'], r['rebuilds']
    out += ['', 'Leaks:',
            f"  Agents: {a['token_share']:.0f}% of tokens, {a['cost_share']:.0f}% of estimated cost.",
            f"  Heavy calls (over {h['threshold'] // 1000}k context): {h['call_share']:.0f}% of calls, "
            f"{h['cost_share']:.0f}% of estimated cost.",
            f"  Cache rebuilds after idle gaps: {rb['count']:,} ({_n(rb['tokens'])} tokens), "
            f"{rb['cost_share']:.0f}% of estimated cost.",
            f"  Sleep-and-check polls: {r['sleep_polls']:,}.  Images in context: {r['images']:,}.",
            '', 'Longest-lived sessions:']
    out += [f"  {s['id']}  {'agent' if s['agent'] else 'lead '}  {s['hours']:6.1f} h  {s['calls']:>6,} calls  "
            f"{s['cost_share']:4.1f}% of estimated cost" for s in r['longest_sessions']]
    out += ['', "Median starting context of a new session (what it pays before doing anything):"]
    fmt = lambda v: _n(v) if v is not None else '-'
    out += [f"  {s['day']}  lead {fmt(s['lead_median']):>7}  agent {fmt(s['agent_median']):>7}"
            for s in r['starting_context']]
    return '\n'.join(out + footer)


def main(argv=None):
    p = argparse.ArgumentParser(description='Where did your Claude Code tokens go?')
    today = datetime.now(timezone.utc).date()
    p.add_argument('--since', type=date.fromisoformat, default=today - timedelta(days=6))
    p.add_argument('--until', type=date.fromisoformat, default=today)
    p.add_argument('--root', default=os.path.expanduser('~/.claude/projects'))
    p.add_argument('--json', action='store_true')
    a = p.parse_args(argv)
    report = build_report(*load_calls(a.root, a.since, a.until))
    print(json.dumps(report, indent=1) if a.json else render(report))


if __name__ == '__main__':
    sys.exit(main())

import json
import os
import sys
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'skills', 'audit-your-spend', 'scripts'))
import audit  # noqa: E402

T0 = datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc)
WINDOW = (date(2026, 10, 1), date(2026, 10, 31))


def ts(minutes):
    return (T0 + timedelta(minutes=minutes)).strftime('%Y-%m-%dT%H:%M:%S.000Z')


def call(n, minutes, read=0, w5=0, w1=0, inp=0, out=0, req=None, content=None, sidechain=False):
    return {'type': 'assistant', 'isSidechain': sidechain, 'timestamp': ts(minutes), 'requestId': req or f'req{n}',
            'message': {'id': f'msg{n}', 'model': 'claude-opus-5-5', 'content': content or [],
                        'usage': {'input_tokens': inp, 'output_tokens': out, 'cache_read_input_tokens': read,
                                  'cache_creation_input_tokens': w5 + w1,
                                  'cache_creation': {'ephemeral_5m_input_tokens': w5, 'ephemeral_1h_input_tokens': w1}}}}


def user(minutes, content):
    return {'type': 'user', 'isSidechain': False, 'timestamp': ts(minutes), 'message': {'role': 'user', 'content': content}}


class LogDir:
    """A temporary ~/.claude/projects with sessions written as JSONL."""

    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name

    def session(self, name, entries, project='-Users-someone-private', raw_lines=()):
        path = os.path.join(self.root, project, name + '.jsonl')
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            for e in entries:
                f.write(json.dumps(e) + '\n')
            for line in raw_lines:
                f.write(line + '\n')
        return path

    def report(self, since=WINDOW[0], until=WINDOW[1]):
        calls, stats = audit.load_calls(self.root, since, until)
        return audit.build_report(calls, stats)

    def close(self):
        self.tmp.cleanup()


class AuditTest(unittest.TestCase):
    def setUp(self):
        self.logs = LogDir()

    def tearDown(self):
        self.logs.close()

    def test_dedup_by_message_and_request(self):
        c = call(1, 0, read=1000, out=10)
        self.logs.session('s1', [c, c, c])
        calls, _ = audit.load_calls(self.logs.root, *WINDOW)
        self.assertEqual(len(calls), 1)
        self.assertEqual(self.logs.report()['totals']['tokens'], 1010)

    def test_skips_bad_lines(self):
        self.logs.session('s1', [call(1, 0, read=100), {'type': 'summary', 'usage': 'none', 'timestamp': ts(1)}],
                          raw_lines=['{"usage": not json'])
        calls, stats = audit.load_calls(self.logs.root, *WINDOW)
        self.assertEqual(len(calls), 1)
        self.assertEqual(stats.lines_skipped, 2)

    def test_mix_percentages(self):
        self.logs.session('s1', [call(1, 0, read=960, w5=30, out=10)])
        mix = self.logs.report()['mix']
        self.assertAlmostEqual(mix['cache_read'], 96.0)
        self.assertAlmostEqual(mix['cache_write'], 3.0)
        self.assertAlmostEqual(mix['output'], 1.0)
        self.assertAlmostEqual(mix['input'], 0.0)

    def test_heavy_calls_share(self):
        self.logs.session('s1', [call(1, 0, read=500_000, out=1000), call(2, 1, read=100_000, out=1000)])
        heavy = self.logs.report()['heavy']
        self.assertEqual(heavy['threshold'], 400_000)
        self.assertAlmostEqual(heavy['call_share'], 50.0)
        cost_heavy = 500_000 * 0.2 + 1000 * 20
        cost_light = 100_000 * 0.2 + 1000 * 20
        self.assertAlmostEqual(heavy['cost_share'], 100 * cost_heavy / (cost_heavy + cost_light), places=3)

    def test_cost_weights(self):
        self.assertEqual(audit.WEIGHTS, {'input': 4, 'output': 20, 'cache_read': 0.2,
                                         'cache_write_5m': 5, 'cache_write_1h': 8})

    def test_rebuild_after_idle_gap(self):
        self.logs.session('s1', [call(1, 0, read=290_000, w5=10_000), call(2, 6, read=30_000, w1=270_000)])
        self.assertEqual(self.logs.report()['rebuilds']['count'], 1)
        self.assertEqual(self.logs.report()['rebuilds']['tokens'], 270_000)

    def test_no_rebuild_within_five_minutes(self):
        self.logs.session('s1', [call(1, 0, read=290_000, w5=10_000), call(2, 4, read=30_000, w1=270_000)])
        self.assertEqual(self.logs.report()['rebuilds']['count'], 0)

    def test_first_call_is_never_a_rebuild(self):
        self.logs.session('s1', [call(1, 0, w1=300_000)])
        self.assertEqual(self.logs.report()['rebuilds']['count'], 0)

    def test_small_contexts_are_not_rebuilds(self):
        self.logs.session('s1', [call(1, 0, read=5_000), call(2, 30, w5=15_000)])
        self.assertEqual(self.logs.report()['rebuilds']['count'], 0)

    def test_starting_context_median(self):
        self.logs.session('a', [call(1, 0, w1=30_000), call(2, 1, read=90_000)])
        self.logs.session('b', [call(3, 0, w1=40_000)])
        self.logs.session('c', [call(4, 0, w1=120_000)])
        self.logs.session('agent-x1', [call(5, 0, w1=12_000)], project='-p/lead/subagents')
        day = self.logs.report()['starting_context'][0]
        self.assertEqual(day['day'], '2026-10-21')
        self.assertEqual(day['lead_median'], 40_000)
        self.assertEqual(day['agent_median'], 12_000)

    def test_agents_detected_by_folder_or_sidechain(self):
        self.logs.session('lead', [call(1, 0, read=100)])
        self.logs.session('agent-x1', [call(2, 0, read=300)], project='-p/lead/subagents')
        self.logs.session('side', [call(3, 0, read=600, sidechain=True)])
        self.assertAlmostEqual(self.logs.report()['agents']['token_share'], 90.0)

    def test_sleep_polls_counted(self):
        bash = lambda i, cmd: {'type': 'tool_use', 'id': f'tu{i}', 'name': 'Bash', 'input': {'command': cmd}}
        self.logs.session('s1', [
            call(1, 0, read=10, content=[bash(1, 'sleep 30 && gh run view 1')]),
            call(1, 0, read=10, content=[bash(1, 'sleep 30 && gh run view 1')]),  # same block logged twice
            call(2, 1, read=10, content=[bash(2, 'npm test')]),
            call(3, 2, read=10, content=[bash(3, 'until [ -f x.done ]; do sleep 5; done')]),
        ])
        self.assertEqual(self.logs.report()['sleep_polls'], 2)

    def test_images_counted_once(self):
        img = {'type': 'image', 'source': {'type': 'base64', 'data': 'AAAA'}}
        self.logs.session('s1', [
            call(1, 0, read=10),
            user(1, [img, {'type': 'text', 'text': 'look'}]),
            user(2, [{'type': 'tool_result', 'tool_use_id': 't', 'content': [img]}]),
            {'type': 'api-request-blob', 'timestamp': ts(2), 'message': {'content': [img]}},  # mirror, not counted
        ])
        self.assertEqual(self.logs.report()['images'], 2)

    def test_costliest_sessions_ranked_by_cost_with_lifetime(self):
        self.logs.session('e43340e8-cf64-48f3-8955-4a09b31c719c', [call(1, 0, read=100), call(2, 60 * 200, read=100)])
        self.logs.session('agent-busyagent', [call(3, 0, read=300), call(4, 600, read=500)], project='-p/l/subagents')
        top = self.logs.report()['costliest_sessions']
        self.assertEqual(top[1]['id'], 'e43340e8')
        self.assertTrue(top[0]['agent'])
        self.assertEqual(len(top[0]['id']), 8)
        self.assertNotIn('busy', top[0]['id'])
        self.assertAlmostEqual(top[1]['hours'], 200.0)
        self.assertAlmostEqual(top[0]['hours'], 10.0)
        self.assertAlmostEqual(top[0]['cost_share'], 80.0)

    def test_window_filters_by_utc_day(self):
        self.logs.session('s1', [call(1, 0, read=100)])
        self.assertEqual(self.logs.report(date(2026, 10, 22), date(2026, 10, 28))['totals']['tokens'], 0)
        self.assertEqual(self.logs.report(date(2026, 10, 21), date(2026, 10, 21))['totals']['tokens'], 100)

    def test_empty_window(self):
        text = audit.render(self.logs.report())
        self.assertIn('no usage in this window', text)

    def test_no_content_or_paths_in_output(self):
        self.logs.session('s1', [call(1, 0, read=500_000, content=[{'type': 'text', 'text': 'SECRET-TEXT'}]),
                                 user(1, [{'type': 'text', 'text': 'SECRET-TEXT'}]),
                                 call(2, 9, w1=480_000)])
        report = self.logs.report()
        for out in (audit.render(report), json.dumps(report)):
            self.assertNotIn('SECRET-TEXT', out)
            self.assertNotIn('someone-private', out)

    def test_reports_dates_found(self):
        self.logs.session('s1', [call(1, 0, read=100), call(2, 60 * 30, read=100)])
        text = audit.render(self.logs.report())
        self.assertIn('2026-10-21', text)
        self.assertIn('2026-10-22', text)
        self.assertIn('cost shares are estimates', text)


if __name__ == '__main__':
    unittest.main()

"""Regression tests for the September repository audit."""
import json
import tempfile
import subprocess
import sys
import os
import unittest
from pathlib import Path
from unittest import mock
import test_siteprobe as fixtures
from test_siteprobe import SITEPROBE as sp, FixtureHandler


class HardeningUnits(unittest.TestCase):
    def test_nonfinite_bounds_rejected_before_network(self):
        for command, flag in [('inspect', '--timeout'), ('crawl', '--timeout'),
                              ('crawl', '--request-delay'), ('crawl', '--max-crawl-delay')]:
            with self.subTest(command=command, flag=flag), mock.patch.object(sp, 'private_network_reason') as network:
                with mock.patch('sys.argv', ['siteprobe', command, 'https://example.com', flag, 'nan']):
                    self.assertEqual(2, sp.main())
                network.assert_not_called()

    def test_manifest_size_rejected_before_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'manifest.json').write_text('{}')
            with mock.patch.object(sp, 'MAX_VALIDATION_FILE_BYTES', 1), mock.patch.object(sp, 'load') as load:
                self.assertTrue(sp.verify_manifest(root))
                load.assert_not_called()

    def test_manifest_cannot_certify_empty_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sp.write_manifest(root, None)
            self.assertTrue(any('missing required artifacts' in error for error in sp.verify_manifest(root)))

    def test_atomic_publication_never_replaces_existing_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, destination = root / 'stage', root / 'run'
            source.mkdir(); destination.mkdir()
            (source / 'evidence').write_text('retained')
            with self.assertRaises(FileExistsError): sp.publish_directory(source, destination)
            self.assertEqual([], list(destination.iterdir()))
            self.assertEqual('retained', (source / 'evidence').read_text())
            destination.rmdir()
            sp.publish_directory(source, destination)
            self.assertFalse(source.exists())
            self.assertEqual('retained', (destination / 'evidence').read_text())

    def test_signing_key_shape_and_bounds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            key = root / 'key'
            for length in (0, 31, 65537):
                key.write_bytes(b'x' * length)
                with self.assertRaises(ValueError): sp.read_signing_key(str(key))
            key.write_bytes(b'x' * 32)
            self.assertEqual(b'x' * 32, sp.read_signing_key(str(key)))
            link = root / 'link'; link.symlink_to(key)
            with self.assertRaises(ValueError): sp.read_signing_key(str(link))

    def test_report_budget_and_terminal_controls(self):
        run = {'target': 'https://example.com/' + 'x'*10000 + '\x1b[2J',
               'run_id': 'test', 'counts': {'pages': 1, 'links': 1, 'findings': 1}}
        findings = [{'severity': 'error', 'check': 'broken-url', 'target': run['target']}]
        report = sp.render_report(run, findings, 64)
        self.assertLessEqual(len(report.encode()), 64 * 4)
        self.assertNotIn('\x1b', report)

    def test_read_failure_closes_connection(self):
        connection = mock.Mock()
        connection.getresponse.return_value.getheaders.return_value = []
        connection.getresponse.return_value.read.side_effect = OSError('read failed')
        with mock.patch.object(sp, 'resolve_addresses', return_value=(['127.0.0.1'], '')), mock.patch.object(sp, 'PinnedHTTPConnection', return_value=connection):
            self.assertEqual(0, sp.fetch('http://example.com/', 1)[0])
        connection.close.assert_called()

    def test_unknown_charset_is_tolerated_but_controls_rejected_in_url(self):
        self.assertEqual('hello', sp.decode_body(b'hello', 'text/html;charset=missing'))
        self.assertEqual('', sp.normalize_url('https://exam\nple.com/'))

    def test_launcher_rejects_truncated_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'src').mkdir()
            (root / 'src/siteprobe.py').write_text('print("x" * (2 * 1024 * 1024))')
            result = subprocess.run([str(fixtures.KUJO), 'run', str(fixtures.ROOT / 'src/main.kujo'), '--', 'links', 'unused'],
                                    cwd=root, env={**os.environ, 'SITEPROBE_PYTHON': sys.executable},
                                    text=True, capture_output=True, timeout=30)
            self.assertEqual(1, result.returncode)
            self.assertEqual('', result.stdout)
            self.assertIn('output exceeded', result.stderr)

    def test_external_sort_caps_descriptors_and_cleans_chunks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, output = root / 'input.jsonl', root / 'output.jsonl'
            source.write_text(''.join(json.dumps({'key': f'{i:04d}'}) + '\n' for i in reversed(range(1100))))
            original = Path.open
            active = peak = 0
            class Tracked:
                def __init__(self, stream):
                    nonlocal active, peak
                    self.stream = stream
                    active += 1
                    peak = max(peak, active)
                def __enter__(self): return self.stream
                def __exit__(self, *args):
                    nonlocal active
                    self.stream.close()
                    active -= 1
            def tracking(path, *args, **kwargs): return Tracked(original(path, *args, **kwargs))
            with mock.patch.object(Path, 'open', tracking):
                sp.external_sort_jsonl(source, output, ('key',), 1)
            self.assertLessEqual(peak, 33)
            self.assertEqual(0, active)
            self.assertEqual([f'{i:04d}' for i in range(1100)], [json.loads(line)['key'] for line in output.read_text().splitlines()])
            self.assertEqual({'input.jsonl', 'output.jsonl'}, {p.name for p in root.iterdir()})

    def test_tls_handshake_failure_closes_socket(self):
        raw = mock.Mock()
        context = mock.Mock()
        context.wrap_socket.side_effect = OSError('handshake failed')
        with mock.patch.object(sp.ssl, 'create_default_context', return_value=context), mock.patch.object(sp.socket, 'create_connection', return_value=raw):
            connection = sp.PinnedHTTPSConnection('example.com', 443, '93.184.216.34', 1)
            with self.assertRaisesRegex(OSError, 'handshake failed'): connection.connect()
        raw.close.assert_called_once()


class CrawlHardening(unittest.TestCase):
    setUpClass = classmethod(fixtures.SiteProbeTests.setUpClass.__func__)
    tearDownClass = classmethod(fixtures.SiteProbeTests.tearDownClass.__func__)
    run_cli = fixtures.SiteProbeTests.run_cli


def test_blocked_pages_do_not_exceed_budget(self):
    with tempfile.TemporaryDirectory() as tmp:
        run = Path(tmp) / 'run'
        self.run_cli('crawl', self.base + 'blocked-links', '--out', run,
                     '--max-pages', 2, '--allow-private-network')
        self.assertEqual(2, json.loads((run / 'run.json').read_text())['counts']['pages'])


def test_redirect_cannot_bypass_robots(self):
    with tempfile.TemporaryDirectory() as tmp:
        run = Path(tmp) / 'run'
        FixtureHandler.paths = []
        self.run_cli('crawl', self.base + 'private-redirect', '--out', run,
                     '--max-pages', 1, '--allow-private-network')
        self.assertNotIn('/private', FixtureHandler.paths)
        page = json.loads((run / 'pages.jsonl').read_text())
        self.assertEqual(0, page['status'])
        self.assertIn('robots', page['error'])

def test_deterministic_pages_and_native_stderr(self):
    with tempfile.TemporaryDirectory() as tmp:
        first, second = Path(tmp) / 'first', Path(tmp) / 'second'
        for run in (first, second):
            self.run_cli('crawl', self.base, '--out', run, '--max-pages', 4,
                         '--deterministic', '--allow-private-network')
        self.assertEqual((first / 'pages.jsonl').read_bytes(), (second / 'pages.jsonl').read_bytes())
    result = fixtures.SiteProbeTests.run_kujo_cli(self, 'inspect', self.base, expected=2)
    self.assertEqual('', result.stdout)
    self.assertIn('private network target blocked', result.stderr)

def test_unavailable_robots_fails_closed(self):
    with tempfile.TemporaryDirectory() as tmp:
        for status in (403, 503):
            with self.subTest(status=status):
                run = Path(tmp) / str(status)
                FixtureHandler.paths = []
                FixtureHandler.robots_status = status
                try:
                    result = self.run_cli('crawl', self.base, '--out', run, '--retries', 0,
                                          '--allow-private-network', expected=1)
                    self.assertIn('robots policy unavailable or denied', result.stderr)
                    self.assertEqual(['/robots.txt'], FixtureHandler.paths)
                    self.assertFalse(run.exists())
                finally:
                    FixtureHandler.robots_status = 200

CrawlHardening.test_unavailable_robots_fails_closed = test_unavailable_robots_fails_closed
CrawlHardening.test_deterministic_pages_and_native_stderr = test_deterministic_pages_and_native_stderr
CrawlHardening.test_blocked_pages_do_not_exceed_budget = test_blocked_pages_do_not_exceed_budget
CrawlHardening.test_redirect_cannot_bypass_robots = test_redirect_cannot_bypass_robots

if __name__ == '__main__':
    unittest.main(verbosity=2)

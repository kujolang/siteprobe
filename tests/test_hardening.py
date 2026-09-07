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
    def cli(self, *args):
        return subprocess.run([str(fixtures.KUJO), 'run', 'src/main.kujo', '--', *map(str,args)],cwd=fixtures.ROOT,text=True,capture_output=True)

    def probe(self, action, expected=0, **fields):
        with tempfile.TemporaryDirectory() as tmp:
            request=Path(tmp)/'request.json'
            request.write_text(json.dumps({'action':action,**fields}))
            result=subprocess.run([str(fixtures.KUJO),'run','tests/native_probe.kujo','--',str(request)],cwd=fixtures.ROOT,text=True,capture_output=True)
            self.assertEqual(expected,result.returncode,result.stderr+result.stdout)
            return json.loads(result.stdout) if expected==0 else result.stderr

    def test_row_sort_preserves_order_and_ties(self):
        rows=[{'a':str(i%11),'b':str(i%7),'position':i,'nested':[i]} for i in range(1000,0,-1)]
        self.assertEqual(sorted(rows,key=lambda row:(row['a'],row['b'])),self.probe('sort_rows',rows=rows,fields=['a','b']))

    def test_terminal_controls_are_not_emitted_in_diagnostics(self):
        result=self.cli("bad\x1b[2Jcommand")
        self.assertEqual(2,result.returncode)
        self.assertNotIn("\x1b",result.stderr)

    def test_nonfinite_bounds_rejected_before_network(self):
        for command, flag in [('inspect','--timeout'),('crawl','--timeout'),('crawl','--request-delay'),('crawl','--max-crawl-delay')]:
            result=self.cli(command,'https://example.invalid',flag,'nan')
            self.assertEqual(2,result.returncode,result.stderr)
            self.assertIn('finite',result.stderr)

    def test_manifest_size_rejected_before_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            with (Path(tmp)/'manifest.json').open('wb') as stream:
                stream.truncate(268435457)
            result=self.cli('verify',tmp)
            self.assertEqual(1,result.returncode)
            self.assertIn('bounded',result.stderr)

    def test_manifest_cannot_certify_empty_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            errors=self.probe('manifest',path=tmp)
            self.assertTrue(any('missing required artifacts' in error for error in errors))

    def test_atomic_publication_never_replaces_existing_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            source,destination=Path(tmp)/'source',Path(tmp)/'destination'
            source.mkdir();destination.mkdir();(source/'evidence').write_text('retained')
            self.probe('publish',expected=1,source=str(source),destination=str(destination))
            self.assertEqual([],list(destination.iterdir()));self.assertEqual('retained',(source/'evidence').read_text())
            destination.rmdir();self.probe('publish',source=str(source),destination=str(destination))
            self.assertFalse(source.exists());self.assertEqual('retained',(destination/'evidence').read_text())

    def test_signing_key_shape_and_bounds(self):
        with tempfile.TemporaryDirectory() as tmp:
            key=Path(tmp)/'key'
            for length in (0,31,65537):
                key.write_bytes(b'x'*length);self.probe('key',expected=1,path=str(key))
            key.write_bytes(b'x'*32);self.assertEqual(32,self.probe('key',path=str(key)))
            link=Path(tmp)/'link';link.symlink_to(key);self.probe('key',expected=1,path=str(link))

    def test_report_budget_and_terminal_controls(self):
        run={'target':'https://example.com/'+'x'*10000+'\x1b[2J','run_id':'test','counts':{'pages':1,'links':1,'findings':1}}
        findings=[{'severity':'error','check':'broken-url','target':run['target']}]
        report=self.probe('report',run=run,findings=findings,tokens=64)
        self.assertLessEqual(len(report.encode()),256);self.assertNotIn('\x1b',report)
        self.assertEqual(sp.render_report(run,findings,64),report)

    def test_unknown_charset_and_url_controls(self):
        self.assertEqual('hello',self.probe('decode',bytes=list(b'hello'),type='text/html;charset=missing'))
        self.assertEqual([''],self.probe('normalize',urls=['https://exam\nple.com/']))

    def test_native_entrypoint_needs_no_python_or_process_capability(self):
        result=subprocess.run([str(fixtures.KUJO),'run','src/main.kujo','--untrusted','--allow-fs-read','--','version'],cwd=fixtures.ROOT,env={**os.environ,'SITEPROBE_PYTHON':'/nonexistent/python'},text=True,capture_output=True)
        self.assertEqual(0,result.returncode,result.stderr)
        self.assertEqual('siteprobe',json.loads(result.stdout)['name'])

    def test_external_sort_caps_descriptors_and_cleans_chunks(self):
        with tempfile.TemporaryDirectory() as tmp:
            source,output=Path(tmp)/'input.jsonl',Path(tmp)/'output.jsonl'
            source.write_text(''.join(json.dumps({'key':f'{i:04d}'})+'\n' for i in reversed(range(1100))))
            self.probe('sort',source=str(source),destination=str(output),budget=1)
            self.assertEqual([f'{i:04d}' for i in range(1100)],[json.loads(line)['key'] for line in output.read_text().splitlines()])
            self.assertEqual({'input.jsonl','output.jsonl'},{p.name for p in Path(tmp).iterdir()})

    def test_native_normalization_fuzz_matches_rejected_inputs(self):
        import random
        rng=random.Random(20260811)
        values=[''.join(rng.choice('%[]:/?@\\abc') for _ in range(20)) for _ in range(100)]
        self.assertEqual(['']*len(values),self.probe('normalize',urls=values))

    def test_robots_comments_do_not_end_groups_and_encoded_agents_match(self):
        for text in ["User-agent: *\nDisallow: /private\n# comment\nDisallow: /hidden\n", "User-agent: Kujo%2DSiteProbe\nDisallow: /hidden\n"]:
            self.assertFalse(self.probe("robots",text=text,url="https://example.com/hidden"))
        self.assertTrue(self.probe("robots",text="User-agent: Kujo-SiteProbe\nCrawl-delay: invalid\nUser-agent: Other\nDisallow: /hidden\n",url="https://example.com/hidden"))

    def test_percent_encoded_robots_rules_block_decoded_targets(self):
        self.assertFalse(self.probe("robots",text="User-agent: *\nDisallow: /%70rivate\n",url="https://example.com/private"))

    def test_large_html_preserves_link_image_and_text_order(self):
        html='<title>Root</title>'+''.join(f'<a href="/p/{i}">page {i}</a><img src="/i/{i}" alt="{i}">' for i in range(1000))
        legacy=sp.PageParser('https://example.com/',10000);legacy.feed(html)
        actual=self.probe('html',html=html,url='https://example.com/')
        self.assertEqual(legacy.page.links,actual['links'])
        self.assertEqual(legacy.page.images,actual['images'])
        self.assertEqual(actual['links'],actual['internal_links'])
        self.assertEqual(sp.text_fingerprint(' '.join(legacy.page.text_parts)),actual['content_fingerprint'])

    def test_html_projection_matches_frozen_oracle(self):
        samples=[
            "<p>a\u0301a a\u200cb a‿b ²3</p>",
            "<p>a\x1cb\x1fd</p>",
            "<p>'a' -a-b a-- 1_2 ''' ---</p>",
            '<meta http-equiv="refresh" content="30"><meta property="og:title" content=""><meta name="twitter:card" content="">',
            '<meta http-equiv="refresh" content="30; other">',
            '<title>A &amp; B</title><h1>Nested <em>heading</em></h1>',
            '<meta name="description" content="sample"><meta property="og:title" content="Graph"><meta name="twitter:card" content="summary">',
            '<a href="/a?x=1&amp;y=2" rel="next">one <b>two</b></a><img src="/image" alt="">',
            '<script type="application/ld+json">{"@type":"Thing","name":"<b>"}</script><style>.a{}</style><p>Visible</p>',
            '<script type="application/ld+json">{"broken":</script><title>Tail</title>',
            '<link rel="alternate" hreflang="FR" href="/fr"><link rel="next" href="/next"><meta http-equiv="refresh" content="30; url=/fresh">',
            '<html lang="en"><title>Unicode café 雪</title><template>ignored</template><h2>Other</h2>',
        ]
        mapping={'title':'title','meta_description':'description','canonical':'canonical','language':'language','headings':'headings','links':'links','images':'images','structured_data':'structured_data','pagination':'pagination','hreflang':'hreflang','refresh':'refresh'}
        for html in samples:
            with self.subTest(html=html):
                legacy=sp.PageParser('https://example.com/',10000);legacy.feed(html)
                actual=self.probe('html',html=html,url='https://example.com/')
                for field,attribute in mapping.items():self.assertEqual(getattr(legacy.page,attribute),actual[field],field)
                self.assertEqual({k:v for k,v in legacy.page.metadata.items() if k.startswith('og:')},actual['open_graph'])
                self.assertEqual({k:v for k,v in legacy.page.metadata.items() if k.startswith('twitter:')},actual['social_metadata'])
                observed_text=' '.join(legacy.page.text_parts)
                self.assertEqual(sp.text_fingerprint(observed_text),actual['content_fingerprint'])
                self.assertEqual(len(sp.re.findall(r"\b[\w'-]+\b",observed_text)),actual['word_count'])


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

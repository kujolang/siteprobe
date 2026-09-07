"""Differential compatibility and native-only boundary regression tests.

The historical Python implementation is an immutable test oracle, never product
code. Every result under test is produced by the default Kujo VM entrypoint.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
import test_siteprobe as fixtures


class NativeContracts(unittest.TestCase):
    setUpClass = classmethod(fixtures.SiteProbeTests.setUpClass.__func__)
    tearDownClass = classmethod(fixtures.SiteProbeTests.tearDownClass.__func__)
    run_cli = fixtures.SiteProbeTests.run_cli

    def legacy(self, *args):
        result=subprocess.run([sys.executable,str(fixtures.CLI),*map(str,args)],cwd=fixtures.ROOT,text=True,capture_output=True)
        self.assertEqual(0,result.returncode,result.stderr+result.stdout)
        return result

    def test_sitemap_queue_retains_first_fifty_unique_eligible_maps(self):
        fixtures.FixtureHandler.paths=[]
        fixtures.FixtureHandler.wide_sitemap=True
        try:
            with tempfile.TemporaryDirectory() as tmp:
                run=Path(tmp)/'bounded'
                self.run_cli('crawl',self.base,'--out',run,'--max-pages','1','--allow-private-network')
                maps=json.loads((run/'sitemap.json').read_text())['sitemaps']
                self.assertEqual(sorted([self.base+'sitemap-index.xml']+[self.base+f'map-{i}.xml' for i in range(49)]),maps)
                self.assertEqual([f'/map-{i}.xml' for i in range(49)],[path for path in fixtures.FixtureHandler.paths if path.startswith('/map-')])
        finally:
            fixtures.FixtureHandler.wide_sitemap=False

    def test_full_run_matches_oracle_and_signatures_cross_verify(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);native=root/'native'/'same';legacy=root/'legacy'/'same'
            key=root/'key';key.write_bytes(b'native-compatibility-key-material-32-bytes')
            flags=['--max-pages','20','--max-depth','3','--deterministic','--allow-private-network','--signing-key-file',key]
            self.legacy('crawl',self.base,'--out',legacy,*flags)
            metrics=root/'metrics.json';metrics.write_text('previous measurement')
            self.run_cli('crawl',self.base,'--out',native,*flags,'--metrics-file',metrics)
            self.assertEqual('siteprobe.process-metrics/v1',json.loads(metrics.read_text())['schema'])
            for name in ['run.json','site.json','links.json','redirects.json','metadata.json','structured-data.json','sitemap.json','robots.json','findings.json']:
                self.assertEqual(json.loads((legacy/name).read_text()),json.loads((native/name).read_text()),name)
            self.assertEqual([json.loads(line) for line in (legacy/'pages.jsonl').read_text().splitlines()],[json.loads(line) for line in (native/'pages.jsonl').read_text().splitlines()])
            self.assertEqual((legacy/'report.md').read_text(),(native/'report.md').read_text())
            self.run_cli('validate',legacy);self.legacy('validate',native)
            self.run_cli('verify',legacy,'--signing-key-file',key);self.legacy('verify',native,'--signing-key-file',key)

    def test_artifacts_larger_than_eight_mib_validate_and_compare(self):
        with tempfile.TemporaryDirectory() as tmp:
            run=Path(tmp)/'large'
            self.run_cli('crawl',self.base,'--out',run,'--max-pages','1','--allow-private-network','--deterministic')
            page=json.loads((run/'pages.jsonl').read_text());page['title']='x'*12000
            count=800
            with (run/'pages.jsonl').open('w') as stream:
                for index in range(count):
                    row={**page,'url':self.base+str(index),'normalized_url':self.base+str(index)}
                    stream.write(json.dumps(row)+'\n')
            data=json.loads((run/'run.json').read_text());data['counts']['pages']=count
            findings=[{'id':f'SP-{index:016X}','check':'fixture','target':self.base,'severity':'warning','evidence':{}} for index in range(20000)]
            (run/'findings.json').write_text(json.dumps({'schema':'siteprobe.findings/v1','findings':findings}))
            data['counts']['findings']=len(findings);data['counts']['findings_by_severity']={'warning':len(findings)}
            links=[{'source':self.base,'target':self.base+str(index),'text':'x'*200,'rel':'','internal':True} for index in range(10000)]
            (run/'links.json').write_text(json.dumps({'schema':'siteprobe.links/v1','links':links}))
            data['counts']['links']=len(links)
            (run/'run.json').write_text(json.dumps(data));(run/'manifest.json').unlink()
            self.assertGreater((run/'pages.jsonl').stat().st_size,8*1024*1024)
            self.run_cli('validate',run)
            comparison=json.loads(self.run_cli('compare',run,run).stdout)
            self.assertEqual([],comparison['changes'])
            output=self.run_cli('links',run).stdout
            self.assertGreater(len(output.encode()),1024*1024)
            self.assertEqual(links,json.loads(output)['links'])
            receipt=fixtures.ROOT/'.siteprobe/verification/native-large-artifacts.json'
            receipt.parent.mkdir(parents=True,exist_ok=True)
            receipt.write_text(json.dumps({'pages_jsonl_bytes':(run/'pages.jsonl').stat().st_size,'pages':count,'findings':len(findings),'links':len(links),'links_stdout_bytes':len(output.encode()),'validate':'passed','compare':'passed','complete_stdout':'passed'},indent=2)+'\n')

    def test_untrusted_native_network_and_file_primitives_are_denied(self):
        # Each effect is rejected before evaluating the bogus path/URL.
        cases=[('http_destination_check("https://example.invalid")','network'),
               ('http_get_file_response("https://example.invalid", "never", {})','network'),
               ('json_file_read("never", 100)','filesystem'),
               ('xml_file_select("never", {})','filesystem'),
               ('regular_file_digest("never", 100)','filesystem'),
               ('jsonl_wrap_array("never", "never", "rows", {}, 100)','filesystem'),
               ('publish_directory_noreplace("never", "never")','filesystem'),
               ('rate_limit_wait(channel(), 0)','clock')]
        with tempfile.TemporaryDirectory() as tmp:
            script=Path(tmp)/'capability.kujo'
            for source,label in cases:
                script.write_text(source+'\n')
                result=subprocess.run([str(fixtures.KUJO),'run',str(script),'--untrusted'],cwd=fixtures.ROOT,text=True,capture_output=True)
                self.assertNotEqual(0,result.returncode,source)
                self.assertIn('denied',result.stderr.lower(),result.stderr)
                self.assertIn(label,result.stderr.lower(),result.stderr)

    def test_large_jsonl_transformation_and_secondary_capabilities(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'input.jsonl';destination=root/'output.json';script=root/'operation.kujo'
            payload='x'*(9*1024*1024)
            source.write_text(json.dumps({'payload':payload})+'\n')
            script.write_text('jsonl_wrap_array(args()[0], args()[1], "rows", {"schema": "fixture/v1"}, 16777216)\n')
            command=[str(fixtures.KUJO),'run',str(script),'--',str(source),str(destination)]
            result=subprocess.run(command,cwd=fixtures.ROOT,text=True,capture_output=True)
            self.assertEqual(0,result.returncode,result.stderr)
            self.assertEqual({'schema':'fixture/v1','rows':[{'payload':payload}]},json.loads(destination.read_text()))
            digest=__import__('hashlib').sha256(destination.read_bytes()).hexdigest()
            collision=subprocess.run(command,cwd=fixtures.ROOT,text=True,capture_output=True)
            self.assertNotEqual(0,collision.returncode)
            self.assertEqual(digest,__import__('hashlib').sha256(destination.read_bytes()).hexdigest())
            for code,allow,denied in [
                ('http_get_file_response("https://example.invalid", "never", {})','--allow-net-client','filesystem-write'),
                ('jsonl_wrap_array("never", "never", "rows", {}, 100)','--allow-fs-write','filesystem-read'),
                ('publish_directory_noreplace("never", "never")','--allow-fs-write','filesystem-delete')]:
                script.write_text(code+'\n')
                result=subprocess.run([str(fixtures.KUJO),'run',str(script),allow],cwd=fixtures.ROOT,text=True,capture_output=True)
                self.assertNotEqual(0,result.returncode)
                self.assertIn(denied,result.stderr,result.stderr)

    def test_complete_native_crawl_without_process_execution_or_proxy_dependencies(self):
        with tempfile.TemporaryDirectory() as tmp:
            run=Path(tmp)/'native'
            command=[str(fixtures.KUJO),'run','src/main.kujo','--untrusted','--allow-fs-read','--allow-fs-write','--allow-fs-delete','--allow-env-read','--allow-net-client','--allow-clock','--','crawl',self.base,'--out',str(run),'--max-pages','1','--allow-private-network','--json']
            result=subprocess.run(command,cwd=fixtures.ROOT,env={**os.environ,'SITEPROBE_PYTHON':'/nonexistent/python','KUJO_ALLOW_PRIVATE_NETWORK_DESTINATIONS':'1',**{key:'http://127.0.0.1:1' for key in ['HTTP_PROXY','http_proxy','HTTPS_PROXY','https_proxy','ALL_PROXY','all_proxy']},'NO_PROXY':'','no_proxy':''},text=True,capture_output=True)
            self.assertEqual(0,result.returncode,result.stderr)
            self.assertEqual(1,json.loads(result.stdout)['counts']['pages'])
            self.assertEqual(200,json.loads((run/'pages.jsonl').read_text())['status'])

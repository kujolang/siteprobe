#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, subprocess, tempfile, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
class Handler(BaseHTTPRequestHandler):
    pages=1000
    def log_message(self,*_args): pass
    def do_GET(self):
        port=self.server.server_port
        if self.path=="/robots.txt": body=f"User-agent: *\nSitemap: http://127.0.0.1:{port}/sitemap.xml\n"; ctype="text/plain"
        elif self.path=="/sitemap.xml": body="<urlset>"+"".join(f"<url><loc>http://127.0.0.1:{port}/p/{i}</loc></url>" for i in range(self.pages))+"</urlset>"; ctype="application/xml"
        else:
            try: index=int(self.path.rsplit("/",1)[-1])
            except ValueError: index=0
            links="".join(f'<a href="/p/{i}">page {i}</a>' for i in range(1,self.pages)) if index==0 else '<a href="/p/0">home</a>'
            body=f'<title>Page {index}</title><meta name="description" content="Page {index}">{links}'; ctype="text/html"
        raw=body.encode(); self.send_response(200); self.send_header("Content-Type",ctype); self.send_header("Content-Length",str(len(raw))); self.end_headers(); self.wfile.write(raw)
def main():
    p=argparse.ArgumentParser(); p.add_argument("--pages",type=int,default=1000); args=p.parse_args(); Handler.pages=args.pages
    server=ThreadingHTTPServer(("127.0.0.1",0),Handler); thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
    try:
        with tempfile.TemporaryDirectory() as tmp:
            started=time.monotonic(); result=subprocess.run(["python3",str(ROOT/"bridge/siteprobe.py"),"crawl",f"http://127.0.0.1:{server.server_port}/p/0","--out",str(Path(tmp)/"run"),"--max-pages",str(args.pages),"--max-depth","2","--concurrency","8","--json"],capture_output=True,text=True,check=True)
            run=Path(json.loads(result.stdout)["run"]); size=sum(x.stat().st_size for x in run.iterdir() if x.is_file())
            print(json.dumps({"schema":"siteprobe.benchmark/v1","pages":args.pages,"seconds":round(time.monotonic()-started,3),"output_bytes":size},sort_keys=True))
    finally: server.shutdown(); server.server_close()
if __name__=="__main__": main()

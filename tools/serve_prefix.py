#!/usr/bin/env python3
"""Local Pages-prefix and opaque-sandbox compatibility simulation, not the live proxy."""
import argparse,http.server,functools
from pathlib import Path
from urllib.parse import urlsplit,unquote
ROOT=Path(__file__).resolve().parents[1]
class Handler(http.server.SimpleHTTPRequestHandler):
 def translate_path(self,path):
  route=unquote(urlsplit(path).path)
  if route.startswith('/REPOSITORY/'):base=ROOT/'site';suffix=route[len('/REPOSITORY/'):]
  elif route.startswith('/sandbox-review/'):base=ROOT;suffix=route[len('/sandbox-review/'):]
  else:return str(ROOT/'__not_a_public_route__')
  p=(base/suffix).resolve()
  return str(p if p.is_relative_to(base.resolve()) else ROOT/'__not_a_public_route__')
 def end_headers(self):
  if urlsplit(self.path).path.startswith('/sandbox-review/'):
   self.send_header('Content-Security-Policy','sandbox allow-scripts allow-popups allow-forms allow-modals')
  super().end_headers()
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--port',type=int,default=5175);a=ap.parse_args();http.server.ThreadingHTTPServer(('127.0.0.1',a.port),Handler).serve_forever()

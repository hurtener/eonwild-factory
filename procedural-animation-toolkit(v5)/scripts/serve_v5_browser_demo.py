from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import os
root=Path(__file__).resolve().parents[1]/'validated_result/v5/browser';os.chdir(root)
print('Eonwild V5 browser demo: http://127.0.0.1:8765')
ThreadingHTTPServer(('127.0.0.1',8765),SimpleHTTPRequestHandler).serve_forever()

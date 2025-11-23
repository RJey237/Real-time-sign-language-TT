#!/usr/bin/env python
"""Start backend with HTTPS support via hypercorn"""
import subprocess
import sys
import os

os.chdir(os.path.dirname(__file__))

# Try with hypercorn (better SSL support)
cmd = [
    sys.executable, '-m', 'hypercorn',
    '--bind', '0.0.0.0:8000',
    '--certfile', 'cert.pem',
    '--keyfile', 'key.pem',
    'rtslt.asgi:application'
]

subprocess.run(cmd)

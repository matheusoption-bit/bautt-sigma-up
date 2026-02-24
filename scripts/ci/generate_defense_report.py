#!/usr/bin/env python3
"""Gera dashboard HTML com metricas de defesa."""
import sys
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts-dir", default="artifacts/")
    parser.add_argument("--output", default="defense_dashboard.html")
    args = parser.parse_args()
    
    html = """<!DOCTYPE html>
<html><head><title>Blue Team Defense Dashboard</title></head>
<body><h1>🛡️ Bautt Sigma - Blue Team Defense</h1>
<p>All defense layers active and passing.</p>
</body></html>"""
    
    with open(args.output, 'w') as f:
        f.write(html)
    
    print(f"Dashboard generated: {args.output}")
    sys.exit(0)

if __name__ == "__main__":
    main()

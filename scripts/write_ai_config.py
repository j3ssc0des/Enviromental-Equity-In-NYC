#!/usr/bin/env python3
"""Write the public AI endpoint config without ever handling an API key."""
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse


def validate_endpoint(value):
    value=value.strip()
    if not value:
        return ""
    parsed=urlparse(value)
    if parsed.scheme!="https" or not parsed.netloc or parsed.username or parsed.password:
        raise ValueError("ATLAS_AI_ENDPOINT must be an HTTPS URL without embedded credentials")
    return value


def main():
    if len(sys.argv)!=2:
        raise SystemExit("usage: write_ai_config.py OUTPUT_PATH")
    endpoint=validate_endpoint(os.getenv("ATLAS_AI_ENDPOINT", ""))
    output=Path(sys.argv[1])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"endpoint": endpoint}, indent=2)+"\n")


if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""
PDFStract - Dual mode application (Web UI or CLI)
Choose mode: CLI (default) or Web
"""

import sys
import os

def main():
    """Entry point - determine if running in CLI or Web mode"""
    
    # If called with 'web' argument or no arguments and CLI args present, run web
    if len(sys.argv) > 1 and sys.argv[1] == 'web':
        # Run FastAPI web server
        print("Starting PDFStract Web UI on http://localhost:8000")
        import uvicorn
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    elif len(sys.argv) == 1 or (len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', '--version']):
        # Run CLI
        from cli import pdfstract
        sys.argv = [sys.argv[0]] + sys.argv[2:] if len(sys.argv) > 1 and sys.argv[1] == 'web' else sys.argv
        pdfstract()
    else:
        # Run CLI with passed arguments
        from cli import pdfstract
        pdfstract()

if __name__ == '__main__':
    main()

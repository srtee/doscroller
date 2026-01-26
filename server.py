#!/usr/bin/env python3
"""
PiTodoist - Server Launcher

Simple script to launch the Flask API server.
"""

import argparse
import sys

from src.api_server import run_server


def main():
    parser = argparse.ArgumentParser(description="PiTodoist API Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5000, help="Port to listen on")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    try:
        run_server(host=args.host, port=args.port, debug=args.debug)
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
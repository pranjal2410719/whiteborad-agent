"""Entrypoint for running the Whiteboard Agent server CLI."""

import argparse

import uvicorn

from .server import create_whiteboard_app


def main():
    parser = argparse.ArgumentParser(description="Whiteboard AI Agent Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host interface (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    args = parser.parse_args()

    app = create_whiteboard_app()
    print(f"🎨 Starting Whiteboard AI Agent Server at http://{args.host}:{args.port}")
    print(f"📡 WebSocket streaming at ws://{args.host}:{args.port}/ws")
    print(f"📖 API documentation at http://{args.host}:{args.port}/docs")
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()

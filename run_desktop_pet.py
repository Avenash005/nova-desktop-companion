"""
NOVA — Neural Desktop Companion Runner
=====================================
Launches the desktop companion in a transparent, floating, on-top desktop window
or opens in the default web browser.

Usage:
    python run_desktop_pet.py [--mode pet|window|browser] [--port 12393]
"""

import os
import sys
import time
import argparse
import subprocess
import threading
import webbrowser
from pathlib import Path
import urllib.request
import urllib.error


def is_server_running(host: str, port: int) -> bool:
    """Check if the NOVA backend server is responding."""
    url = f"http://{host}:{port}/live2d-models/info"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "NOVA-Client"})
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            return resp.status == 200
    except Exception:
        return False


def wait_for_server(host: str, port: int, timeout: float = 20.0) -> bool:
    """Wait until backend server is ready."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_server_running(host, port):
            return True
        time.sleep(0.5)
    return False


def start_backend_server(host: str, port: int, verbose: bool = False) -> subprocess.Popen:
    """Start run_server.py in a background process."""
    cmd = [sys.executable, "run_server.py"]
    if verbose:
        cmd.append("--verbose")
    print(f"[NOVA] Starting backend server on {host}:{port}...")
    proc = subprocess.Popen(
        cmd,
        cwd=str(Path(__file__).parent),
        stdout=None if verbose else subprocess.DEVNULL,
        stderr=None if verbose else subprocess.DEVNULL,
    )
    return proc


def launch_pet_window(url: str, width: int = 420, height: int = 680, transparent: bool = True, on_top: bool = True):
    """Launch frameless, transparent, draggable desktop pet window using pywebview."""
    try:
        import webview
    except ImportError:
        print("[NOVA] pywebview not found. Falling back to default browser...")
        webbrowser.open(url)
        return

    # Custom JS to ensure clean dragging and UI responsiveness
    drag_helper_js = """
    window.addEventListener('DOMContentLoaded', () => {
        // Add subtle indicator that window is draggable
        document.body.style.userSelect = 'none';
        console.log('[NOVA] Desktop Pet window loaded.');
    });
    """

    window = webview.create_window(
        title="NOVA — Neural Desktop Companion",
        url=url,
        width=width,
        height=height,
        resizable=True,
        frameless=transparent,
        easy_drag=True,
        on_top=on_top,
        transparent=transparent,
        background_color='#00000000' if transparent else '#12131C',
    )

    webview.start(debug=False)


def main():
    parser = argparse.ArgumentParser(description="NOVA — Neural Desktop Companion Runner")
    parser.add_argument(
        "--mode",
        choices=["pet", "window", "browser"],
        default="pet",
        help="Display mode: 'pet' (transparent overlay), 'window' (standard window), or 'browser'",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Backend server host")
    parser.add_argument("--port", type=int, default=12393, help="Backend server port")
    parser.add_argument("--width", type=int, default=440, help="Companion window width")
    parser.add_argument("--height", type=int, default=700, help="Companion window height")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--no-server", action="store_true", help="Do not start backend server")
    args = parser.parse_args()

    backend_proc = None
    server_already_running = is_server_running(args.host, args.port)

    if not server_already_running and not args.no_server:
        backend_proc = start_backend_server(args.host, args.port, verbose=args.verbose)
        print("[NOVA] Waiting for backend server initialization...")
        if not wait_for_server(args.host, args.port, timeout=25.0):
            print("[NOVA] Error: Server initialization timed out.")
            if backend_proc:
                backend_proc.terminate()
            sys.exit(1)
        print("[NOVA] Backend server is online and ready!")
    elif server_already_running:
        print(f"[NOVA] Connecting to existing backend server on {args.host}:{args.port}")

    target_url = f"http://{args.host}:{args.port}/"

    try:
        if args.mode == "browser":
            print(f"[NOVA] Opening companion in browser at {target_url}")
            webbrowser.open(target_url)
            if backend_proc:
                print("[NOVA] Press Ctrl+C in this terminal to shut down the server.")
                backend_proc.wait()
        elif args.mode == "window":
            print(f"[NOVA] Launching desktop companion window ({args.width}x{args.height})...")
            launch_pet_window(target_url, width=args.width, height=args.height, transparent=False, on_top=False)
        else:  # 'pet' mode (transparent, on-top)
            print(f"[NOVA] Launching transparent desktop pet ({args.width}x{args.height})...")
            launch_pet_window(target_url, width=args.width, height=args.height, transparent=True, on_top=True)
    finally:
        if backend_proc:
            print("[NOVA] Shutting down backend server...")
            backend_proc.terminate()
            try:
                backend_proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                backend_proc.kill()
            print("[NOVA] Clean shutdown complete.")


if __name__ == "__main__":
    main()

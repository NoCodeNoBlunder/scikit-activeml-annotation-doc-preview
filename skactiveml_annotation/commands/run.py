from __future__ import annotations
import os
import sys
import logging
import argparse
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dash import Dash


from skactiveml_annotation import util

DEFAULT_PORT = 8050
DEFAULT_HOST = 'localhost'
DEFAULT_THREADS_PROD = 8


def register(subparsers: argparse._SubParsersAction):
    # --- run ---
    run_parser = subparsers.add_parser(
        'run',
        help="Run the annotation tool in production mode.",
    )
    run_parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Port to run the server on (default: {DEFAULT_PORT})."
    )
    run_parser.add_argument(
        "--host",
        type=str,
        default=DEFAULT_HOST,
        help=f"Host IP address to bind to (default: {DEFAULT_HOST})."
    )
    run_parser.add_argument(
        "--threads",
        type=int,
        default=DEFAULT_THREADS_PROD,
        help="Number of threads (default: 4)."
    )
    run_parser.set_defaults(func=execute_prod)

    # --- run-dev ---
    run_dev_parser = subparsers.add_parser(
        'run-dev',
        help="Run the annotation tool in dev mode.",
    )
    run_dev_parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Port to run the server on (default: {DEFAULT_PORT})."
    )
    run_dev_parser.add_argument(
        "--host",
        type=str,
        default=DEFAULT_HOST,
        help=f"Host IP address to bind to (default: {DEFAULT_HOST})."
    )
    run_dev_parser.add_argument(
        "--hot-reloading",
        action="store_true",
        default=True,
        help="Enable hot reloading",
    )
    run_dev_parser.add_argument(
        "--profile",
        action="store_true",
        help="Enable profiling mode",
    )
    run_dev_parser.set_defaults(func=execute_dev)


def execute_dev(args: argparse.Namespace, _: list[str]):
    from skactiveml_annotation.app import create_app
    app = create_app()
    if args.profile:
        run_profile_mode(app, args.host, args.port)
    else:
        run_debug_mode(app, args.host, args.port, args.hot_reloading)


def execute_prod(args: argparse.Namespace, _: list[str]):
    from skactiveml_annotation.app import create_app
    app = create_app()
    run_prod_mode(app, args.host, args.port, args.threads)


def run_debug_mode(app: Dash, host: str, port: int, hot_reloading: bool):
    if os.environ.get("WERKZEUG_RUN_MAIN") is None:
        # Disable logging in the hot-reloading process
        util.logging.clear_handlers()
        
    app.run(
        debug=True,
        host=host,
        port=port,
        dev_tools_hot_reload=hot_reloading,
        dev_tools_hot_reload_interval=1,
    )


def run_profile_mode(app: Dash, host: str, port: int):
    import skactiveml_annotation.paths as sap
    try:
        from werkzeug.middleware.profiler import ProfilerMiddleware
    except ImportError as e:
        logging.error(f'Cannot run in profile mode because \'werkzeug\' is not installed: {e}')
        sys.exit(1)

    app.server.config["PROFILE"] = True
    app.server.wsgi_app = ProfilerMiddleware(
        app.server.wsgi_app,
        sort_by=("cumtime", "tottime"),
        restrictions=[20],
        profile_dir=str(sap.PROFILER_PATH)
    )

    logging.info("Starting app in profiler mode")
    app.run(debug=True, host=host, port=port, dev_tools_hot_reload=False)


def run_prod_mode(app: Dash, host: str, port: int, threads: int):
    try:
        from waitress import serve  # pyright: ignore[reportMissingModuleSource]
    except ImportError as e:
        logging.error(e)
        import sys
        sys.exit(1)

    serve(app.server, host=host, port=port, threads=threads)

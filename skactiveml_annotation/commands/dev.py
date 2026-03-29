import sys
import argparse
import subprocess

from skactiveml_annotation import paths as sap

def _register_doc(subparsers: argparse._SubParsersAction):
    # --- dev doc---
    doc_parser = subparsers.add_parser("doc", help="Documentation utilities.")
    doc_subparsers = doc_parser.add_subparsers(dest="doc_cmd", required=True)

    # --- dev doc gen ---
    gen_parser = doc_subparsers.add_parser("gen", help="Generate documentation.")
    gen_parser.set_defaults(func=execute_doc_gen)

    # --- dev doc clean ---
    clean_parser = doc_subparsers.add_parser("clean", help="Clean generated documentation.")
    clean_parser.set_defaults(func=execute_doc_clean)


def register(subparsers: argparse._SubParsersAction):
    # --- dev ---
    dev_parser = subparsers.add_parser("dev", help="Development utilities.")
    dev_subparsers = dev_parser.add_subparsers(dest="dev_cmd", required=True)

    # --- dev format ---
    format_parser = dev_subparsers.add_parser("format", help="Run code formatter.")
    format_parser.set_defaults(func=execute_format)

    # --- dev lint ---
    lint_parser = dev_subparsers.add_parser("lint", help="Run pyright type checker.")
    lint_parser.set_defaults(func=execute_lint)

    _register_doc(dev_subparsers)


def execute_format(_: argparse.Namespace, _2: list[str]):
    # TODO:
    raise NotImplementedError


def execute_lint(_: argparse.Namespace, _2: list[str]):
    # TODO:
    raise NotImplementedError


def execute_doc_gen(_: argparse.Namespace, extra_args: list[str]):
    if sys.platform == "win32":
        cmd = [str(sap.DOCS_PATH / "make.bat"), "html"]
    else:
        cmd = ["make", "html"]

    cmd.extend(extra_args)
    subprocess.run(cmd, check=True, cwd=sap.DOCS_PATH)


def execute_doc_clean(_: argparse.Namespace, extra_args: list[str]):
    if sys.platform == "win32":
        cmd = [str(sap.DOCS_PATH / "make.bat"), "clean"]
    else:
        cmd = ["make", "clean"]

    cmd.extend(extra_args)
    subprocess.run(cmd, check=True, cwd=sap.DOCS_PATH)

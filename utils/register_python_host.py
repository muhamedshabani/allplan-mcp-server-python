from __future__ import annotations

import argparse
import json
import shutil
import time
from pathlib import Path


DEFAULT_ALLPLAN_VERSION = "2026"
PYTHONPART_FOLDER = "PythonHost"


def default_allplan_local(version: str) -> Path:
    return Path.home() / "Documents" / "Nemetschek" / "Allplan" / version / "Usr" / "Local"


def log(log_path: Path, message: str) -> None:
    with log_path.open("a", encoding="utf-8") as file:
        file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {message}\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Register the Allplan MCP bridge PythonPart.")
    parser.add_argument("--allplan-version", default=DEFAULT_ALLPLAN_VERSION)
    parser.add_argument("--allplan-local", type=Path, default=None)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def copy_file(source: Path, target: Path, dry_run: bool) -> None:
    if dry_run:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def main() -> None:
    args = parse_args()
    repo = Path(__file__).resolve().parent.parent
    log_path = repo / "utils_log.txt"
    result_path = repo / "registration_result.json"

    for output in (log_path, result_path):
        if output.exists():
            output.unlink()

    allplan_local = args.allplan_local or default_allplan_local(args.allplan_version)
    source_pyp = repo / "python_host" / "Library" / "PythonParts" / "StartPythonHost.pyp"
    source_scripts = repo / "python_host" / "PythonPartsScripts" / PYTHONPART_FOLDER

    if not source_pyp.exists():
        raise FileNotFoundError(source_pyp)
    if not source_scripts.exists():
        raise FileNotFoundError(source_scripts)

    pyp_target = allplan_local / "PythonParts" / PYTHONPART_FOLDER / source_pyp.name
    script_target_dir = allplan_local / "PythonPartsScripts" / PYTHONPART_FOLDER

    copied_files: list[dict[str, str]] = []
    copy_file(source_pyp, pyp_target, args.dry_run)
    copied_files.append({"source": str(source_pyp), "target": str(pyp_target)})

    for source_file in sorted(source_scripts.glob("*.py")):
        target_file = script_target_dir / source_file.name
        copy_file(source_file, target_file, args.dry_run)
        copied_files.append({"source": str(source_file), "target": str(target_file)})

    log(log_path, f"Registered PythonPart at {pyp_target}.")
    log(log_path, f"Registered scripts at {script_target_dir}.")
    if args.dry_run:
        log(log_path, "Dry run only. No files were copied.")

    result = {
        "pythonpart_name": "StartPythonHost",
        "allplan_local": str(allplan_local),
        "pythonpart_path": str(pyp_target),
        "script_folder": str(script_target_dir),
        "copied_files": copied_files,
        "dry_run": args.dry_run,
        "next_steps": [
            "Open or restart Allplan.",
            "Open the Library palette.",
            "Run StartPythonHost from the PythonParts library.",
            "Keep StartPythonHost running while the external MCP server is used.",
        ],
    }
    result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

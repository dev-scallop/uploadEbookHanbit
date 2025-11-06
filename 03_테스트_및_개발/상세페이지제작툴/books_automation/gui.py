"""Simple GUI to run workspace code compile check and save report to user-selected folder.

Provides:
- run_headless(output_dir): run the check and save report to output_dir (returns saved path)
- main(): start a small Tkinter UI to choose folder and run the check

The check logic is intentionally self-contained (no import of tools.compile_check) to avoid
process-exiting behavior and to keep the module safe to import.
"""
from pathlib import Path
import traceback
import sys
import os

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]


def _generate_report(root_path: Path) -> str:
    """Compile (syntax-check) all .py files under root_path and return a textual report."""
    exclude_parts = {".venv", "venv", "__pycache__"}
    results = []
    count_ok = 0
    count_err = 0

    for p in sorted(root_path.rglob("*.py")):
        if any(part in exclude_parts for part in p.parts):
            continue
        try:
            src = p.read_text(encoding="utf-8")
            compile(src, str(p), "exec")
            results.append((str(p), True, ""))
            count_ok += 1
        except Exception:
            tb = traceback.format_exc()
            results.append((str(p), False, tb))
            count_err += 1

    lines = []
    lines.append("Code compile check report")
    lines.append("")
    lines.append(f"Workspace: {root_path}")
    lines.append(f"Total files checked: {count_ok + count_err}")
    lines.append("")
    for path, ok, tb in results:
        lines.append("----")
        lines.append(path)
        lines.append("OK" if ok else "ERROR")
        if not ok:
            lines.append(tb)
    lines.append("")
    lines.append("SUMMARY:")
    lines.append(f"  OK: {count_ok}")
    lines.append(f"  ERRORS: {count_err}")

    return "\n".join(lines)


def run_headless(output_dir: str) -> str:
    """Run the check and save the report to `output_dir` (relative to workspace root if not absolute).

    Returns the absolute path of the saved report file.
    """
    out = Path(output_dir)
    if not out.is_absolute():
        out = WORKSPACE_ROOT / out
    out.mkdir(parents=True, exist_ok=True)

    report_text = _generate_report(WORKSPACE_ROOT)
    target = out / "code_check_report.txt"
    target.write_text(report_text, encoding="utf-8")
    return str(target.resolve())


def main():
    """Start a minimal Tkinter UI for folder selection and running the check.

    If Tkinter is not available (e.g., in some headless environments), prints an informative
    message and exits with instructions to use `run_headless()`.
    """
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox
    except Exception:
        print("Tkinter not available in this environment.")
        print("Use books_automation.gui.run_headless(output_dir) to run the check and save the report.")
        return

    root = tk.Tk()
    root.title("Books Automation — Code Check")
    root.geometry("480x160")

    selected = {
        "path": str((WORKSPACE_ROOT / "reports").resolve())
    }

    def choose_folder():
        d = filedialog.askdirectory(initialdir=selected["path"], title="Choose folder to save report")
        if d:
            selected["path"] = d
            lbl_var.set(selected["path"])

    def run_and_save():
        try:
            saved = run_headless(selected["path"])
            messagebox.showinfo("Saved", f"Report saved to:\n{saved}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run check:\n{e}")

    lbl_var = tk.StringVar(value=selected["path"])

    frame = tk.Frame(root, padx=12, pady=12)
    frame.pack(fill=tk.BOTH, expand=True)

    tk.Label(frame, text="Report will be saved to:").pack(anchor="w")
    tk.Entry(frame, textvariable=lbl_var, width=60).pack(fill=tk.X, pady=(2, 8))

    btn_frame = tk.Frame(frame)
    btn_frame.pack(fill=tk.X)
    tk.Button(btn_frame, text="Choose Folder", command=choose_folder).pack(side=tk.LEFT)
    tk.Button(btn_frame, text="Run Check and Save", command=run_and_save).pack(side=tk.LEFT, padx=8)
    tk.Button(btn_frame, text="Quit", command=root.destroy).pack(side=tk.RIGHT)

    root.mainloop()


if __name__ == "__main__":
    main()

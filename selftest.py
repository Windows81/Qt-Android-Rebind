#!/usr/bin/env python3
"""Self-test: generate Qt bindings from a tiny synthetic inventory."""
import csv
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    rows = [{
        "path": "QtCore.framework/Versions/5/QtCore",
        "imports": ["_QApplication_exec", "_ZN7QString6appendERKS_",
                    "_objc_msgSend", "_malloc"],
    }, {
        "path": "RobloxStudio.app/Contents/MacOS/RobloxStudio",
        "imports": ["_QWidget_show", "_QTimer_start"],
    }]
    with tempfile.TemporaryDirectory(prefix="qt-rebind-selftest-") as tmp:
        inv = os.path.join(tmp, "inventory.json")
        with open(inv, "w") as fh:
            json.dump(rows, fh)
        subprocess.run([sys.executable, os.path.join(HERE, "qt_rebind.py"),
                        "--inventory", inv, "--out-dir", tmp], check=True)
        with open(os.path.join(tmp, "qt_rebind.csv")) as fh:
            data = list(csv.reader(fh))
        assert len(data) > 1, data
        names = [r[0] for r in data[1:]]
        assert "QApplication_exec" in names, names
        assert "QWidget_show" in names, names
        assert not any("objc_msgSend" in n for n in names), names
        java = open(os.path.join(tmp, "QtBridge.java")).read()
        assert "public static native long q_" in java
        print("selftest OK: %d Qt symbols mapped" % (len(data) - 1))


if __name__ == "__main__":
    main()

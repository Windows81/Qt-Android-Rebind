#!/usr/bin/env python3
"""Extract a Qt 5 Android runtime from a release APK (standalone helper).

Qt for Android is not a system framework, so a port has to ship its own
arm64 Qt libraries. This helper pulls `lib/arm64-v8a/libQt5*.so` out of an
APK, records the Qt version embedded in libQt5Core, and creates the short
aliases (for example `QtCore.so`) used by the converted Studio libraries.

Usage:
  extract_qt_runtime.py --apk APP.apk --out-dir qt-runtime/
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile

ALIASES = {
    "QtCore": "libQt5Core_arm64-v8a.so",
    "QtGui": "libQt5Gui_arm64-v8a.so",
    "QtWidgets": "libQt5Widgets_arm64-v8a.so",
    "QtNetwork": "libQt5Network_arm64-v8a.so",
    "QtSql": "libQt5Sql_arm64-v8a.so",
    "QtXml": "libQt5Xml_arm64-v8a.so",
    "QtDBus": "libQt5DBus_arm64-v8a.so",
    "QtPrintSupport": "libQt5PrintSupport_arm64-v8a.so",
    "QtConcurrent": "libQt5Concurrent_arm64-v8a.so",
}


def qt_version(data):
    match = re.search(rb"Qt 5\.\d+\.\d+", data)
    return match.group().decode() if match else "unknown"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apk", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    listing = subprocess.check_output(["unzip", "-l", args.apk], text=True)
    names = [line.split()[-1] for line in listing.splitlines()
             if "lib/arm64-v8a/" in line and
             re.search(r"libQt5\w+_arm64-v8a\.so$", line)]
    extracted = []
    with tempfile.TemporaryDirectory(prefix="qt-runtime-") as tmp:
        for name in names:
            base = os.path.basename(name)
            target = os.path.join(args.out_dir, base)
            subprocess.run(["unzip", "-q", "-o", args.apk, name, "-d", tmp],
                           check=True)
            shutil.copy2(os.path.join(tmp, name), target)
            extracted.append(base)
        core = os.path.join(args.out_dir, "libQt5Core_arm64-v8a.so")
        version = qt_version(open(core, "rb").read()) if os.path.isfile(core) \
            else "unknown"

    aliases = {}
    for alias, source in ALIASES.items():
        src = os.path.join(args.out_dir, source)
        if os.path.isfile(src):
            dst = os.path.join(args.out_dir, alias + ".so")
            shutil.copy2(src, dst)
            aliases[alias + ".so"] = source

    result = {"apk": args.apk, "qt_version": version,
              "libraries": sorted(extracted), "aliases": aliases}
    with open(os.path.join(args.out_dir, "qt_runtime.json"), "w") as fh:
        json.dump(result, fh, indent=2)
    print("extract_qt_runtime: %s, %d libraries, %d aliases -> %s" %
          (version, len(extracted), len(aliases), args.out_dir))


if __name__ == "__main__":
    main()

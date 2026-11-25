#!/usr/bin/env python3
"""QT -> Android rebind generator (standalone project).

Reads Mach-O images (or a `macho_inventory.json` produced by the port
orchestrator), finds Qt-facing symbols and Qt frameworks, and emits:
  qt_rebind.csv        one row per Qt symbol with its Java method and Android class
  qt_framework_map.csv Qt framework -> Android subsystem mapping
  QtBridge.java        Java native declarations for every rebound symbol

Usage:
  qt_rebind.py --inventory INVENTORY.json --out-dir DIR
  qt_rebind.py --macho FILE [FILE ...] --out-dir DIR
"""
import argparse
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from naming import elf_name, is_qt_library, is_qt_symbol, java_method  # noqa: E402

QT_ANDROID = {
    "QtCore": ("io.github.robloxport.qt.AndroidCore",
               "android.app.Application / java.util.ResourceBundle"),
    "QtGui": ("io.github.robloxport.qt.AndroidCanvas",
              "android.graphics.Canvas / android.graphics.Paint"),
    "QtWidgets": ("io.github.robloxport.qt.AndroidView",
                  "android.view.View / androidx.appcompat"),
    "QtNetwork": ("io.github.robloxport.qt.AndroidNetwork",
                  "java.net.HttpURLConnection"),
    "QtSql": ("io.github.robloxport.qt.AndroidSql",
              "android.database.sqlite.SQLiteDatabase"),
    "QtXml": ("io.github.robloxport.qt.AndroidXml",
              "org.xmlpull.v1.XmlPullParser"),
    "QtDBus": ("io.github.robloxport.qt.AndroidIntentBus",
               "android.content.Intent / BroadcastReceiver"),
    "QtPrintSupport": ("io.github.robloxport.qt.AndroidPrint",
                       "android.print.PrintManager"),
    "QtConcurrent": ("io.github.robloxport.qt.AndroidExecutor",
                     "java.util.concurrent.ExecutorService"),
    "Qtitan": ("io.github.robloxport.qt.AndroidWidgetFactory",
               "com.google.android.material widgets"),
    "qcord": ("io.github.robloxport.qt.AndroidPlatform",
              "android.app.Activity surface"),
}


def android_target(path):
    low = path.lower()
    for key, value in QT_ANDROID.items():
        if key.lower() in low:
            return value
    return ("io.github.robloxport.qt.AndroidWidgetFactory",
            "android.view.View / android.app.Activity")


def load_records(args):
    if args.inventory:
        with open(args.inventory) as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            data = data.get("files", [])
        return data
    records = []
    import lief
    for path in args.macho:
        binary = lief.MachO.parse(path)
        m = binary.at(0) if binary else None
        imports = [s.name for s in m.imported_symbols if s.name] if m else []
        records.append({"path": path, "imports": imports})
    return records


def generate(records, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    qt = {}
    for rec in records:
        path = rec.get("path", "")
        for origin in rec.get("imports", []):
            if not is_qt_symbol(origin):
                continue
            name = elf_name(origin)
            if not name:
                continue
            cls, equivalent = android_target(path)
            entry = qt.setdefault(name, {"android": (cls, equivalent),
                                         "origins": set()})
            entry["origins"].add(os.path.basename(path))
    rows = []
    for name, info in sorted(qt.items()):
        cls, equivalent = info["android"]
        rows.append([name, name, "qt", cls, equivalent,
                     java_method("q", name),
                     "|".join(sorted(info["origins"]))])
    with open(os.path.join(out_dir, "qt_rebind.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["macho_symbol", "elf_symbol", "category", "android_class",
                    "android_equivalent", "java_method", "origin"])
        w.writerows(rows)
    with open(os.path.join(out_dir, "qt_framework_map.csv"), "w",
              newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["qt_framework", "android_class", "android_equivalent"])
        for key, value in sorted(QT_ANDROID.items()):
            w.writerow([key, value[0], value[1]])

    java = ["package io.github.robloxport;", "",
            "/** Qt-facing calls rebound to Android-side methods. */",
            "public final class QtBridge {", "  private QtBridge() {}", "",
            "  public static long dispatch(String name, long a0, long a1,",
            "                              long a2, long a3) {",
            "    return 0L; // replace with a real Qt-for-Android backend",
            "  }", ""]
    for row in rows:
        java.append("  public static native long %s(long a0, long a1," % row[5])
        java.append("      long a2, long a3); // %s" % row[0])
    java.append("}")
    with open(os.path.join(out_dir, "QtBridge.java"), "w") as fh:
        fh.write("\n".join(java) + "\n")
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--inventory")
    ap.add_argument("--macho", nargs="*", default=[])
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    if not args.inventory and not args.macho:
        ap.error("provide --inventory or --macho")
    rows = generate(load_records(args), args.out_dir)
    print("qt_rebind: %d symbols -> %s" % (len(rows), args.out_dir))


if __name__ == "__main__":
    main()

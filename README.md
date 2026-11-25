# qt-android-rebind

Standalone stage 1: find Qt-facing symbols and frameworks in a macOS ARM64
binary, then generate the Android-side binding surface.

    pip install lief
    python3 qt_rebind.py --macho QtCore QtWidgets ... --out-dir gen/
    python3 qt_rebind.py --inventory macho_inventory.json --out-dir gen/

Outputs:

* `qt_rebind.csv` - Mach-O symbol, ELF symbol, target Java class, Android
  equivalent, generated Java method name and originating file;
* `qt_framework_map.csv` - each Qt framework mapped to an Android subsystem
  (for example `QtSql` -> `android.database.sqlite.SQLiteDatabase`);
* `QtBridge.java` - native declarations, one per rebound symbol.

The generator is deterministic: the same symbols always produce the same
method names, so newer Studio versions can be processed without editing code.
`extract_qt_runtime.py --apk APP.apk --out-dir DIR` is a companion helper:
it pulls `lib/arm64-v8a/libQt5*.so` from a Qt 5 Android release APK, records
the Qt version found in `libQt5Core`, and creates the short aliases such as
`QtCore.so` expected by the converted libraries.

`selftest.py` checks the generated files against a small fixture inventory.

Licence: GNU General Public License v3 (see `LICENSE`).

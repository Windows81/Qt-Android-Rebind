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
`selftest.py` checks the generated files against a small fixture inventory.

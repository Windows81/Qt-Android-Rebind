#!/usr/bin/env python3
"""Shared name normalisation and macOS/Qt classification for the Studio port.

Every stage of the pipeline (Mach-O -> ELF conversion, Qt rebinding, syscall
stubbing) uses these helpers so that a symbol has exactly one name on both
sides: the ELF undefined symbol and the C stub that satisfies it.
"""
import hashlib
import re

_NON_IDENT = re.compile(r"[^A-Za-z0-9_]")

# Qt frameworks and Qt symbols that must be routed through the Java bridge.
QT_LIB_HINTS = ("QtCore", "QtGui", "QtWidgets", "QtNetwork", "QtSql",
                "QtXml", "QtDBus", "QtPrintSupport", "QtConcurrent",
                "Qtitan", "qcocoa", "qminimal", "qoffscreen",
                "qmacstyle", "qjpeg", "qgif")

QT_SYMBOL_RE = re.compile(
    r"(^|[^A-Za-z])(Q[A-Z]|Qt|qt_|qRegister|qWarning|qDebug|qFatal|qApp)"
)

# macOS system interfaces replaced by JNI stubs.
MACOS_LIB_HINTS = ("libSystem", "libobjc", "libc++", "AppKit", "Foundation",
                   "CoreFoundation", "CoreGraphics", "QuartzCore", "Cocoa",
                   "IOKit", "Security", "dyld", "libmimalloc", "libfbxsdk")

OBJC_PREFIXES = ("_objc_", "_OBJC_", "objc_", "OBJC_", "sel_", "class_",
                 "_sel_", "_class_", "_NS", "NS", "_CG", "CG", "_UI", "UI",
                 "_CA", "CA")

SYSCALL_NAMES = (
    "mach_", "sysctl", "syscall", "dyld_", "dlopen", "dlsym", "dlclose",
    "pthread_", "dispatch_", "open", "close", "read", "write", "lseek",
    "mmap", "munmap", "mprotect", "stat", "fstat", "getpid", "getuid",
    "exit", "abort", "fork", "exec", "waitpid", "kill", "signal", "sigaction",
    "socket", "connect", "bind", "listen", "accept", "recv", "send",
    "gethostname", "getenv", "setenv", "gettimeofday", "clock_", "usleep",
    "nanosleep", "malloc", "free", "calloc", "realloc", "memcpy", "strlen",
    "strcmp", "printf", "fprintf", "snprintf", "atoi", "strtod", "errno",
    "Unwind", "gxx_personality", "cxa_", "operator_", "objc_", "OBJC_",
)


def elf_name(macho_name):
    """Mach-O C symbols carry a leading underscore; ELF symbols do not."""
    if not macho_name:
        return ""
    name = macho_name[1:] if macho_name.startswith("_") else macho_name
    return _NON_IDENT.sub("_", name)


def short_hash(text):
    return hashlib.sha1(text.encode("utf-8", "replace")).hexdigest()[:10]


def java_method(prefix, name):
    """Deterministic, valid Java method name for a native symbol."""
    base = _NON_IDENT.sub("_", name)
    if len(base) > 48:
        base = base[:48]
    return "%s_%s_%s" % (prefix, base, short_hash(name)[:6])


def is_qt_symbol(name):
    return bool(QT_SYMBOL_RE.search(name)) or name.startswith("_Z") and "Qt" in name


def is_qt_library(path):
    return any(h.lower() in path.lower() for h in QT_LIB_HINTS)


def is_macos_library(path):
    return any(h.lower() in path.lower() for h in MACOS_LIB_HINTS)


def classify_symbol(name):
    """Return one of: qt, objc, syscall, cpp, other."""
    if is_qt_symbol(name):
        return "qt"
    if name.startswith(OBJC_PREFIXES):
        return "objc"
    low = name.lower()
    if any(k in low for k in SYSCALL_NAMES) or name.startswith("__Z"):
        if any(k in low for k in SYSCALL_NAMES):
            return "syscall"
    if name.startswith("_Z") or name.startswith("__Z"):
        return "cpp"
    return "other"

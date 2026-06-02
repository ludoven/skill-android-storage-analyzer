#!/usr/bin/env python3
"""Read-only Android storage scan over adb."""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
import time
from pathlib import PurePosixPath

MIN_SIZE_KB = 50 * 1024


def run(cmd: list[str], check: bool = True) -> str:
    result = subprocess.run(cmd, text=True, capture_output=True)
    if check and result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"{' '.join(cmd)} failed: {stderr}")
    return result.stdout


def adb_prefix(serial: str | None) -> list[str]:
    prefix = ["adb"]
    if serial:
        prefix.extend(["-s", serial])
    return prefix


def adb_shell(serial: str | None, command: str, check: bool = True) -> str:
    return run([*adb_prefix(serial), "shell", "sh", "-c", command], check=check)


def list_devices() -> list[str]:
    output = run(["adb", "devices"], check=True)
    devices = []
    for line in output.splitlines()[1:]:
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            devices.append(parts[0])
    return devices


def resolve_serial(explicit: str | None) -> str:
    if explicit:
        return explicit
    devices = list_devices()
    if not devices:
        raise RuntimeError("No adb device attached.")
    if len(devices) > 1:
        raise RuntimeError(
            "Multiple adb devices attached. Pass --serial explicitly. "
            f"Available: {', '.join(devices)}"
        )
    return devices[0]


def human_size(size_kb: int) -> str:
    size = float(size_kb)
    units = ["KB", "MB", "GB", "TB"]
    unit = units[0]
    for unit in units:
        if size < 1024 or unit == units[-1]:
            break
        size /= 1024
    return f"{size:.1f} {unit}"


def shell_quote(path: str) -> str:
    return shlex.quote(path)


def getprop(serial: str, key: str) -> str:
    return adb_shell(serial, f"getprop {key}", check=False).strip()


def parse_df(serial: str, target: str) -> dict[str, str] | None:
    output = adb_shell(serial, f"df -k {shell_quote(target)}", check=False).strip()
    lines = [line for line in output.splitlines() if line.strip()]
    if len(lines) < 2:
        return None
    parts = lines[-1].split()
    if len(parts) < 6:
        return None
    return {
        "mount": target,
        "filesystem": parts[0],
        "total": human_size(int(parts[1])),
        "used": human_size(int(parts[2])),
        "free": human_size(int(parts[3])),
        "used_percent": parts[4],
        "mounted_on": parts[5],
    }


def du_children(serial: str, root: str, limit: int = 20) -> list[dict[str, object]]:
    script = (
        f"for p in {shell_quote(root)}/*; do "
        f"[ -e \"$p\" ] || continue; "
        f"du -sk \"$p\" 2>/dev/null; "
        "done"
    )
    output = adb_shell(serial, script, check=False)
    rows = []
    for line in output.splitlines():
        parts = line.strip().split(maxsplit=1)
        if len(parts) != 2:
            continue
        try:
            size_kb = int(parts[0])
        except ValueError:
            continue
        if size_kb < MIN_SIZE_KB:
            continue
        path = parts[1]
        rows.append(
            {
                "name": PurePosixPath(path).name,
                "path": path,
                "size_kb": size_kb,
                "size_h": human_size(size_kb),
            }
        )
    rows.sort(key=lambda item: int(item["size_kb"]), reverse=True)
    return rows[:limit]


def du_targets(serial: str, targets: list[str], limit: int = 20) -> list[dict[str, object]]:
    rows = []
    for target in targets:
        output = adb_shell(serial, f"du -sk {shell_quote(target)} 2>/dev/null", check=False).strip()
        parts = output.split(maxsplit=1)
        if len(parts) != 2:
            continue
        try:
            size_kb = int(parts[0])
        except ValueError:
            continue
        if size_kb < MIN_SIZE_KB:
            continue
        rows.append(
            {
                "name": PurePosixPath(target).name,
                "path": target,
                "size_kb": size_kb,
                "size_h": human_size(size_kb),
            }
        )
    rows.sort(key=lambda item: int(item["size_kb"]), reverse=True)
    return rows[:limit]


def path_exists(serial: str, path: str) -> bool:
    output = adb_shell(serial, f"[ -e {shell_quote(path)} ] && echo yes || echo no", check=False)
    return output.strip() == "yes"


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Android storage scan via adb.")
    parser.add_argument("--serial", help="adb serial")
    parser.add_argument("--max-entries", type=int, default=15, help="max rows per group")
    args = parser.parse_args()

    started = time.time()
    serial = resolve_serial(args.serial)

    shared_root = "/sdcard"
    media_root = "/sdcard/Android/media"
    obb_root = "/sdcard/Android/obb"

    groups: dict[str, list[dict[str, object]]] = {}
    warnings: list[str] = []

    for name, root in (
        ("shared_root", shared_root),
        ("android_media", media_root),
        ("android_obb", obb_root),
    ):
        if path_exists(serial, root):
            groups[name] = du_children(serial, root, limit=args.max_entries)
        else:
            groups[name] = []
            warnings.append(f"Path not accessible or not present: {root}")

    media_targets = [
        "/sdcard/DCIM",
        "/sdcard/Movies",
        "/sdcard/Pictures",
        "/sdcard/Download",
        "/sdcard/Documents",
        "/sdcard/Music",
        "/sdcard/ScreenRecord",
        "/sdcard/Screenrecorder",
        "/sdcard/tencent",
        "/sdcard/MIUI",
    ]
    groups["shared_hotspots"] = du_targets(serial, media_targets, limit=args.max_entries)

    download_root = "/sdcard/Download"
    if path_exists(serial, download_root):
        groups["download_children"] = du_children(serial, download_root, limit=args.max_entries)
    else:
        groups["download_children"] = []

    volumes = []
    for mount in ("/data", "/sdcard", "/storage/emulated"):
        volume = parse_df(serial, mount)
        if volume:
            volumes.append(volume)
        else:
            warnings.append(f"Could not parse df for {mount}")

    data = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "scan_seconds": round(time.time() - started, 1),
        "system": {
            "serial": serial,
            "model": getprop(serial, "ro.product.model"),
            "brand": getprop(serial, "ro.product.brand"),
            "device": getprop(serial, "ro.product.device"),
            "android_version": getprop(serial, "ro.build.version.release"),
            "sdk": getprop(serial, "ro.build.version.sdk"),
            "fingerprint": getprop(serial, "ro.build.fingerprint"),
            "volumes": volumes,
        },
        "groups": groups,
        "warnings": warnings,
        "notes": [
            "Android 11+ may block direct access to /sdcard/Android/data for adb shell.",
            "App-private /data/data paths are intentionally not scanned.",
            "Android/media and Android/obb may contain user data or redownloadable assets depending on the app.",
        ],
    }

    json.dump(data, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

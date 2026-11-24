#!/usr/bin/env python3
"""Alternador rápido de perfiles visuales para VS Code.

Uso:
    python switch_theme.py tinta
    python switch_theme.py vaporwave
    python switch_theme.py brutalismo
    python switch_theme.py restore
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

EDITORS = {
    "antigravity-ide": "Antigravity IDE",
    "vscode": "Code",
}
DEFAULT_EDITOR = "antigravity-ide"
THEMES_DIR = Path(__file__).resolve().parent / "vscode-themes-test"


def get_available_styles() -> tuple[str, ...]:
    """Detecta automáticamente los perfiles *.json dentro de vscode-themes-test."""
    if not THEMES_DIR.is_dir():
        return ()
    return tuple(sorted(p.stem for p in THEMES_DIR.glob("*.json")))


def get_editor_user_dir(editor: str = DEFAULT_EDITOR) -> Path:
    """Devuelve la carpeta User de configuración del editor según el SO."""
    folder_name = EDITORS[editor]
    system = platform.system()
    if system == "Windows":
        appdata = os.environ.get("APPDATA")
        if not appdata:
            raise RuntimeError("No se encontró la variable de entorno APPDATA.")
        return Path(appdata) / folder_name / "User"
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / folder_name / "User"
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg_config) if xdg_config else Path.home() / ".config"
    return base / folder_name / "User"


def strip_jsonc(text: str) -> str:
    """Elimina comentarios //, /* ... */ y comas finales de un JSONC sin alterar cadenas."""
    out: list[str] = []
    i = 0
    n = len(text)
    in_string = False
    escape = False

    # Paso 1: eliminar comentarios preservando cadenas literales
    while i < n:
        ch = text[i]
        if in_string:
            out.append(ch)
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            i += 1
            continue

        if ch == '"':
            in_string = True
            out.append(ch)
            i += 1
        elif ch == "/" and i + 1 < n and text[i + 1] == "/":
            i += 2
            while i < n and text[i] not in ("\r", "\n"):
                i += 1
        elif ch == "/" and i + 1 < n and text[i + 1] == "*":
            i += 2
            while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2
        else:
            out.append(ch)
            i += 1

    no_comments = "".join(out)

    # Paso 2: eliminar comas finales antes de } o ] fuera de cadenas
    cleaned: list[str] = []
    i = 0
    n = len(no_comments)
    in_string = False
    escape = False

    while i < n:
        ch = no_comments[i]
        if in_string:
            cleaned.append(ch)
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            i += 1
            continue

        if ch == '"':
            in_string = True
            cleaned.append(ch)
            i += 1
        elif ch == ",":
            j = i + 1
            while j < n and no_comments[j] in " \t\r\n":
                j += 1
            if j < n and no_comments[j] in ("}", "]"):
                # Omitir la coma final
                i += 1
            else:
                cleaned.append(ch)
                i += 1
        else:
            cleaned.append(ch)
            i += 1

    return "".join(cleaned)


def load_jsonc(path: Path) -> dict[str, Any]:
    """Carga un archivo JSON/JSONC (con soporte para UTF-8 con o sin BOM)."""
    raw = path.read_text(encoding="utf-8-sig")
    stripped = strip_jsonc(raw).strip()
    if not stripped:
        return {}
    data = json.loads(stripped)
    if not isinstance(data, dict):
        raise ValueError(f"Se esperaba un objeto JSON en {path}")
    return data


def merge_settings(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    """Combina recursivamente diccionarios; el perfil visual sobrescribe claves en conflicto."""
    merged = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merge_settings(merged[key], value)
        else:
            merged[key] = value
    return merged


def write_json_atomic(path: Path, data: dict[str, Any]) -> None:
    """Escribe JSON válido de forma atómica para no corromper settings.json."""
    content = json.dumps(data, indent=4, ensure_ascii=False) + "\n"
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=".settings.", suffix=".tmp")
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(content)
        os.replace(tmp_path, path)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink()
        raise


def apply_style(style: str, user_dir: Path) -> None:
    backup_path = user_dir / "settings.backup.json"
    settings_path = user_dir / "settings.json"
    style_path = THEMES_DIR / f"{style}.json"

    if not backup_path.exists():
        raise FileNotFoundError(
            f"No se encontró el respaldo obligatorio: {backup_path}\n"
            "Crea settings.backup.json antes de aplicar estilos."
        )
    if not style_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo del estilo: {style_path}")

    base_settings = load_jsonc(backup_path)
    style_settings = load_jsonc(style_path)
    merged = merge_settings(base_settings, style_settings)
    write_json_atomic(settings_path, merged)

    print(f"[OK] Estilo '{style}' aplicado correctamente.")
    print(f"     Respaldo base : {backup_path}")
    print(f"     Perfil visual : {style_path}")
    print(f"     Destino       : {settings_path}")
    print(f"     Tema          : {merged.get('workbench.colorTheme')}")
    print(f"     Iconos        : {merged.get('workbench.iconTheme')}")
    print(f"     Fuente        : {merged.get('editor.fontFamily')}")


def restore_backup(user_dir: Path) -> None:
    backup_path = user_dir / "settings.backup.json"
    settings_path = user_dir / "settings.json"

    if not backup_path.exists():
        raise FileNotFoundError(f"No se encontró el respaldo: {backup_path}")

    shutil.copyfile(backup_path, settings_path)
    print("[OK] Configuración original restaurada intacta desde settings.backup.json.")
    print(f"     Origen  : {backup_path}")
    print(f"     Destino : {settings_path}")


def create_backup(user_dir: Path) -> None:
    user_dir.mkdir(parents=True, exist_ok=True)
    backup_path = user_dir / "settings.backup.json"
    settings_path = user_dir / "settings.json"

    if backup_path.exists():
        print(f"[OK] El respaldo ya existe y no se sobrescribió: {backup_path}")
        return

    if settings_path.exists():
        shutil.copyfile(settings_path, backup_path)
        print("[OK] Respaldo creado correctamente desde tu settings.json actual.")
    else:
        backup_path.write_text("{}\n", encoding="utf-8")
        print("[OK] No había settings.json previo; se creó un respaldo base vacío ({}).")
    print(f"     Respaldo: {backup_path}")


def main() -> int:
    styles = get_available_styles()
    parser = argparse.ArgumentParser(
        description="Alterna estilos visuales de Antigravity IDE / VS Code sin perder tu configuración base."
    )
    parser.add_argument(
        "action",
        choices=(*styles, "backup", "restore"),
        help=f"Estilo a aplicar ({', '.join(styles)}), 'backup' para respaldar o 'restore' para restaurar.",
    )
    parser.add_argument(
        "--editor",
        choices=tuple(EDITORS.keys()),
        default=DEFAULT_EDITOR,
        help=f"Editor destino (por defecto: {DEFAULT_EDITOR}).",
    )
    parser.add_argument(
        "--user-dir",
        type=Path,
        default=None,
        help="Ruta opcional a la carpeta User del editor (sobrescribe --editor).",
    )
    args = parser.parse_args()

    try:
        user_dir = args.user_dir if args.user_dir else get_editor_user_dir(args.editor)
        if args.action == "backup":
            create_backup(user_dir)
        elif args.action == "restore":
            restore_backup(user_dir)
        else:
            apply_style(args.action, user_dir)
        return 0
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

# Perfiles Visuales para VS Code / Antigravity IDE

Alterna rápido entre estilos visuales (tema, iconos, fuente y layout) sin perder ni mezclar tu configuración funcional actual.

## Estilos incluidos

| Perfil | Tema | Iconos | Fuente |
| --- | --- | --- | --- |
| `chamba` | GitHub Dark Default | `symbols` | `'Cascadia Code', 'JetBrains Mono', Consolas, monospace` |
| `tinta` | Kanagawa Dragon | `symbols` | `'Iosevka', 'JetBrains Mono', 'Cascadia Code', Consolas, monospace` |
| `vaporwave` | Tokyo Night | `catppuccin-mocha` | `'JetBrains Mono', 'Cascadia Code', Consolas, monospace` |
| `brutalismo` | Vesper | `null` (sin iconos) | `'Maple Mono', 'Fira Code', 'Cascadia Code', Consolas, monospace` |

## Uso en una PC nueva (por ejemplo, en VS Code del trabajo)

### 1. Instalar las extensiones de temas e iconos

**En VS Code:**
```powershell
code --install-extension GitHub.github-vscode-theme
code --install-extension miguelsolorio.symbols
code --install-extension metaphore.kanagawa-vscode-color-theme
code --install-extension enkia.tokyo-night
code --install-extension Catppuccin.catppuccin-vsc-icons
code --install-extension raunofreiberg.vesper
```

**En Antigravity IDE:**
```powershell
antigravity-ide --install-extension GitHub.github-vscode-theme
antigravity-ide --install-extension metaphore.kanagawa-vscode-color-theme
antigravity-ide --install-extension Catppuccin.catppuccin-vsc-icons
antigravity-ide --install-extension raunofreiberg.vesper
```
*(Antigravity IDE ya incluye `miguelsolorio.symbols` y `enkia.tokyo-night` integrados).*

> Si en tu trabajo solo quieres el perfil **`chamba`**, basta con instalar `GitHub.github-vscode-theme` y `miguelsolorio.symbols`.

### 2. Crear tu respaldo local obligatorio

**En VS Code:**
```powershell
python switch_theme.py --editor vscode backup
```

**En Antigravity IDE:**
```powershell
python switch_theme.py backup
```

Esto crea `settings.backup.json` en la carpeta `User` de tu editor sin modificar tu configuración original (y nunca sobrescribe un respaldo existente).

### 3. Alternar estilos o restaurar

**En VS Code:**
```powershell
python switch_theme.py --editor vscode chamba
python switch_theme.py --editor vscode tinta
python switch_theme.py --editor vscode vaporwave
python switch_theme.py --editor vscode brutalismo
python switch_theme.py --editor vscode restore
```

**En Antigravity IDE:**
```powershell
python switch_theme.py chamba
python switch_theme.py tinta
python switch_theme.py vaporwave
python switch_theme.py brutalismo
python switch_theme.py restore
```

## Cómo funciona

- Cada cambio hace un *merge* limpio del JSON del estilo (`vscode-themes-test/*.json`) sobre tu `settings.backup.json` local (con soporte JSONC para comentarios y comas finales) y escribe un `settings.json` válido de forma atómica.
- `restore` devuelve tu `settings.backup.json` intacto byte por byte.
- Tus ajustes locales (`settings.json` y `settings.backup.json`) nunca se guardan ni se suben a este repositorio.

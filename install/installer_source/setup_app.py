"""Небольшой установщик WebHunt__ для Windows: ставит программу текущему пользователю."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
import winreg
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


from webhunt.version import APP_NAME, APP_VERSION, APP_PUBLISHER
PROGRESS_COLOR = "#E3B8FF"
UNINSTALL_KEY = rf"Software\Microsoft\Windows\CurrentVersion\Uninstall\{APP_NAME}"
SHORTCUT_SCRIPT = r"""
param([string]$ShortcutPath, [string]$TargetPath, [string]$IconPath)
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($ShortcutPath)
$shortcut.TargetPath = $TargetPath
$shortcut.WorkingDirectory = Split-Path -Parent $TargetPath
$shortcut.IconLocation = "$IconPath,0"
$shortcut.Save()
"""
UNINSTALL_SCRIPT = r"""
$installDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$startMenu = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\WebHunt__.lnk'
$desktop = Join-Path ([Environment]::GetFolderPath('Desktop')) 'WebHunt__.lnk'
Remove-Item -LiteralPath $startMenu, $desktop -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\WebHunt__' -Recurse -Force -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 700
$appExe = Join-Path $installDir 'WebHunt__.exe'
$icon = Join-Path $installDir 'webhunt_logo.ico'
Remove-Item -LiteralPath $appExe -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $icon -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath (Join-Path $installDir 'shortcut.ps1') -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath (Join-Path $installDir 'uninstall.ps1') -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $installDir -Force -ErrorAction SilentlyContinue
"""


def _powershell(script: str, *arguments: str) -> subprocess.CompletedProcess:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".ps1", delete=False) as file:
        file.write(script)
        script_path = file.name
    try:
        return subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script_path, *arguments],
            check=True,
            capture_output=True,
            text=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    finally:
        try:
            os.remove(script_path)
        except OSError:
            pass


class SetupWindow(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"Установка {APP_NAME}")
        asset_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent)) / "assets"
        try:
            self.iconbitmap(str(asset_root / "webhunt_logo.ico"))
        except tk.TclError:
            pass
        # The path picker and its permission note need room above the footer so
        # the install button never gets clipped on common Windows scaling levels.
        self.geometry("660x500")
        self.resizable(False, False)
        self.configure(bg="#08050F")
        self._installing = False

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#100A1C")
        style.configure("TLabel", background="#100A1C", foreground="#F6EDFF", font=("Segoe UI", 10))
        style.configure("Title.TLabel", background="#08050F", font=("Segoe UI", 22, "bold"), foreground="#FFFFFF")
        style.configure("Muted.TLabel", background="#08050F", foreground="#B7A6C9", font=("Segoe UI", 10))
        style.configure("CardMuted.TLabel", background="#100A1C", foreground="#B7A6C9", font=("Segoe UI", 10))
        style.configure("Card.TFrame", background="#100A1C", relief="flat")
        style.configure("TButton", font=("Segoe UI", 10), padding=(14, 9), borderwidth=0)
        style.configure("Accent.TButton", background="#A020F0", foreground="#FFFFFF", font=("Segoe UI", 10, "bold"))
        style.map("Accent.TButton", background=[("disabled", "#39204D"), ("active", "#C026D3"), ("!disabled", "#A020F0")], foreground=[("disabled", "#B7A6C9"), ("!disabled", "#FFFFFF")])
        style.configure("Soft.TButton", background="#1A1028", foreground="#F6EDFF")
        style.map("Soft.TButton", background=[("active", "#2A183B"), ("!disabled", "#1A1028")], foreground=[("!disabled", "#F6EDFF")])
        style.configure("TEntry", fieldbackground="#1A1028", foreground="#F6EDFF", insertcolor="#F6EDFF", bordercolor="#38234D", padding=9)
        style.map("TEntry", bordercolor=[("focus", "#D946EF")])
        style.configure("TCheckbutton", background="#100A1C", foreground="#F6EDFF", font=("Segoe UI", 10))
        style.map("TCheckbutton", background=[("active", "#100A1C")], foreground=[("disabled", "#756486")])
        style.configure("Neon.Horizontal.TProgressbar", background=PROGRESS_COLOR, troughcolor="#1A1028", bordercolor="#1A1028", lightcolor=PROGRESS_COLOR, darkcolor="#A967C5")

        outer = ttk.Frame(self, padding=22, style="TFrame")
        outer.pack(fill="both", expand=True)
        header = ttk.Frame(outer, style="TFrame")
        header.pack(fill="x", pady=(0, 18))
        self.logo_image = tk.PhotoImage(file=str(asset_root / "webhunt_logo.png")).subsample(6, 6)
        tk.Label(header, image=self.logo_image, bg="#100A1C", width=48, height=48).pack(side="left", padx=(0, 14))
        title_box = ttk.Frame(header, style="TFrame")
        title_box.pack(side="left", fill="y")
        ttk.Label(title_box, text=APP_NAME, style="Title.TLabel").pack(anchor="w")
        ttk.Label(title_box, text=f"{APP_PUBLISHER} · УСТАНОВЩИК · ВЕРСИЯ {APP_VERSION}", style="Muted.TLabel").pack(anchor="w", pady=(2, 0))

        card = ttk.Frame(outer, padding=18, style="Card.TFrame")
        card.pack(fill="x")
        ttk.Label(card, text="Установка WebHunt__", font=("Segoe UI", 14, "bold")).pack(anchor="w")
        ttk.Label(card, text="Программа будет установлена для вашей учётной записи. Права администратора не нужны.", wraplength=520, style="CardMuted.TLabel").pack(anchor="w", pady=(5, 18))
        ttk.Label(card, text="Папка установки", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.target_dir = self._default_target_dir()
        self.target_dir_var = tk.StringVar(value=str(self.target_dir))
        path_row = ttk.Frame(card, style="TFrame")
        path_row.pack(fill="x", pady=(7, 6))
        self.path_entry = ttk.Entry(path_row, textvariable=self.target_dir_var, state="readonly")
        self.path_entry.pack(side="left", fill="x", expand=True)
        self.browse_button = ttk.Button(path_row, text="Выбрать…", style="Soft.TButton", command=self._choose_target_dir)
        self.browse_button.pack(side="left", padx=(8, 0))
        ttk.Label(card, text="Выберите доступную для записи папку. Каталог Program Files может потребовать права администратора.", wraplength=520, style="CardMuted.TLabel").pack(anchor="w", pady=(0, 10))

        self.desktop_shortcut = tk.BooleanVar(value=True)
        ttk.Checkbutton(card, text="Создать ярлык на рабочем столе", variable=self.desktop_shortcut).pack(anchor="w")

        footer = ttk.Frame(outer)
        footer.pack(side="bottom", fill="x", pady=(14, 0))
        self.status = tk.StringVar(value="Будет создан ярлык в меню «Пуск».")
        status_box = ttk.Frame(footer, style="TFrame")
        status_box.pack(side="left", fill="x", expand=True)
        ttk.Label(status_box, textvariable=self.status, style="CardMuted.TLabel").pack(anchor="w")
        self.install_progress = ttk.Progressbar(status_box, mode="indeterminate", length=230, style="Neon.Horizontal.TProgressbar")
        self.install_button = ttk.Button(footer, text="Установить", style="Accent.TButton", command=self._install)
        self.install_button.pack(side="right", padx=(14, 0))

    @staticmethod
    def _default_target_dir() -> Path:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, UNINSTALL_KEY) as key:
                existing, _kind = winreg.QueryValueEx(key, "InstallLocation")
                if existing:
                    return Path(existing)
        except (FileNotFoundError, OSError):
            pass
        return Path(os.environ.get("LOCALAPPDATA", Path.home())) / "Programs" / APP_NAME

    def _choose_target_dir(self) -> None:
        selected = filedialog.askdirectory(
            title="Выберите папку для установки WebHunt__",
            initialdir=self.target_dir_var.get() or str(Path.home()),
            mustexist=False,
            parent=self,
        )
        if selected:
            self.target_dir_var.set(str(Path(selected).expanduser()))

    def _install(self) -> None:
        if self._installing:
            return
        target_text = self.target_dir_var.get().strip()
        if not target_text:
            messagebox.showwarning("Нужна папка", "Выберите папку для установки WebHunt__.", parent=self)
            return
        target_dir = Path(target_text).expanduser()
        try:
            target_dir = target_dir.resolve()
        except OSError as exc:
            messagebox.showerror("Папка недоступна", str(exc), parent=self)
            return
        if target_dir.exists() and not target_dir.is_dir():
            messagebox.showwarning("Неверная папка", "Выберите папку, а не файл.", parent=self)
            return
        source_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent)) / "payload"
        source_exe = source_dir / f"{APP_NAME}.exe"
        source_icon = source_dir / "webhunt_logo.ico"
        if not source_exe.is_file():
            messagebox.showerror("Нет файла программы", f"Не найден файл:\n{source_exe}", parent=self)
            return

        self._installing = True
        self.status.set("Устанавливаю WebHunt__…")
        self.install_progress.pack(fill="x", pady=(8, 0))
        self.install_progress.start(12)
        self.install_button.configure(state="disabled")
        threading.Thread(
            target=self._install_worker,
            args=(target_dir, source_exe, source_icon, bool(self.desktop_shortcut.get())),
            daemon=True,
        ).start()

    def _install_worker(self, target_dir: Path, source_exe: Path, source_icon: Path, create_desktop: bool) -> None:
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            target_exe = target_dir / f"{APP_NAME}.exe"
            shutil.copy2(source_exe, target_exe)
            target_icon = target_dir / "webhunt_logo.ico"
            if source_icon.is_file():
                shutil.copy2(source_icon, target_icon)

            uninstall_path = target_dir / "uninstall.ps1"
            uninstall_path.write_text(UNINSTALL_SCRIPT, encoding="utf-8")
            shortcut_script = target_dir / "shortcut.ps1"
            shortcut_script.write_text(SHORTCUT_SCRIPT, encoding="utf-8")
            start_menu_dir = Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
            start_menu_dir.mkdir(parents=True, exist_ok=True)
            _powershell(str(shortcut_script.read_text(encoding="utf-8")), str(start_menu_dir / f"{APP_NAME}.lnk"), str(target_exe), str(target_icon))
            if create_desktop:
                desktop = Path(subprocess.check_output(
                    ["powershell.exe", "-NoProfile", "-Command", "[Environment]::GetFolderPath('Desktop')"],
                    text=True,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                ).strip())
                _powershell(str(shortcut_script.read_text(encoding="utf-8")), str(desktop / f"{APP_NAME}.lnk"), str(target_exe), str(target_icon))
            shortcut_script.unlink(missing_ok=True)

            uninstall_command = f'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "{uninstall_path}"'
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, UNINSTALL_KEY) as key:
                winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, f"{APP_NAME} · {APP_PUBLISHER}")
                winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, APP_VERSION)
                winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, APP_PUBLISHER)
                winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, str(target_dir))
                winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, str(target_exe))
                winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, uninstall_command)
        except Exception as exc:  # noqa: BLE001
            message = str(exc) or exc.__class__.__name__
            self.after(0, lambda message=message: self._install_complete(message, None))
            return
        self.after(0, lambda target_exe=target_exe: self._install_complete(None, target_exe))

    def _install_complete(self, error: str | None, target_exe: Path | None) -> None:
        self._installing = False
        self.install_progress.stop()
        self.install_progress.pack_forget()
        self.install_button.configure(state="normal")
        if error:
            self.status.set("Установка не завершена")
            messagebox.showerror(
                "Не удалось установить",
                f"{error}\n\nЕсли WebHunt__ уже запущен, закройте его и повторите установку.",
                parent=self,
            )
            return

        self.status.set("WebHunt__ установлен.")
        if target_exe and messagebox.askyesno("Установка завершена", "WebHunt__ установлен. Запустить его сейчас?", parent=self):
            os.startfile(target_exe)
        self.destroy()


if __name__ == "__main__":
    SetupWindow().mainloop()




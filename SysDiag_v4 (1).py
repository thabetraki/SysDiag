# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║       SysDiag v4.0 - Diagnostic + IA (Claude & Gemini) + Terminal CMD       ║
║                                                                              ║
║  Copyright (C) 2026  Thabet Raki                                             ║
║  Licence : GNU General Public License v3 (GPLv3)                            ║
║  https://www.gnu.org/licenses/gpl-3.0.html                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, font as tkfont
import subprocess
import platform
import os
import sys
import threading
import datetime
import json
import socket
import time
import ctypes
import queue
import math

try:
    import psutil
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
    import psutil

try:
    import requests
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

# ─── Palette moderne glassmorphism ───────────────────────────────────────────
BG_BASE      = "#060810"
BG_SURFACE   = "#0D1117"
BG_CARD      = "#111827"
BG_GLASS     = "#161D2E"
BG_TERMINAL  = "#080C0A"
BG_INPUT     = "#0F1523"

ACCENT_BLUE  = "#4F8EF7"
ACCENT_CYAN  = "#22D3EE"
ACCENT_GREEN = "#10B981"
ACCENT_RED   = "#F43F5E"
ACCENT_WARN  = "#F59E0B"
ACCENT_AI    = "#A855F7"
ACCENT_GEM   = "#1A73E8"   # Google Gemini blue

TEXT_MAIN    = "#E2E8F0"
TEXT_SUB     = "#64748B"
TEXT_DIM     = "#334155"
BORDER       = "#1E293B"
BORDER_GLOW  = "#2D3F5A"

CMD_GREEN    = "#00FF87"
CMD_RED      = "#FF4560"
CMD_YELLOW   = "#FFD700"
CMD_WHITE    = "#CBD5E1"
CMD_CYAN     = "#67E8F9"

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
GEMINI_API_URL    = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# ══════════════════════════════════════════════════════════════════════════════
#  VÉRIFICATION ADMIN
# ══════════════════════════════════════════════════════════════════════════════
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def run_as_admin():
    try:
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, f'"{os.path.abspath(__file__)}"', None, 1
        )
    except Exception:
        pass

# ══════════════════════════════════════════════════════════════════════════════
#  BIBLIOTHÈQUE DE COMMANDES DE RÉPARATION
# ══════════════════════════════════════════════════════════════════════════════
REPAIR_COMMANDS = {
    "windows_update": {
        "label": "Rechercher les mises à jour Windows",
        "cmds": [
            'powershell -Command "Install-Module PSWindowsUpdate -Force -Scope CurrentUser -ErrorAction SilentlyContinue"',
            'powershell -Command "Get-WindowsUpdate -AcceptAll -Install -AutoReboot:$false"',
        ],
        "category": "Mises à jour", "icon": "🔄",
    },
    "windows_update_reset": {
        "label": "Réinitialiser Windows Update",
        "cmds": [
            "net stop wuauserv", "net stop cryptSvc", "net stop bits", "net stop msiserver",
            'rd /s /q "%systemroot%\\SoftwareDistribution"',
            'rd /s /q "%systemroot%\\system32\\catroot2"',
            "net start wuauserv", "net start cryptSvc", "net start bits", "net start msiserver",
        ],
        "category": "Mises à jour", "icon": "🔄",
    },
    "drivers_scan": {
        "label": "Scanner les pilotes manquants / obsolètes",
        "cmds": [
            'powershell -Command "Get-WmiObject Win32_PnPSignedDriver | Where-Object {$_.IsSigned -eq $false} | Select-Object DeviceName,DriverVersion | Format-Table -AutoSize"',
            'pnputil /enum-drivers',
        ],
        "category": "Pilotes", "icon": "🔌",
    },
    "drivers_gpu_update": {
        "label": "Mettre à jour le pilote GPU via winget",
        "cmds": ["winget upgrade --all --include-unknown --accept-source-agreements --accept-package-agreements"],
        "category": "Pilotes", "icon": "🖥️",
    },
    "sfc_scan": {
        "label": "Réparer les fichiers système (SFC)",
        "cmds": ["sfc /scannow"],
        "category": "Système", "icon": "🛡️",
    },
    "dism_repair": {
        "label": "Réparer l'image Windows (DISM)",
        "cmds": [
            "DISM /Online /Cleanup-Image /CheckHealth",
            "DISM /Online /Cleanup-Image /ScanHealth",
            "DISM /Online /Cleanup-Image /RestoreHealth",
        ],
        "category": "Système", "icon": "🛠️",
    },
    "chkdsk": {
        "label": "Vérifier le disque C: (CHKDSK)",
        "cmds": ["chkdsk C: /f /r /x"],
        "category": "Disques", "icon": "💿",
    },
    "disk_cleanup": {
        "label": "Nettoyer les fichiers temporaires",
        "cmds": [
            'del /s /q "%temp%\\*"',
            'del /s /q "C:\\Windows\\Temp\\*"',
            "cleanmgr /sagerun:1",
        ],
        "category": "Disques", "icon": "🗑️",
    },
    "network_reset": {
        "label": "Réinitialiser le réseau complet",
        "cmds": [
            "netsh winsock reset", "netsh int ip reset",
            "ipconfig /release", "ipconfig /flushdns", "ipconfig /renew",
        ],
        "category": "Réseau", "icon": "🌐",
    },
    "dns_flush": {
        "label": "Vider le cache DNS",
        "cmds": ["ipconfig /flushdns"],
        "category": "Réseau", "icon": "🔃",
    },
    "network_drivers": {
        "label": "Réinstaller les pilotes réseau",
        "cmds": [
            'powershell -Command "Get-NetAdapter | Disable-NetAdapter -Confirm:$false"',
            'powershell -Command "Get-NetAdapter | Enable-NetAdapter -Confirm:$false"',
        ],
        "category": "Réseau", "icon": "📶",
    },
    "ram_optimize": {
        "label": "Optimiser la mémoire RAM",
        "cmds": [
            'powershell -Command "Get-Process | Where-Object {$_.WorkingSet -gt 500MB} | Select-Object Name,@{N=\'RAM(MB)\';E={[math]::Round($_.WorkingSet/1MB,1)}} | Sort-Object \'RAM(MB)\' -Descending | Format-Table"',
            'powershell -Command "[System.GC]::Collect()"',
        ],
        "category": "RAM", "icon": "🧠",
    },
    "pagefile_optimize": {
        "label": "Optimiser le fichier d'échange",
        "cmds": ['powershell -Command "$cs = Get-WmiObject Win32_ComputerSystem; $cs.AutomaticManagedPagefile = $true; $cs.Put()"'],
        "category": "RAM", "icon": "📄",
    },
    "cpu_performance": {
        "label": "Activer le mode Haute Performance CPU",
        "cmds": ["powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"],
        "category": "CPU", "icon": "⚡",
    },
    "startup_clean": {
        "label": "Lister et désactiver les apps au démarrage",
        "cmds": ['powershell -Command "Get-CimInstance Win32_StartupCommand | Select-Object Name,Command,Location | Format-Table -AutoSize"'],
        "category": "CPU", "icon": "🚀",
    },
    "defender_scan": {
        "label": "Scan antivirus Windows Defender",
        "cmds": ['powershell -Command "Start-MpScan -ScanType QuickScan"'],
        "category": "Sécurité", "icon": "🦠",
    },
    "defender_update": {
        "label": "Mettre à jour les définitions Defender",
        "cmds": ['powershell -Command "Update-MpSignature"'],
        "category": "Sécurité", "icon": "🔒",
    },
    "winget_upgrade_all": {
        "label": "Mettre à jour toutes les applications (winget)",
        "cmds": ["winget upgrade --all --accept-source-agreements --accept-package-agreements"],
        "category": "Applications", "icon": "📦",
    },
    "winget_list": {
        "label": "Lister les applications installées",
        "cmds": ["winget list"],
        "category": "Applications", "icon": "📋",
    },
}

# ══════════════════════════════════════════════════════════════════════════════
#  MOTEUR DE DIAGNOSTIC
# ══════════════════════════════════════════════════════════════════════════════
class DiagnosticEngine:
    def get_system_info(self):
        info = {
            "OS"           : f"{platform.system()} {platform.release()} ({platform.version()})",
            "Architecture" : platform.machine(),
            "Processeur"   : platform.processor() or "N/A",
            "Nom Machine"  : platform.node(),
            "Python"       : platform.python_version(),
            "Admin"        : "Oui ✔" if is_admin() else "Non (certaines réparations limitées)",
        }
        try:
            info["RAM Totale"] = f"{psutil.virtual_memory().total / (1024**3):.2f} Go"
        except Exception:
            pass
        return info

    def check_cpu(self):
        issues = []
        try:
            cpu_pct = psutil.cpu_percent(interval=1)
            freq    = psutil.cpu_freq()
            cores   = psutil.cpu_count(logical=False)
            threads = psutil.cpu_count(logical=True)
            if cpu_pct > 90:
                issues.append({"composant": "CPU", "severite": "CRITIQUE",
                    "probleme": f"CPU à {cpu_pct:.1f}%",
                    "repair_keys": ["startup_clean", "cpu_performance", "defender_scan"]})
            elif cpu_pct > 70:
                issues.append({"composant": "CPU", "severite": "AVERTISSEMENT",
                    "probleme": f"CPU élevé : {cpu_pct:.1f}%",
                    "repair_keys": ["startup_clean", "cpu_performance"]})
            if freq and freq.current < freq.max * 0.5:
                issues.append({"composant": "CPU", "severite": "AVERTISSEMENT",
                    "probleme": f"Throttling CPU ({freq.current:.0f}/{freq.max:.0f} MHz)",
                    "repair_keys": ["cpu_performance", "drivers_gpu_update"]})
            return {"Utilisation": f"{cpu_pct:.1f}%",
                    "Fréquence": f"{freq.current:.0f} MHz" if freq else "N/A",
                    "Cœurs": str(cores), "Threads": str(threads)}, issues
        except Exception as e:
            return {"Erreur": str(e)}, []

    def check_ram(self):
        issues = []
        try:
            vm = psutil.virtual_memory()
            swap = psutil.swap_memory()
            pct = vm.percent
            if pct > 90:
                issues.append({"composant": "RAM", "severite": "CRITIQUE",
                    "probleme": f"RAM saturée : {pct:.1f}%",
                    "repair_keys": ["ram_optimize", "pagefile_optimize"]})
            elif pct > 75:
                issues.append({"composant": "RAM", "severite": "AVERTISSEMENT",
                    "probleme": f"RAM élevée : {pct:.1f}%",
                    "repair_keys": ["ram_optimize"]})
            if swap.percent > 50:
                issues.append({"composant": "SWAP", "severite": "AVERTISSEMENT",
                    "probleme": f"Swap élevé : {swap.percent:.1f}%",
                    "repair_keys": ["pagefile_optimize"]})
            return {"Total": f"{vm.total/(1024**3):.2f} Go",
                    "Utilisé": f"{vm.used/(1024**3):.2f} Go ({pct:.1f}%)",
                    "Disponible": f"{vm.available/(1024**3):.2f} Go",
                    "Swap": f"{swap.percent:.1f}%"}, issues
        except Exception as e:
            return {"Erreur": str(e)}, []

    def check_disks(self):
        issues = []
        disk_info = {}
        try:
            for part in psutil.disk_partitions(all=False):
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    pct = usage.percent
                    disk_info[f"Disque {part.device}"] = \
                        f"{usage.used/(1024**3):.1f}/{usage.total/(1024**3):.1f} Go ({pct:.1f}%)"
                    if pct > 95:
                        issues.append({"composant": f"Disque {part.device}",
                            "severite": "CRITIQUE",
                            "probleme": f"Disque plein : {pct:.1f}% ({usage.free/(1024**3):.1f} Go libres)",
                            "repair_keys": ["disk_cleanup", "chkdsk"]})
                    elif pct > 85:
                        issues.append({"composant": f"Disque {part.device}",
                            "severite": "AVERTISSEMENT",
                            "probleme": f"Disque presque plein : {pct:.1f}%",
                            "repair_keys": ["disk_cleanup"]})
                except PermissionError:
                    pass
            io1 = psutil.disk_io_counters()
            time.sleep(0.3)
            io2 = psutil.disk_io_counters()
            if io1 and io2:
                disk_info["I/O Lecture"]  = f"{(io2.read_bytes-io1.read_bytes)/(1024**2)/0.3:.1f} Mo/s"
                disk_info["I/O Écriture"] = f"{(io2.write_bytes-io1.write_bytes)/(1024**2)/0.3:.1f} Mo/s"
        except Exception as e:
            disk_info["Erreur"] = str(e)
        return disk_info, issues

    def check_network(self):
        issues = []
        net_info = {}
        try:
            try:
                socket.setdefaulttimeout(3)
                socket.create_connection(("8.8.8.8", 53))
                net_info["Connexion Internet"] = "✔ Connecté"
            except OSError:
                net_info["Connexion Internet"] = "✘ Déconnecté"
                issues.append({"composant": "Réseau", "severite": "CRITIQUE",
                    "probleme": "Pas de connexion internet",
                    "repair_keys": ["network_reset", "dns_flush", "network_drivers"]})
            io = psutil.net_io_counters()
            net_info["Reçus"]   = f"{io.bytes_recv/(1024**2):.1f} Mo"
            net_info["Envoyés"] = f"{io.bytes_sent/(1024**2):.1f} Mo"
            net_info["Err RX"]  = str(io.errin)
            net_info["Err TX"]  = str(io.errout)
            if io.errin > 1000 or io.errout > 1000:
                issues.append({"composant": "Réseau", "severite": "AVERTISSEMENT",
                    "probleme": f"Erreurs réseau (RX:{io.errin} TX:{io.errout})",
                    "repair_keys": ["network_reset", "network_drivers"]})
        except Exception as e:
            net_info["Erreur"] = str(e)
        return net_info, issues

    def check_windows_update(self):
        issues = []
        info = {}
        if platform.system() != "Windows":
            return {"Info": "Windows uniquement"}, []
        try:
            result = subprocess.run(
                ["powershell", "-Command",
                 "(New-Object -ComObject Microsoft.Update.Session).CreateUpdateSearcher().Search('IsInstalled=0').Updates.Count"],
                capture_output=True, text=True, timeout=20
            )
            count = result.stdout.strip()
            if count.isdigit() and int(count) > 0:
                info["Mises à jour disponibles"] = f"{count} mise(s) à jour en attente"
                issues.append({"composant": "Windows Update", "severite": "AVERTISSEMENT",
                    "probleme": f"{count} mise(s) à jour Windows disponible(s)",
                    "repair_keys": ["windows_update", "windows_update_reset"]})
            else:
                info["Mises à jour"] = "Système à jour ✔"
        except Exception:
            info["Mises à jour"] = "Vérification impossible (droits insuffisants)"
        return info, issues

    def run_full_diagnostic(self, progress_callback=None):
        all_issues, all_sections = [], {}
        steps = [
            ("Système",       self.get_system_info),
            ("CPU",           self.check_cpu),
            ("RAM",           self.check_ram),
            ("Disques",       self.check_disks),
            ("Réseau",        self.check_network),
            ("Windows Update",self.check_windows_update),
        ]
        for i, (name, func) in enumerate(steps):
            if progress_callback:
                progress_callback(int(i / len(steps) * 100), f"Analyse : {name}…")
            result = func()
            if isinstance(result, tuple):
                info, issues = result
                all_issues.extend(issues)
            else:
                info = result
            all_sections[name] = info
        if progress_callback:
            progress_callback(100, "Analyse terminée ✔")
        return all_sections, all_issues


# ══════════════════════════════════════════════════════════════════════════════
#  TERMINAL CMD INTÉGRÉ
# ══════════════════════════════════════════════════════════════════════════════
class CMDTerminal:
    def __init__(self, output_widget, status_callback=None):
        self.output  = output_widget
        self.status  = status_callback
        self.running = False
        self.queue   = queue.Queue()
        self._configure_tags()

    def _configure_tags(self):
        w = self.output
        w.tag_config("prompt",  foreground=CMD_GREEN,  font=("Cascadia Code", 10, "bold"))
        w.tag_config("cmd",     foreground=CMD_CYAN,   font=("Cascadia Code", 10, "bold"))
        w.tag_config("stdout",  foreground=CMD_WHITE,  font=("Cascadia Code", 10))
        w.tag_config("stderr",  foreground=CMD_RED,    font=("Cascadia Code", 10))
        w.tag_config("success", foreground=CMD_GREEN,  font=("Cascadia Code", 10, "bold"))
        w.tag_config("warning", foreground=CMD_YELLOW, font=("Cascadia Code", 10))
        w.tag_config("info",    foreground=CMD_CYAN,   font=("Cascadia Code", 10))
        w.tag_config("ai",      foreground="#C084FC",  font=("Cascadia Code", 10, "italic"))
        w.tag_config("sep",     foreground="#1E293B",  font=("Cascadia Code", 10))

    def write(self, text, tag="stdout"):
        self.output.config(state="normal")
        self.output.insert(tk.END, text, tag)
        self.output.see(tk.END)
        self.output.config(state="disabled")
        self.output.update_idletasks()

    def clear(self):
        self.output.config(state="normal")
        self.output.delete("1.0", tk.END)
        self.output.config(state="disabled")

    def run_command(self, cmd, label=""):
        self.running = True
        if self.status:
            self.status(f"⚡ {label or cmd[:50]}…", ACCENT_WARN)
        self.write(f"\n{'─'*65}\n", "sep")
        self.write(f"  PS> ", "prompt")
        self.write(f"{cmd}\n", "cmd")
        self.write(f"{'─'*65}\n", "sep")

        def _exec():
            try:
                proc = subprocess.Popen(
                    cmd, shell=True,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True, encoding="utf-8", errors="replace",
                    creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
                )
                for line in proc.stdout:
                    self.output.after(0, self.write, line, "stdout")
                err = proc.stderr.read()
                if err.strip():
                    self.output.after(0, self.write, err, "stderr")
                proc.wait()
                rc = proc.returncode
                if rc == 0:
                    self.output.after(0, self.write, f"\n  ✔ Succès (code {rc})\n", "success")
                else:
                    self.output.after(0, self.write, f"\n  ⚠ Code de retour : {rc}\n", "warning")
            except Exception as ex:
                self.output.after(0, self.write, f"\n  ✘ Erreur : {ex}\n", "stderr")
            finally:
                self.running = False
                if self.status:
                    self.output.after(0, self.status, "Prêt", ACCENT_GREEN)

        threading.Thread(target=_exec, daemon=True).start()

    def run_repair(self, repair_key):
        if repair_key not in REPAIR_COMMANDS:
            return
        r = REPAIR_COMMANDS[repair_key]
        self.write(f"\n{'═'*65}\n", "sep")
        self.write(f"  {r['icon']}  {r['label'].upper()}\n", "info")
        self.write(f"{'═'*65}\n", "sep")

        def _run_all():
            for cmd in r["cmds"]:
                self.running = True
                proc = subprocess.Popen(
                    cmd, shell=True,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True, encoding="utf-8", errors="replace",
                    creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
                )
                self.output.after(0, self.write, f"\n  PS> ", "prompt")
                self.output.after(0, self.write, f"{cmd}\n", "cmd")
                for line in proc.stdout:
                    self.output.after(0, self.write, line, "stdout")
                err = proc.stderr.read()
                if err.strip():
                    self.output.after(0, self.write, err, "stderr")
                proc.wait()
                rc = proc.returncode
                msg = f"  ✔ OK (code {rc})\n" if rc == 0 else f"  ⚠ Code : {rc}\n"
                tag = "success" if rc == 0 else "warning"
                self.output.after(0, self.write, msg, tag)
                time.sleep(0.3)
            self.running = False
            self.output.after(0, self.write, f"\n  ✅ '{r['label']}' terminé.\n", "success")
            if self.status:
                self.output.after(0, self.status, "Prêt", ACCENT_GREEN)

        threading.Thread(target=_run_all, daemon=True).start()


# ══════════════════════════════════════════════════════════════════════════════
#  ASSISTANT IA MULTI-MOTEUR (Claude + Gemini)
# ══════════════════════════════════════════════════════════════════════════════
class AIAssistant:
    SYSTEM_PROMPT = """Tu es SysDiag-AI, expert Windows intégré dans un outil de diagnostic.
Rôle : analyser les problèmes PC et proposer des commandes CMD/PowerShell concrètes.

Règles :
- Réponds TOUJOURS en français
- Fournis des commandes CMD/PowerShell précises et exécutables
- Classe par priorité (CRITIQUE > AVERTISSEMENT > INFO)
- Sois concis mais complet
- Encadre les commandes dans ```cmd ... ```
- N'utilise jamais de commandes dangereuses sans avertissement
"""

    def __init__(self, terminal: CMDTerminal):
        self.terminal     = terminal
        self.anthropic_key = ""
        self.gemini_key    = ""
        self.active_engine = "local"   # "claude", "gemini", "local"
        self.history       = []

    def set_keys(self, anthropic_key="", gemini_key=""):
        if anthropic_key: self.anthropic_key = anthropic_key.strip()
        if gemini_key:    self.gemini_key    = gemini_key.strip()
        if self.anthropic_key:
            self.active_engine = "claude"
        elif self.gemini_key:
            self.active_engine = "gemini"
        else:
            self.active_engine = "local"

    def set_engine(self, engine: str):
        self.active_engine = engine

    def _build_context(self, issues, sections):
        lines = ["=== ÉTAT DU SYSTÈME ==="]
        for k, v in sections.get("Système", {}).items():
            lines.append(f"{k}: {v}")
        lines.append("\n=== PROBLÈMES DÉTECTÉS ===")
        if issues:
            for iss in issues:
                lines.append(f"[{iss['severite']}] {iss['composant']}: {iss['probleme']}")
        else:
            lines.append("Aucun problème détecté.")
        return "\n".join(lines)

    def ask(self, user_message: str, issues=None, sections=None, callback=None):
        context  = self._build_context(issues or [], sections or {})
        full_msg = f"{context}\n\n=== QUESTION ===\n{user_message}"
        self.history.append({"role": "user", "content": full_msg})

        engine = self.active_engine
        if engine == "claude" and self.anthropic_key:
            threading.Thread(target=self._call_claude, args=(callback,), daemon=True).start()
        elif engine == "gemini" and self.gemini_key:
            threading.Thread(target=self._call_gemini, args=(callback,), daemon=True).start()
        else:
            threading.Thread(target=self._local_response, args=(user_message, issues or [], callback), daemon=True).start()

    # ── Claude (Anthropic) ────────────────────────────────────────────────
    def _call_claude(self, callback):
        try:
            payload = {
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 1024,
                "system": self.SYSTEM_PROMPT,
                "messages": self.history[-10:],
            }
            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.anthropic_key,
                "anthropic-version": "2023-06-01",
            }
            resp = requests.post(ANTHROPIC_API_URL, json=payload, headers=headers, timeout=30)
            if resp.status_code == 200:
                text = resp.json()["content"][0]["text"]
                self.history.append({"role": "assistant", "content": text})
                if callback: callback(text, "claude")
            else:
                err = f"Erreur API Claude ({resp.status_code}): {resp.text[:200]}"
                if callback: callback(f"[Erreur] {err}", "error")
        except Exception as e:
            if callback: callback(f"[Claude indisponible] {e}\n→ Passage en mode local.", "error")
            self._local_response("", [], callback)

    # ── Gemini (Google) ───────────────────────────────────────────────────
    def _call_gemini(self, callback):
        try:
            # Construire la conversation pour Gemini
            gemini_msgs = []
            # System instruction via first user turn
            sys_text = self.SYSTEM_PROMPT + "\n\nRéponds toujours en français."
            for msg in self.history[-10:]:
                role = "user" if msg["role"] == "user" else "model"
                gemini_msgs.append({"role": role, "parts": [{"text": msg["content"]}]})

            payload = {
                "system_instruction": {"parts": [{"text": sys_text}]},
                "contents": gemini_msgs,
                "generationConfig": {
                    "maxOutputTokens": 1024,
                    "temperature": 0.7,
                }
            }
            url = f"{GEMINI_API_URL}?key={self.gemini_key}"
            resp = requests.post(url, json=payload, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                self.history.append({"role": "assistant", "content": text})
                if callback: callback(text, "gemini")
            else:
                err = f"Erreur API Gemini ({resp.status_code}): {resp.text[:200]}"
                if callback: callback(f"[Erreur Gemini] {err}", "error")
        except Exception as e:
            if callback: callback(f"[Gemini indisponible] {e}\n→ Passage en mode local.", "error")
            self._local_response("", [], callback)

    # ── Mode local (sans API) ─────────────────────────────────────────────
    def _local_response(self, message, issues, callback):
        time.sleep(0.4)
        msg_lower = message.lower()
        lines = ["**SysDiag-AI (mode local)**\n\n"]
        if any(w in msg_lower for w in ["mise à jour", "update"]):
            lines += ["Pour mettre à jour Windows et les apps :\n",
                      "```cmd\nwinget upgrade --all --accept-source-agreements\n```\n",
                      "```cmd\npowershell -Command \"Get-WindowsUpdate -AcceptAll -Install\"\n```\n"]
        elif any(w in msg_lower for w in ["réseau", "internet", "connexion"]):
            lines += ["Pour réparer la connexion réseau :\n",
                      "```cmd\nnetsh winsock reset\nnetsh int ip reset\nipconfig /flushdns\nipconfig /renew\n```\n",
                      "Redémarrez après l'exécution.\n"]
        elif any(w in msg_lower for w in ["lent", "performance", "rapide"]):
            lines += ["Pour améliorer les performances :\n",
                      "```cmd\npowercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c\n```\n",
                      "```cmd\ndel /s /q \"%temp%\\*\"\n```\n",
                      "```cmd\nsfc /scannow\n```\n"]
        elif any(w in msg_lower for w in ["virus", "malware", "sécurité"]):
            lines += ["Pour sécuriser le système :\n",
                      "```cmd\npowershell -Command \"Update-MpSignature\"\n```\n",
                      "```cmd\npowershell -Command \"Start-MpScan -ScanType FullScan\"\n```\n"]
        elif issues:
            lines.append("Actions recommandées pour les problèmes détectés :\n\n")
            for iss in issues[:4]:
                keys = iss.get("repair_keys", [])
                lines.append(f"**{iss['severite']} — {iss['composant']}** : {iss['probleme']}\n")
                for k in keys[:2]:
                    r = REPAIR_COMMANDS.get(k, {})
                    if r:
                        lines.append(f"  → {r['icon']} {r['label']}\n")
                        if r["cmds"]:
                            lines.append(f"```cmd\n{r['cmds'][0]}\n```\n")
                lines.append("\n")
        else:
            lines += ["Système en bonne santé. Bonnes pratiques :\n\n",
                      "• `sfc /scannow` — vérification fichiers système\n",
                      "• `winget upgrade --all` — mises à jour\n",
                      "• Vider `%temp%` chaque semaine\n",
                      "• Activer Windows Defender\n"]
        lines.append("\n*Ajoutez une clé API dans Paramètres IA pour Claude ou Gemini.*")
        if callback: callback("".join(lines), "local")


# ══════════════════════════════════════════════════════════════════════════════
#  WIDGETS PERSONNALISÉS
# ══════════════════════════════════════════════════════════════════════════════
class ModernButton(tk.Canvas):
    """Bouton moderne avec gradient et hover effect."""
    def __init__(self, parent, text, command=None, color=ACCENT_BLUE,
                 text_color=BG_BASE, width=160, height=36, font_size=9, **kwargs):
        super().__init__(parent, width=width, height=height,
                         bg=parent.cget("bg"), highlightthickness=0, **kwargs)
        self.text     = text
        self.command  = command
        self.color    = color
        self.tc       = text_color
        self.w        = width
        self.h        = height
        self.fs       = font_size
        self.hovered  = False
        self._draw()
        self.bind("<Enter>",    self._on_enter)
        self.bind("<Leave>",    self._on_leave)
        self.bind("<Button-1>", self._on_click)

    def _draw(self, hover=False):
        self.delete("all")
        r = 8
        col = self._lighten(self.color, 20) if hover else self.color
        # Rounded rect
        self.create_arc(0, 0, r*2, r*2, start=90, extent=90, fill=col, outline="")
        self.create_arc(self.w-r*2, 0, self.w, r*2, start=0, extent=90, fill=col, outline="")
        self.create_arc(0, self.h-r*2, r*2, self.h, start=180, extent=90, fill=col, outline="")
        self.create_arc(self.w-r*2, self.h-r*2, self.w, self.h, start=270, extent=90, fill=col, outline="")
        self.create_rectangle(r, 0, self.w-r, self.h, fill=col, outline="")
        self.create_rectangle(0, r, self.w, self.h-r, fill=col, outline="")
        self.create_text(self.w//2, self.h//2, text=self.text,
                         fill=self.tc, font=("Segoe UI", self.fs, "bold"))

    def _lighten(self, hex_color, amount):
        hex_color = hex_color.lstrip("#")
        rgb = tuple(min(255, int(hex_color[i:i+2], 16) + amount) for i in (0, 2, 4))
        return f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"

    def _on_enter(self, e): self._draw(hover=True); self.config(cursor="hand2")
    def _on_leave(self, e): self._draw(hover=False)
    def _on_click(self, e):
        if self.command: self.command()


class GlassFrame(tk.Frame):
    """Frame avec apparence glassmorphism simulée."""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG_GLASS,
                         highlightbackground=BORDER_GLOW,
                         highlightthickness=1, **kwargs)


class StatusBadge(tk.Label):
    """Badge de statut coloré."""
    def __init__(self, parent, text, color=ACCENT_GREEN, **kwargs):
        super().__init__(parent, text=f"  {text}  ",
                         font=("Segoe UI", 8, "bold"),
                         fg=color, bg=BG_GLASS,
                         relief="flat", padx=4, pady=2, **kwargs)


# ══════════════════════════════════════════════════════════════════════════════
#  APPLICATION PRINCIPALE
# ══════════════════════════════════════════════════════════════════════════════
class SysDiagApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.engine    = DiagnosticEngine()
        self._sections = {}
        self._issues   = []
        self._pulse    = 0
        self._setup_window()
        self._build_ui()
        self._check_admin_warning()
        self._start_pulse()

    def _setup_window(self):
        self.title("SysDiag v4.0  ·  IA (Claude + Gemini)  ·  Thabet Raki")
        self.geometry("1400x860")
        self.minsize(1150, 720)
        self.configure(bg=BG_BASE)
        # Tenter DPI-awareness sur Windows
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

    def _check_admin_warning(self):
        if platform.system() == "Windows" and not is_admin():
            self._set_status("⚠  Lancez en administrateur pour toutes les réparations", ACCENT_WARN)

    def _start_pulse(self):
        """Animation de pulsation sur l'indicateur de statut."""
        self._pulse = (self._pulse + 1) % 60
        alpha = int(128 + 127 * math.sin(self._pulse * math.pi / 30))
        # On anime juste la couleur du dot
        if hasattr(self, 'pulse_dot'):
            r = int(0x10 + (0x10 * math.sin(self._pulse * math.pi / 30)))
            g = int(0xB9 + (0x10 * math.sin(self._pulse * math.pi / 30)))
            b = int(0x81 + (0x10 * math.sin(self._pulse * math.pi / 30)))
            col = f"#{max(0,min(255,r)):02X}{max(0,min(255,g)):02X}{max(0,min(255,b)):02X}"
            self.pulse_dot.config(fg=col)
        self.after(50, self._start_pulse)

    # ══════════════════════════════════════════════════════════════════════════
    #  BUILD UI
    # ══════════════════════════════════════════════════════════════════════════
    def _build_ui(self):
        self._build_sidebar()
        self._build_main_area()

    def _build_sidebar(self):
        """Sidebar gauche fixe avec navigation."""
        self.sidebar = tk.Frame(self, bg=BG_SURFACE, width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo
        logo_f = tk.Frame(self.sidebar, bg=BG_SURFACE, pady=20)
        logo_f.pack(fill="x")
        tk.Label(logo_f, text="⬡", font=("Segoe UI", 28),
                 fg=ACCENT_CYAN, bg=BG_SURFACE).pack()
        tk.Label(logo_f, text="SysDiag", font=("Segoe UI", 16, "bold"),
                 fg=TEXT_MAIN, bg=BG_SURFACE).pack()
        tk.Label(logo_f, text="v4.0", font=("Segoe UI", 9),
                 fg=TEXT_SUB, bg=BG_SURFACE).pack()

        # Séparateur
        tk.Frame(self.sidebar, bg=BORDER, height=1).pack(fill="x", padx=16, pady=4)

        # Navigation
        nav_f = tk.Frame(self.sidebar, bg=BG_SURFACE)
        nav_f.pack(fill="x", pady=8)
        tk.Label(nav_f, text="NAVIGATION", font=("Segoe UI", 7, "bold"),
                 fg=TEXT_DIM, bg=BG_SURFACE).pack(anchor="w", padx=18, pady=(6,4))

        self._nav_buttons = []
        self._current_tab = tk.IntVar(value=0)
        nav_items = [
            (0, "🔍", "Diagnostic"),
            (1, "🛠️", "Réparations"),
            (2, "🤖", "Assistant IA"),
            (3, "⚙️", "Paramètres"),
        ]
        for idx, icon, label in nav_items:
            btn = self._make_nav_btn(nav_f, icon, label, idx)
            btn.pack(fill="x", padx=8, pady=2)
            self._nav_buttons.append(btn)

        # Séparateur
        tk.Frame(self.sidebar, bg=BORDER, height=1).pack(fill="x", padx=16, pady=12)

        # Stats rapides
        stats_f = tk.Frame(self.sidebar, bg=BG_SURFACE)
        stats_f.pack(fill="x", padx=14)
        tk.Label(stats_f, text="SYSTÈME EN DIRECT", font=("Segoe UI", 7, "bold"),
                 fg=TEXT_DIM, bg=BG_SURFACE).pack(anchor="w", pady=(0,8))

        self.live_cpu  = self._make_stat_bar(stats_f, "CPU")
        self.live_ram  = self._make_stat_bar(stats_f, "RAM")
        self.live_disk = self._make_stat_bar(stats_f, "Disque")
        self._update_live_stats()

        # Footer sidebar
        tk.Frame(self.sidebar, bg=BORDER, height=1).pack(fill="x", padx=16, pady=12, side="bottom")
        foot_f = tk.Frame(self.sidebar, bg=BG_SURFACE)
        foot_f.pack(side="bottom", fill="x", padx=14, pady=8)
        self.pulse_dot = tk.Label(foot_f, text="●", font=("Segoe UI", 10),
                                  fg=ACCENT_GREEN, bg=BG_SURFACE)
        self.pulse_dot.pack(side="left")
        self.status_lbl = tk.Label(foot_f, text="Prêt",
                                   font=("Segoe UI", 8), fg=TEXT_SUB, bg=BG_SURFACE)
        self.status_lbl.pack(side="left", padx=6)

        tk.Label(self.sidebar, text="Thabet Raki · GPLv3",
                 font=("Segoe UI", 7), fg=TEXT_DIM, bg=BG_SURFACE).pack(side="bottom", pady=4)

    def _make_nav_btn(self, parent, icon, label, idx):
        """Crée un bouton de navigation sidebar."""
        f = tk.Frame(parent, bg=BG_SURFACE, cursor="hand2")
        def select(i=idx):
            self._current_tab.set(i)
            self._show_tab(i)
            self._refresh_nav()
        f.bind("<Button-1>", lambda e: select())
        f.bind("<Enter>", lambda e, fr=f: fr.config(bg=BG_GLASS))
        f.bind("<Leave>", lambda e, fr=f: fr.config(bg="#161D30" if self._current_tab.get()==idx else BG_SURFACE))

        inner = tk.Frame(f, bg=f.cget("bg"), pady=8, padx=10)
        inner.pack(fill="x")
        tk.Label(inner, text=icon, font=("Segoe UI", 12),
                 fg=TEXT_MAIN, bg=inner.cget("bg")).pack(side="left")
        tk.Label(inner, text=label, font=("Segoe UI", 10),
                 fg=TEXT_MAIN, bg=inner.cget("bg")).pack(side="left", padx=8)

        for w in [f, inner] + inner.winfo_children():
            try:
                w.bind("<Button-1>", lambda e, s=select: s())
                w.bind("<Enter>", lambda e, fr=f: fr.config(bg=BG_GLASS))
                w.bind("<Leave>", lambda e, fr=f: fr.config(bg="#161D30" if self._current_tab.get()==idx else BG_SURFACE))
            except Exception:
                pass
        return f

    def _refresh_nav(self):
        for i, btn in enumerate(self._nav_buttons):
            is_active = (i == self._current_tab.get())
            btn.config(bg=BG_GLASS if is_active else BG_SURFACE)
            for w in btn.winfo_children():
                w.config(bg=BG_GLASS if is_active else BG_SURFACE)
                for ww in w.winfo_children():
                    col = ACCENT_CYAN if is_active else TEXT_MAIN
                    try: ww.config(fg=col, bg=BG_GLASS if is_active else BG_SURFACE)
                    except: pass

    def _make_stat_bar(self, parent, label):
        """Mini barre de stat live dans la sidebar."""
        f = tk.Frame(parent, bg=BG_SURFACE, pady=4)
        f.pack(fill="x")
        hdr = tk.Frame(f, bg=BG_SURFACE)
        hdr.pack(fill="x")
        tk.Label(hdr, text=label, font=("Segoe UI", 8),
                 fg=TEXT_SUB, bg=BG_SURFACE).pack(side="left")
        pct_lbl = tk.Label(hdr, text="0%", font=("Segoe UI", 8, "bold"),
                           fg=ACCENT_CYAN, bg=BG_SURFACE)
        pct_lbl.pack(side="right")

        bar_bg = tk.Frame(f, bg=BORDER, height=4)
        bar_bg.pack(fill="x", pady=(2,0))
        bar_fg = tk.Frame(bar_bg, bg=ACCENT_CYAN, height=4, width=0)
        bar_fg.place(x=0, y=0, relheight=1)
        return {"pct": pct_lbl, "bar": bar_fg, "bg": bar_bg}

    def _update_live_stats(self):
        try:
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            try:
                disk = psutil.disk_usage("C:/").percent
            except Exception:
                disk = 0.0
            for val, widget, color in [
                (cpu, self.live_cpu, ACCENT_CYAN),
                (ram, self.live_ram, ACCENT_AI),
                (disk, self.live_disk, ACCENT_GREEN),
            ]:
                widget["pct"].config(text=f"{val:.0f}%")
                bg_w = widget["bg"].winfo_width()
                if bg_w > 10:
                    widget["bar"].place(width=int(bg_w * val / 100))
                c = ACCENT_RED if val > 90 else ACCENT_WARN if val > 70 else color
                widget["bar"].config(bg=c)
        except Exception:
            pass
        self.after(2000, self._update_live_stats)

    def _build_main_area(self):
        """Zone principale avec stacked frames (tabs)."""
        self.main = tk.Frame(self, bg=BG_BASE)
        self.main.pack(side="right", fill="both", expand=True)

        # Topbar
        topbar = tk.Frame(self.main, bg=BG_SURFACE, height=52)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)

        self.page_title = tk.Label(topbar, text="Diagnostic Système",
                                   font=("Segoe UI", 13, "bold"),
                                   fg=TEXT_MAIN, bg=BG_SURFACE)
        self.page_title.pack(side="left", padx=20, pady=14)

        # Barre de progression (topbar)
        prog_f = tk.Frame(topbar, bg=BG_SURFACE)
        prog_f.pack(side="right", padx=16, pady=10)
        self.prog_var = tk.IntVar()
        s = ttk.Style(); s.theme_use("default")
        s.configure("Slim.Horizontal.TProgressbar",
                    troughcolor=BG_CARD, background=ACCENT_CYAN,
                    thickness=4, borderwidth=0)
        self.prog_bar = ttk.Progressbar(prog_f, variable=self.prog_var,
                                        maximum=100, length=200,
                                        style="Slim.Horizontal.TProgressbar")
        self.prog_bar.pack()

        # Content area
        self.content = tk.Frame(self.main, bg=BG_BASE)
        self.content.pack(fill="both", expand=True)

        # Créer les 4 pages
        self.pages = {}
        self.pages[0] = self._build_page_diagnostic()
        self.pages[1] = self._build_page_repairs()
        self.pages[2] = self._build_page_ai()
        self.pages[3] = self._build_page_settings()

        for page in self.pages.values():
            page.place(relx=0, rely=0, relwidth=1, relheight=1)

        self._show_tab(0)
        self._refresh_nav()

        # Footer actions
        self._build_footer()

    def _show_tab(self, idx):
        titles = {0: "🔍  Diagnostic Système", 1: "🛠️  Réparations CMD",
                  2: "🤖  Assistant IA", 3: "⚙️  Paramètres"}
        self.page_title.config(text=titles.get(idx, ""))
        for i, page in self.pages.items():
            if i == idx:
                page.lift()
            else:
                page.lower()

    # ── Page 0 : Diagnostic ───────────────────────────────────────────────
    def _build_page_diagnostic(self):
        page = tk.Frame(self.content, bg=BG_BASE)
        paned = tk.PanedWindow(page, orient="horizontal", bg=BG_BASE,
                               sashwidth=6, sashpad=0, sashrelief="flat",
                               sashcursor="sb_h_double_arrow")
        paned.pack(fill="both", expand=True, padx=12, pady=12)

        # Panel gauche : sections
        left = GlassFrame(paned, width=220)
        paned.add(left, minsize=180)
        tk.Label(left, text="SECTIONS", font=("Segoe UI", 8, "bold"),
                 fg=TEXT_DIM, bg=BG_GLASS).pack(anchor="w", padx=12, pady=(10,4))
        self.sec_list = tk.Listbox(left, bg=BG_GLASS, fg=TEXT_MAIN,
                                   font=("Segoe UI", 10), selectbackground="#1A4A5A",
                                   selectforeground=ACCENT_CYAN,
                                   activestyle="none", relief="flat", bd=0,
                                   highlightthickness=0, cursor="hand2",
                                   selectborderwidth=0)
        self.sec_list.pack(fill="both", expand=True, padx=4, pady=(0,6))
        self.sec_list.bind("<<ListboxSelect>>", self._on_section_select)

        # Panel droit : détail
        right = tk.Frame(paned, bg=BG_BASE)
        paned.add(right, minsize=500)

        # Cards résumé CPU/RAM/Disk en haut
        cards_f = tk.Frame(right, bg=BG_BASE)
        cards_f.pack(fill="x", pady=(0, 8))
        self.metric_cards = {}
        for label, color in [("CPU", ACCENT_CYAN), ("RAM", ACCENT_AI), ("Disque", ACCENT_GREEN), ("Réseau", ACCENT_BLUE)]:
            card = self._make_metric_card(cards_f, label, "–", color)
            card.pack(side="left", padx=4, fill="x", expand=True)
            self.metric_cards[label] = card

        self.detail = scrolledtext.ScrolledText(
            right, bg=BG_GLASS, fg=TEXT_MAIN, font=("Cascadia Code", 10),
            relief="flat", bd=0, insertbackground=ACCENT_CYAN,
            wrap="word", state="disabled",
            padx=16, pady=12
        )
        self.detail.pack(fill="both", expand=True)
        self._config_detail_tags()
        return page

    def _make_metric_card(self, parent, label, value, color):
        f = tk.Frame(parent, bg=BG_CARD,
                     highlightbackground="#1A2540", highlightthickness=1)
        tk.Label(f, text=label, font=("Segoe UI", 8, "bold"),
                 fg=color, bg=BG_CARD).pack(anchor="w", padx=10, pady=(8,0))
        lbl = tk.Label(f, text=value, font=("Segoe UI", 18, "bold"),
                       fg=TEXT_MAIN, bg=BG_CARD)
        lbl.pack(anchor="w", padx=10, pady=(0,8))
        f._value_label = lbl
        return f

    def _update_metric_card(self, label, value):
        card = self.metric_cards.get(label)
        if card and hasattr(card, "_value_label"):
            card._value_label.config(text=value)

    def _config_detail_tags(self):
        t = self.detail
        t.tag_config("title",    foreground=ACCENT_CYAN,  font=("Segoe UI", 14, "bold"))
        t.tag_config("key",      foreground=ACCENT_GREEN, font=("Cascadia Code", 10, "bold"))
        t.tag_config("val",      foreground=TEXT_MAIN,    font=("Cascadia Code", 10))
        t.tag_config("critical", foreground=ACCENT_RED,   font=("Segoe UI", 10, "bold"))
        t.tag_config("warning",  foreground=ACCENT_WARN,  font=("Segoe UI", 10, "bold"))
        t.tag_config("ok",       foreground=ACCENT_GREEN, font=("Segoe UI", 10, "bold"))
        t.tag_config("repair",   foreground="#93C5FD",    font=("Cascadia Code", 9))
        t.tag_config("sep",      foreground=BORDER,       font=("Cascadia Code", 9))
        t.tag_config("badge_ok", foreground=ACCENT_GREEN, font=("Segoe UI", 9))
        t.tag_config("badge_warn",foreground=ACCENT_WARN, font=("Segoe UI", 9))

    # ── Page 1 : Réparations CMD ──────────────────────────────────────────
    def _build_page_repairs(self):
        page = tk.Frame(self.content, bg=BG_BASE)

        # Panel gauche : boutons
        left = GlassFrame(page, width=300)
        left.pack(side="left", fill="y", padx=(12,0), pady=12)
        left.pack_propagate(False)

        tk.Label(left, text="ACTIONS DE RÉPARATION", font=("Segoe UI", 8, "bold"),
                 fg=TEXT_DIM, bg=BG_GLASS).pack(anchor="w", padx=12, pady=(10,6))

        canvas = tk.Canvas(left, bg=BG_GLASS, highlightthickness=0)
        sb = ttk.Scrollbar(left, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=BG_GLASS)
        scroll_frame.bind("<Configure>",
                          lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        CAT_COLORS = {
            "Mises à jour": ACCENT_CYAN,  "Pilotes": "#FB923C",
            "Système": ACCENT_GREEN,       "Disques": "#FB7185",
            "Réseau": ACCENT_BLUE,         "RAM": ACCENT_AI,
            "CPU": CMD_YELLOW,             "Sécurité": ACCENT_RED,
            "Applications": "#86EFAC",
        }
        categories = {}
        for key, r in REPAIR_COMMANDS.items():
            cat = r.get("category", "Autre")
            categories.setdefault(cat, []).append((key, r))

        for cat, items in categories.items():
            color = CAT_COLORS.get(cat, ACCENT_CYAN)
            cat_f = tk.Frame(scroll_frame, bg=BG_GLASS)
            cat_f.pack(fill="x", padx=6, pady=(8,2))
            tk.Label(cat_f, text=f"  {cat.upper()}", font=("Segoe UI", 7, "bold"),
                     fg=color, bg=BG_GLASS).pack(side="left")
            tk.Frame(cat_f, bg="#1E293B", height=1).pack(side="left", fill="x", expand=True, padx=6, pady=6)

            for key, r in items:
                self._make_repair_btn(scroll_frame, key, r, color)

        # Panel droit : terminal
        right = tk.Frame(page, bg=BG_BASE)
        right.pack(side="right", fill="both", expand=True, padx=12, pady=12)

        # Header terminal
        th = tk.Frame(right, bg="#050805", pady=6, padx=12,
                      highlightbackground="#0A3020", highlightthickness=1)
        th.pack(fill="x")
        dots = tk.Frame(th, bg="#050805")
        dots.pack(side="left")
        for col in ["#FF5F57", "#FFBD2E", "#28CA41"]:
            tk.Label(dots, text="●", font=("Segoe UI", 10), fg=col, bg="#050805").pack(side="left", padx=1)
        tk.Label(th, text="  PowerShell  ·  SysDiag v4.0  ·  Thabet Raki",
                 font=("Cascadia Code", 9), fg=CMD_GREEN, bg="#050805").pack(side="left", padx=8)
        tk.Button(th, text="⟳ Effacer", font=("Segoe UI", 8), fg=TEXT_SUB,
                  bg="#050805", relief="flat", cursor="hand2",
                  command=self._clear_terminal).pack(side="right")

        self.terminal_out = scrolledtext.ScrolledText(
            right, bg="#050805", fg=CMD_WHITE,
            font=("Cascadia Code", 10), relief="flat", bd=0,
            insertbackground=CMD_GREEN, wrap="word", state="disabled",
            padx=12, pady=8
        )
        self.terminal_out.pack(fill="both", expand=True)

        # Barre de commande
        cmd_bar = tk.Frame(right, bg="#050805", pady=8, padx=12,
                           highlightbackground="#0A3020", highlightthickness=1)
        cmd_bar.pack(fill="x")
        tk.Label(cmd_bar, text="PS>", font=("Cascadia Code", 10, "bold"),
                 fg=CMD_GREEN, bg="#050805").pack(side="left")
        self.cmd_entry = tk.Entry(cmd_bar, bg="#050805", fg=CMD_WHITE,
                                  font=("Cascadia Code", 10), relief="flat",
                                  insertbackground=CMD_GREEN, bd=0)
        self.cmd_entry.pack(side="left", fill="x", expand=True, padx=(6,0))
        self.cmd_entry.bind("<Return>", self._run_manual_cmd)
        tk.Button(cmd_bar, text="▶ Exécuter", font=("Cascadia Code", 9, "bold"),
                  fg="#050805", bg=CMD_GREEN, relief="flat", cursor="hand2",
                  command=self._run_manual_cmd).pack(side="right", padx=(6,0))

        # Initialiser le terminal + IA
        self.terminal = CMDTerminal(self.terminal_out, self._set_status)
        self.ai = AIAssistant(self.terminal)
        self.terminal.write("  SysDiag v4.0 — Terminal PowerShell intégré\n", "info")
        self.terminal.write("  Auteur : Thabet Raki  ·  Licence : GPLv3\n", "info")
        self.terminal.write("  Tapez une commande ou cliquez sur une action à gauche.\n\n", "info")
        return page

    def _make_repair_btn(self, parent, key, r, color):
        f = tk.Frame(parent, bg=BG_GLASS, cursor="hand2")
        f.pack(fill="x", padx=6, pady=1)
        inner = tk.Frame(f, bg=BG_GLASS, pady=7, padx=10)
        inner.pack(fill="x")
        tk.Label(inner, text=r['icon'], font=("Segoe UI", 11), fg=color, bg=BG_GLASS).pack(side="left")
        tk.Label(inner, text=r['label'], font=("Segoe UI", 9), fg=TEXT_MAIN,
                 bg=BG_GLASS, anchor="w", wraplength=200).pack(side="left", padx=8)

        def on_click(k=key): self._run_repair(k)
        def on_enter(e, fr=f):
            fr.config(highlightbackground=color, highlightthickness=1)
            for w in fr.winfo_children(): w.config(bg=BG_CARD)
        def on_leave(e, fr=f):
            fr.config(highlightthickness=0)
            for w in fr.winfo_children(): w.config(bg=BG_GLASS)

        for w in [f, inner] + inner.winfo_children():
            try:
                w.bind("<Button-1>", lambda e, oc=on_click: oc())
                w.bind("<Enter>", on_enter)
                w.bind("<Leave>", on_leave)
            except Exception: pass

    # ── Page 2 : Assistant IA ─────────────────────────────────────────────
    def _build_page_ai(self):
        page = tk.Frame(self.content, bg=BG_BASE)

        # Header moteur IA
        ai_header = GlassFrame(page)
        ai_header.pack(fill="x", padx=12, pady=(12,0))

        engine_f = tk.Frame(ai_header, bg=BG_GLASS, pady=10, padx=16)
        engine_f.pack(fill="x")

        tk.Label(engine_f, text="🤖  Moteur IA actif :",
                 font=("Segoe UI", 10, "bold"), fg=TEXT_MAIN, bg=BG_GLASS).pack(side="left")

        self.engine_var = tk.StringVar(value="local")
        for val, label, color in [
            ("claude", "  ◆ Claude (Anthropic)  ", ACCENT_AI),
            ("gemini", "  ✦ Gemini (Google)  ",    ACCENT_GEM),
            ("local",  "  ● Mode Local  ",          TEXT_SUB),
        ]:
            rb = tk.Radiobutton(engine_f, text=label, variable=self.engine_var,
                                value=val, font=("Segoe UI", 9, "bold"),
                                fg=color, bg=BG_GLASS, selectcolor=BG_GLASS,
                                activebackground=BG_GLASS, activeforeground=color,
                                relief="flat", cursor="hand2",
                                command=self._on_engine_change)
            rb.pack(side="left", padx=6)

        # Zone de chat
        self.ai_chat = scrolledtext.ScrolledText(
            page, bg=BG_GLASS, fg=TEXT_MAIN, font=("Segoe UI", 10),
            relief="flat", bd=0, insertbackground=ACCENT_AI,
            wrap="word", state="disabled",
            padx=16, pady=12
        )
        self.ai_chat.pack(fill="both", expand=True, padx=12, pady=8)
        self._config_ai_tags()

        # Boutons rapides
        quick = tk.Frame(page, bg=BG_BASE)
        quick.pack(fill="x", padx=12, pady=(0,6))
        tk.Label(quick, text="Analyse rapide :", font=("Segoe UI", 9),
                 fg=TEXT_SUB, bg=BG_BASE).pack(side="left", padx=(0,8))
        for label, prompt in [
            ("📊 Analyser", "Analyse les problèmes détectés et donne-moi un plan d'action prioritaire"),
            ("🔄 Mises à jour", "Comment mettre à jour tous les composants de mon PC Windows ?"),
            ("⚡ Optimiser", "Quelles commandes pour optimiser les performances de mon Windows ?"),
            ("🦠 Sécurité", "Vérifie la sécurité de mon système et propose des corrections"),
        ]:
            tk.Button(quick, text=label, font=("Segoe UI", 8, "bold"),
                      fg=TEXT_MAIN, bg=BG_GLASS, relief="flat", cursor="hand2",
                      activebackground="#3D1F5A", activeforeground=TEXT_MAIN,
                      padx=12, pady=5,
                      command=lambda p=prompt: self._ask_ai(p)).pack(side="left", padx=3)

        # Saisie IA
        ai_bar = GlassFrame(page)
        ai_bar.pack(fill="x", padx=12, pady=(0,12))
        bar_inner = tk.Frame(ai_bar, bg=BG_GLASS, pady=8, padx=12)
        bar_inner.pack(fill="x")
        self.ai_entry = tk.Entry(bar_inner, bg=BG_INPUT, fg=TEXT_MAIN,
                                 font=("Segoe UI", 10), relief="flat",
                                 insertbackground=ACCENT_AI, bd=0,
                                 highlightthickness=1,
                                 highlightbackground=BORDER,
                                 highlightcolor=ACCENT_AI)
        self.ai_entry.pack(side="left", fill="x", expand=True, ipady=6, padx=(0,8))
        self.ai_entry.bind("<Return>", lambda e: self._ask_ai(self.ai_entry.get()))
        tk.Button(bar_inner, text="  ➤ Envoyer  ",
                  font=("Segoe UI", 10, "bold"), fg=BG_BASE, bg=ACCENT_AI,
                  relief="flat", cursor="hand2", padx=10,
                  activebackground=ACCENT_AI,
                  command=lambda: self._ask_ai(self.ai_entry.get())).pack(side="right")

        # Message d'accueil
        self._ai_write("SysDiag-AI", "Bonjour ! Je suis votre assistant IA.\n\n"
                       "• Sélectionnez votre moteur IA en haut (Claude, Gemini ou mode local)\n"
                       "• Configurez vos clés API dans ⚙️ Paramètres\n"
                       "• Lancez d'abord un diagnostic (🔍), puis posez vos questions !", "ai_msg", "local")
        return page

    # ── Page 3 : Paramètres ───────────────────────────────────────────────
    def _build_page_settings(self):
        page = tk.Frame(self.content, bg=BG_BASE)
        scroll = scrolledtext.ScrolledText(page, bg=BG_BASE, relief="flat",
                                           bd=0, state="disabled")
        # On n'utilise pas ScrolledText pour les settings — frame scrollable manuelle

        outer = tk.Frame(page, bg=BG_BASE)
        outer.pack(fill="both", expand=True, padx=40, pady=20)

        # ── Clé Anthropic ────────────────────────────────────────────────
        self._settings_section(outer, "◆  Clé API Anthropic (Claude)", ACCENT_AI)
        claude_f = GlassFrame(outer)
        claude_f.pack(fill="x", pady=(4,16))
        cf = tk.Frame(claude_f, bg=BG_GLASS, padx=16, pady=14)
        cf.pack(fill="x")
        tk.Label(cf, text="Clé API (sk-ant-…)",
                 font=("Segoe UI", 9), fg=TEXT_SUB, bg=BG_GLASS).pack(anchor="w")
        self.claude_key_entry = tk.Entry(cf, bg=BG_INPUT, fg=TEXT_MAIN,
                                         font=("Cascadia Code", 10), relief="flat",
                                         show="*", insertbackground=ACCENT_AI, bd=0,
                                         highlightthickness=1,
                                         highlightbackground=BORDER,
                                         highlightcolor=ACCENT_AI)
        self.claude_key_entry.pack(fill="x", ipady=7, pady=(4,0))
        tk.Label(cf, text="Obtenez une clé sur console.anthropic.com",
                 font=("Segoe UI", 8), fg=TEXT_DIM, bg=BG_GLASS).pack(anchor="w", pady=(4,0))

        # ── Clé Google Gemini ─────────────────────────────────────────────
        self._settings_section(outer, "✦  Clé API Google Gemini", ACCENT_GEM)
        gemini_f = GlassFrame(outer)
        gemini_f.pack(fill="x", pady=(4,16))
        gf = tk.Frame(gemini_f, bg=BG_GLASS, padx=16, pady=14)
        gf.pack(fill="x")
        tk.Label(gf, text="Clé API Google (AIza…)",
                 font=("Segoe UI", 9), fg=TEXT_SUB, bg=BG_GLASS).pack(anchor="w")
        self.gemini_key_entry = tk.Entry(gf, bg=BG_INPUT, fg=TEXT_MAIN,
                                         font=("Cascadia Code", 10), relief="flat",
                                         show="*", insertbackground=ACCENT_GEM, bd=0,
                                         highlightthickness=1,
                                         highlightbackground=BORDER,
                                         highlightcolor=ACCENT_GEM)
        self.gemini_key_entry.pack(fill="x", ipady=7, pady=(4,0))
        tk.Label(gf, text="Obtenez une clé sur aistudio.google.com",
                 font=("Segoe UI", 8), fg=TEXT_DIM, bg=BG_GLASS).pack(anchor="w", pady=(4,0))

        # ── Bouton Enregistrer ────────────────────────────────────────────
        btn_f = tk.Frame(outer, bg=BG_BASE)
        btn_f.pack(fill="x", pady=8)
        ModernButton(btn_f, "  💾  Enregistrer les clés  ", command=self._save_api_keys,
                     color=ACCENT_GREEN, text_color=BG_BASE, width=240, height=40, font_size=10
                     ).pack(side="left")

        # ── Infos ──────────────────────────────────────────────────────────
        self._settings_section(outer, "ℹ  À propos", TEXT_SUB)
        info_f = GlassFrame(outer)
        info_f.pack(fill="x", pady=(4,0))
        fi = tk.Frame(info_f, bg=BG_GLASS, padx=16, pady=14)
        fi.pack(fill="x")
        for line in [
            ("SysDiag", "v4.0", ACCENT_CYAN),
            ("Auteur", "Thabet Raki", TEXT_MAIN),
            ("Licence", "GNU GPL v3.0", ACCENT_GREEN),
            ("URL", "https://www.gnu.org/licenses/gpl-3.0.html", ACCENT_BLUE),
            ("IA supportées", "Anthropic Claude + Google Gemini + Mode Local", ACCENT_AI),
        ]:
            row = tk.Frame(fi, bg=BG_GLASS)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=f"{line[0]} :", font=("Segoe UI", 9),
                     fg=TEXT_SUB, bg=BG_GLASS, width=18, anchor="w").pack(side="left")
            tk.Label(row, text=line[1], font=("Segoe UI", 9, "bold"),
                     fg=line[2], bg=BG_GLASS).pack(side="left")
        return page

    def _settings_section(self, parent, title, color):
        tk.Label(parent, text=title, font=("Segoe UI", 11, "bold"),
                 fg=color, bg=BG_BASE).pack(anchor="w", pady=(16,0))

    # ── Footer ────────────────────────────────────────────────────────────
    def _build_footer(self):
        f = tk.Frame(self.main, bg=BG_SURFACE, pady=10, padx=16)
        f.pack(fill="x", side="bottom")

        ModernButton(f, "▶  LANCER LE DIAGNOSTIC",
                     command=self._run_diagnostic,
                     color=ACCENT_CYAN, text_color=BG_BASE,
                     width=220, height=38, font_size=10).pack(side="left", padx=(0,8))

        ModernButton(f, "⚡  TOUT RÉPARER (AUTO)",
                     command=self._auto_repair,
                     color=ACCENT_GREEN, text_color=BG_BASE,
                     width=210, height=38, font_size=10).pack(side="left", padx=4)

        ModernButton(f, "💾  EXPORTER RAPPORT",
                     command=self._export_report,
                     color=BORDER_GLOW, text_color=TEXT_MAIN,
                     width=190, height=38, font_size=10).pack(side="left", padx=4)

        if platform.system() == "Windows" and not is_admin():
            ModernButton(f, "🔑  ADMIN",
                         command=run_as_admin,
                         color=ACCENT_WARN, text_color=BG_BASE,
                         width=120, height=38, font_size=10).pack(side="left", padx=4)

        # Indicateur moteur IA
        self.engine_badge = tk.Label(f, text="● Mode Local",
                                     font=("Segoe UI", 8, "bold"),
                                     fg=TEXT_SUB, bg=BG_SURFACE)
        self.engine_badge.pack(side="right", padx=8)
        tk.Label(f, text="Moteur IA :", font=("Segoe UI", 8),
                 fg=TEXT_DIM, bg=BG_SURFACE).pack(side="right")

    # ══════════════════════════════════════════════════════════════════════════
    #  ACTIONS
    # ══════════════════════════════════════════════════════════════════════════
    def _set_status(self, msg, color=None):
        self.status_lbl.config(text=msg, fg=color or ACCENT_GREEN)

    def _run_diagnostic(self):
        self._show_tab(0)
        self._current_tab.set(0)
        self._refresh_nav()
        self.sec_list.delete(0, tk.END)
        self._detail_write("", clear=True)

        def work():
            sections, issues = self.engine.run_full_diagnostic(
                progress_callback=lambda v, m: (
                    self.after(0, lambda: self.prog_var.set(v)),
                    self.after(0, self._set_status, m, ACCENT_WARN)
                )
            )
            self._sections = sections
            self._issues   = issues
            self.after(0, self._populate_results, sections, issues)

        threading.Thread(target=work, daemon=True).start()
        self._set_status("Analyse en cours…", ACCENT_WARN)

    def _populate_results(self, sections, issues):
        self._set_status("Analyse terminée ✔", ACCENT_GREEN)
        self.prog_var.set(100)

        # Mettre à jour les metric cards
        cpu_info  = sections.get("CPU", {})
        ram_info  = sections.get("RAM", {})
        disk_info = sections.get("Disques", {})
        net_info  = sections.get("Réseau", {})
        self._update_metric_card("CPU",   cpu_info.get("Utilisation", "–"))
        self._update_metric_card("RAM",   ram_info.get("Utilisé", "–").split("(")[-1].rstrip(")") if "(" in ram_info.get("Utilisé","") else ram_info.get("Utilisé","–"))
        first_disk = next((v for k, v in disk_info.items() if "Disque" in k), "–")
        self._update_metric_card("Disque", first_disk.split("(")[-1].rstrip(")") if "(" in first_disk else first_disk[:6])
        self._update_metric_card("Réseau", net_info.get("Connexion Internet", "–").replace("✔ ","").replace("✘ ","✘"))

        for name in sections:
            self.sec_list.insert(tk.END, f"  {name}")
        count = len(issues)
        label = f"  ⚠ Problèmes ({count})" if count else "  ✔ Aucun problème"
        self.sec_list.insert(tk.END, label)
        self._show_summary(sections, issues)

    def _show_summary(self, sections, issues):
        t = self.detail
        t.config(state="normal"); t.delete("1.0", tk.END)
        t.insert(tk.END, "RAPPORT DE DIAGNOSTIC  ·  SysDiag v4.0\n", "title")
        t.insert(tk.END, f"  {datetime.datetime.now().strftime('%d/%m/%Y  %H:%M:%S')}  ·  Thabet Raki\n", "val")
        t.insert(tk.END, "─" * 68 + "\n\n", "sep")
        for k, v in sections.get("Système", {}).items():
            t.insert(tk.END, f"  {k:<24} ", "key")
            t.insert(tk.END, f"{v}\n", "val")
        t.insert(tk.END, "\n" + "─" * 68 + "\n\n", "sep")
        t.insert(tk.END, "  RÉSULTATS\n\n", "title")
        critiques = [i for i in issues if i["severite"] == "CRITIQUE"]
        avert     = [i for i in issues if i["severite"] == "AVERTISSEMENT"]
        if not issues:
            t.insert(tk.END, "  ✔  Système en bonne santé !\n", "ok")
        else:
            t.insert(tk.END, f"  ✘  {len(critiques)} CRITIQUE(S)\n", "critical")
            t.insert(tk.END, f"  ⚠  {len(avert)} AVERTISSEMENT(S)\n\n", "warning")
            for iss in issues:
                tag = "critical" if iss["severite"] == "CRITIQUE" else "warning"
                t.insert(tk.END, f"\n  [{iss['severite']}] {iss['composant']} — {iss['probleme']}\n", tag)
                for k in iss.get("repair_keys", []):
                    r = REPAIR_COMMANDS.get(k, {})
                    if r:
                        t.insert(tk.END, f"    {r['icon']} {r['label']}\n", "repair")
        t.insert(tk.END, "\n\n  → Onglet 🛠️ pour les réparations  ·  Onglet 🤖 pour l'IA\n", "val")
        t.config(state="disabled")

    def _on_section_select(self, event):
        sel = self.sec_list.curselection()
        if not sel: return
        idx  = sel[0]
        keys = list(self._sections.keys())
        if idx < len(keys):
            self._show_section(keys[idx], self._sections[keys[idx]])
        else:
            self._show_all_issues()

    def _show_section(self, name, data):
        t = self.detail
        t.config(state="normal"); t.delete("1.0", tk.END)
        t.insert(tk.END, f"  {name.upper()}\n", "title")
        t.insert(tk.END, "─" * 58 + "\n\n", "sep")
        if isinstance(data, dict):
            for k, v in data.items():
                t.insert(tk.END, f"  {k:<26} ", "key")
                t.insert(tk.END, f"{v}\n", "val")
        rel = [i for i in self._issues if i["composant"].lower().startswith(name.lower())]
        if rel:
            t.insert(tk.END, "\n" + "─" * 58 + "\n\n", "sep")
            t.insert(tk.END, "  PROBLÈMES DÉTECTÉS\n\n", "critical")
            for iss in rel:
                tag = "critical" if iss["severite"] == "CRITIQUE" else "warning"
                t.insert(tk.END, f"  [{iss['severite']}] {iss['probleme']}\n", tag)
                for k in iss.get("repair_keys", []):
                    r = REPAIR_COMMANDS.get(k, {})
                    if r:
                        t.insert(tk.END, f"    {r['icon']} {r['label']}\n", "repair")
        t.config(state="disabled")

    def _show_all_issues(self):
        t = self.detail
        t.config(state="normal"); t.delete("1.0", tk.END)
        t.insert(tk.END, "  TOUS LES PROBLÈMES\n", "title")
        t.insert(tk.END, "─" * 58 + "\n\n", "sep")
        if not self._issues:
            t.insert(tk.END, "  ✔  Aucun problème.\n", "ok")
        else:
            for iss in self._issues:
                tag = "critical" if iss["severite"] == "CRITIQUE" else "warning"
                t.insert(tk.END, f"\n  [{iss['severite']}]  {iss['composant']}\n", tag)
                t.insert(tk.END, f"  {iss['probleme']}\n", "val")
                for k in iss.get("repair_keys", []):
                    r = REPAIR_COMMANDS.get(k, {})
                    if r:
                        t.insert(tk.END, f"    {r['icon']} {r['label']}\n", "repair")
        t.config(state="disabled")

    def _detail_write(self, text, clear=False):
        t = self.detail
        t.config(state="normal")
        if clear: t.delete("1.0", tk.END)
        t.insert(tk.END, text)
        t.config(state="disabled")

    def _run_repair(self, key):
        self._show_tab(1); self._current_tab.set(1); self._refresh_nav()
        self.terminal.run_repair(key)

    def _run_manual_cmd(self, event=None):
        cmd = self.cmd_entry.get().strip()
        if cmd:
            self.cmd_entry.delete(0, tk.END)
            self.terminal.run_command(cmd)

    def _clear_terminal(self):
        self.terminal.clear()
        self.terminal.write("  Terminal vidé.\n", "info")

    def _auto_repair(self):
        if not self._issues:
            messagebox.showinfo("Info", "Lancez d'abord un diagnostic.")
            return
        if not messagebox.askyesno("Réparation automatique",
                                    "Lancer automatiquement TOUTES les réparations recommandées ?\n\n"
                                    "Cela peut prendre plusieurs minutes."):
            return
        self._show_tab(1); self._current_tab.set(1); self._refresh_nav()
        all_keys = []
        for iss in self._issues:
            for k in iss.get("repair_keys", []):
                if k not in all_keys:
                    all_keys.append(k)
        def _run_all():
            for k in all_keys:
                self.after(0, self._run_repair, k)
                time.sleep(2)
        threading.Thread(target=_run_all, daemon=True).start()

    # ── IA ─────────────────────────────────────────────────────────────────
    def _on_engine_change(self):
        engine = self.engine_var.get()
        if hasattr(self, 'ai'):
            self.ai.set_engine(engine)
        labels = {"claude": ("◆ Claude", ACCENT_AI),
                  "gemini": ("✦ Gemini", ACCENT_GEM),
                  "local":  ("● Local",  TEXT_SUB)}
        lbl, col = labels.get(engine, ("Local", TEXT_SUB))
        if hasattr(self, 'engine_badge'):
            self.engine_badge.config(text=lbl, fg=col)

    def _save_api_keys(self):
        ck = self.claude_key_entry.get().strip()
        gk = self.gemini_key_entry.get().strip()
        if not ck and not gk:
            messagebox.showwarning("Clés manquantes", "Entrez au moins une clé API.")
            return
        if hasattr(self, 'ai'):
            self.ai.set_keys(anthropic_key=ck, gemini_key=gk)
        # Auto-sélectionner le moteur selon la clé fournie
        if ck:
            self.engine_var.set("claude")
        elif gk:
            self.engine_var.set("gemini")
        self._on_engine_change()
        msg_parts = []
        if ck: msg_parts.append("Claude (Anthropic)")
        if gk: msg_parts.append("Gemini (Google)")
        self._ai_write("Système",
                       f"Clés enregistrées : {' + '.join(msg_parts)}\n"
                       f"Moteur actif : {self.engine_var.get().capitalize()}",
                       "ai_msg", "local")
        messagebox.showinfo("✔ Enregistré", f"Clés API enregistrées !\nMoteur : {self.engine_var.get().capitalize()}")

    def _ask_ai(self, prompt: str):
        if not prompt.strip(): return
        self.ai_entry.delete(0, tk.END)
        self._ai_write("Vous", prompt + "\n", "user_msg", "user")
        self._set_status("🤖 IA en cours…", ACCENT_AI)

        def callback(text, source="local"):
            self.after(0, self._ai_write, "SysDiag-AI", text + "\n", "ai_msg", source)
            self.after(0, self._set_status, "Prêt", ACCENT_GREEN)

        if hasattr(self, 'ai'):
            self.ai.ask(prompt, issues=self._issues, sections=self._sections, callback=callback)

    def _config_ai_tags(self):
        t = self.ai_chat
        t.tag_config("user_label",  foreground=ACCENT_CYAN, font=("Segoe UI", 8, "bold"))
        t.tag_config("user_msg",    foreground=TEXT_MAIN,   font=("Segoe UI", 10))
        t.tag_config("ai_label",    foreground=ACCENT_AI,   font=("Segoe UI", 8, "bold"))
        t.tag_config("ai_label_gem",foreground=ACCENT_GEM,  font=("Segoe UI", 8, "bold"))
        t.tag_config("ai_label_loc",foreground=TEXT_SUB,    font=("Segoe UI", 8, "bold"))
        t.tag_config("ai_msg",      foreground="#DDD6FE",   font=("Segoe UI", 10))
        t.tag_config("code",        foreground=CMD_GREEN,   font=("Cascadia Code", 10), background="#0A1A0A")
        t.tag_config("sep",         foreground=BORDER,      font=("Segoe UI", 8))

    def _ai_write(self, sender, text, tag, source="local"):
        t = self.ai_chat
        t.config(state="normal")
        # Choisir le tag label selon la source
        if sender == "Vous":
            label_tag = "user_label"
        elif source == "claude":
            label_tag = "ai_label"
        elif source == "gemini":
            label_tag = "ai_label_gem"
        else:
            label_tag = "ai_label_loc"

        source_icon = {"claude": " ◆ Claude", "gemini": " ✦ Gemini", "local": " ● Local", "user": ""}.get(source, "")
        t.insert(tk.END, f"\n  [{sender}{source_icon}]\n", label_tag)

        parts = text.split("```")
        for i, part in enumerate(parts):
            if i % 2 == 1:
                content = part.lstrip("cmd\n").lstrip("powershell\n")
                t.insert(tk.END, f"  {content}\n", "code")
            else:
                t.insert(tk.END, f"  {part}", tag)
        t.insert(tk.END, "\n", "sep")
        t.see(tk.END)
        t.config(state="disabled")

    # ── Export rapport ─────────────────────────────────────────────────────
    def _export_report(self):
        if not self._sections:
            messagebox.showinfo("Info", "Lancez d'abord un diagnostic.")
            return
        fname = f"SysDiag_rapport_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        path  = os.path.join(os.path.expanduser("~"), "Desktop", fname)
        lines = [
            "=" * 70,
            "  RAPPORT SysDiag v4.0 — Thabet Raki — GPLv3",
            f"  Date : {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            "=" * 70, ""
        ]
        for sec, data in self._sections.items():
            lines.append(f"\n[{sec.upper()}]")
            if isinstance(data, dict):
                for k, v in data.items():
                    lines.append(f"  {k:<28} {v}")
        if self._issues:
            lines += ["", "=" * 70, "  PROBLÈMES ET RÉPARATIONS", "=" * 70]
            for iss in self._issues:
                lines += [f"\n  [{iss['severite']}] {iss['composant']} — {iss['probleme']}",
                          "  Commandes recommandées :"]
                for k in iss.get("repair_keys", []):
                    r = REPAIR_COMMANDS.get(k, {})
                    if r:
                        lines.append(f"    {r['icon']} {r['label']}")
                        for cmd in r["cmds"]:
                            lines.append(f"       > {cmd}")
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            messagebox.showinfo("✔ Exporté", f"Rapport sauvegardé :\n{path}")
        except Exception as e:
            messagebox.showerror("Erreur", str(e))


# ══════════════════════════════════════════════════════════════════════════════
#  POINT D'ENTRÉE
# ══════════════════════════════════════════════════════════════════════════════
def main():
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass
    app = SysDiagApp()
    app.mainloop()

if __name__ == "__main__":
    main()

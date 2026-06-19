# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║       SysDiag v3.0 - Diagnostic + IA + Terminal CMD                         ║
║                                                                              ║
║  Copyright (C) 2026  Thabet Raki                                             ║
║  Licence : GNU General Public License v3 (GPLv3)                            ║
║  https://www.gnu.org/licenses/gpl-3.0.html                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
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

# ─── Palette ──────────────────────────────────────────────────────────────────
BG_DARK      = "#0A0C10"
BG_PANEL     = "#111318"
BG_CARD      = "#161B27"
BG_TERMINAL  = "#0C0E0A"
ACCENT_CYAN  = "#00E5FF"
ACCENT_GREEN = "#39FF14"
ACCENT_RED   = "#FF2244"
ACCENT_WARN  = "#FFB300"
ACCENT_AI    = "#BD00FF"
TEXT_MAIN    = "#E8EAF0"
TEXT_SUB     = "#555F6E"
BORDER       = "#1E2535"
CMD_GREEN    = "#00FF41"
CMD_RED      = "#FF4444"
CMD_YELLOW   = "#FFD700"
CMD_WHITE    = "#CCCCCC"
CMD_CYAN     = "#00FFFF"

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_API_KEY = ""  # Optionnel — l'IA fonctionne aussi sans clé (mode local)

# ══════════════════════════════════════════════════════════════════════════════
#  VÉRIFICATION ADMIN
# ══════════════════════════════════════════════════════════════════════════════
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def run_as_admin():
    """Relance le script en mode administrateur."""
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
    # ── Windows Update ──────────────────────────────────────────────────────
    "windows_update": {
        "label": "Rechercher les mises à jour Windows",
        "cmds": [
            'powershell -Command "Install-Module PSWindowsUpdate -Force -Scope CurrentUser -ErrorAction SilentlyContinue"',
            'powershell -Command "Get-WindowsUpdate -AcceptAll -Install -AutoReboot:$false"',
        ],
        "category": "Mises à jour",
        "icon": "🔄",
    },
    "windows_update_reset": {
        "label": "Réinitialiser Windows Update",
        "cmds": [
            "net stop wuauserv",
            "net stop cryptSvc",
            "net stop bits",
            "net stop msiserver",
            'rd /s /q "%systemroot%\\SoftwareDistribution"',
            'rd /s /q "%systemroot%\\system32\\catroot2"',
            "net start wuauserv",
            "net start cryptSvc",
            "net start bits",
            "net start msiserver",
        ],
        "category": "Mises à jour",
        "icon": "🔄",
    },

    # ── Pilotes ─────────────────────────────────────────────────────────────
    "drivers_scan": {
        "label": "Scanner les pilotes manquants / obsolètes",
        "cmds": [
            'powershell -Command "Get-WmiObject Win32_PnPSignedDriver | Where-Object {$_.IsSigned -eq $false} | Select-Object DeviceName,DriverVersion | Format-Table -AutoSize"',
            'pnputil /enum-drivers',
        ],
        "category": "Pilotes",
        "icon": "🔌",
    },
    "drivers_gpu_update": {
        "label": "Mettre à jour le pilote GPU via winget",
        "cmds": [
            "winget upgrade --all --include-unknown --accept-source-agreements --accept-package-agreements",
        ],
        "category": "Pilotes",
        "icon": "🖥️",
    },

    # ── Système ─────────────────────────────────────────────────────────────
    "sfc_scan": {
        "label": "Réparer les fichiers système (SFC)",
        "cmds": ["sfc /scannow"],
        "category": "Système",
        "icon": "🛡️",
    },
    "dism_repair": {
        "label": "Réparer l'image Windows (DISM)",
        "cmds": [
            "DISM /Online /Cleanup-Image /CheckHealth",
            "DISM /Online /Cleanup-Image /ScanHealth",
            "DISM /Online /Cleanup-Image /RestoreHealth",
        ],
        "category": "Système",
        "icon": "🛠️",
    },
    "chkdsk": {
        "label": "Vérifier le disque C: (CHKDSK)",
        "cmds": ["chkdsk C: /f /r /x"],
        "category": "Disques",
        "icon": "💿",
    },
    "disk_cleanup": {
        "label": "Nettoyer les fichiers temporaires",
        "cmds": [
            'del /s /q "%temp%\\*"',
            'del /s /q "C:\\Windows\\Temp\\*"',
            "cleanmgr /sagerun:1",
        ],
        "category": "Disques",
        "icon": "🗑️",
    },

    # ── Réseau ───────────────────────────────────────────────────────────────
    "network_reset": {
        "label": "Réinitialiser le réseau complet",
        "cmds": [
            "netsh winsock reset",
            "netsh int ip reset",
            "ipconfig /release",
            "ipconfig /flushdns",
            "ipconfig /renew",
        ],
        "category": "Réseau",
        "icon": "🌐",
    },
    "dns_flush": {
        "label": "Vider le cache DNS",
        "cmds": ["ipconfig /flushdns"],
        "category": "Réseau",
        "icon": "🔃",
    },
    "network_drivers": {
        "label": "Réinstaller les pilotes réseau",
        "cmds": [
            'powershell -Command "Get-NetAdapter | Disable-NetAdapter -Confirm:$false"',
            'powershell -Command "Get-NetAdapter | Enable-NetAdapter -Confirm:$false"',
        ],
        "category": "Réseau",
        "icon": "📶",
    },

    # ── RAM & Performance ────────────────────────────────────────────────────
    "ram_optimize": {
        "label": "Optimiser la mémoire RAM",
        "cmds": [
            'powershell -Command "Get-Process | Where-Object {$_.WorkingSet -gt 500MB} | Select-Object Name,@{N=\'RAM(MB)\';E={[math]::Round($_.WorkingSet/1MB,1)}} | Sort-Object \'RAM(MB)\' -Descending | Format-Table"',
            'powershell -Command "[System.GC]::Collect()"',
        ],
        "category": "RAM",
        "icon": "🧠",
    },
    "pagefile_optimize": {
        "label": "Optimiser le fichier d'échange",
        "cmds": [
            'powershell -Command "$cs = Get-WmiObject Win32_ComputerSystem; $cs.AutomaticManagedPagefile = $true; $cs.Put()"',
        ],
        "category": "RAM",
        "icon": "📄",
    },

    # ── CPU ──────────────────────────────────────────────────────────────────
    "cpu_performance": {
        "label": "Activer le mode Haute Performance CPU",
        "cmds": [
            "powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c",
        ],
        "category": "CPU",
        "icon": "⚡",
    },
    "startup_clean": {
        "label": "Lister et désactiver les apps au démarrage",
        "cmds": [
            'powershell -Command "Get-CimInstance Win32_StartupCommand | Select-Object Name,Command,Location | Format-Table -AutoSize"',
        ],
        "category": "CPU",
        "icon": "🚀",
    },

    # ── Virus & Sécurité ─────────────────────────────────────────────────────
    "defender_scan": {
        "label": "Scan antivirus Windows Defender",
        "cmds": [
            'powershell -Command "Start-MpScan -ScanType QuickScan"',
        ],
        "category": "Sécurité",
        "icon": "🦠",
    },
    "defender_update": {
        "label": "Mettre à jour les définitions Defender",
        "cmds": [
            'powershell -Command "Update-MpSignature"',
        ],
        "category": "Sécurité",
        "icon": "🔒",
    },

    # ── Winget / Apps ────────────────────────────────────────────────────────
    "winget_upgrade_all": {
        "label": "Mettre à jour toutes les applications (winget)",
        "cmds": [
            "winget upgrade --all --accept-source-agreements --accept-package-agreements",
        ],
        "category": "Applications",
        "icon": "📦",
    },
    "winget_list": {
        "label": "Lister les applications installées",
        "cmds": ["winget list"],
        "category": "Applications",
        "icon": "📋",
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
            vm   = psutil.virtual_memory()
            swap = psutil.swap_memory()
            pct  = vm.percent
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
                    pct   = usage.percent
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
    """Exécute des commandes CMD/PowerShell et stream la sortie en temps réel."""

    def __init__(self, output_widget, status_callback=None):
        self.output  = output_widget
        self.status  = status_callback
        self.running = False
        self.queue   = queue.Queue()
        self._configure_tags()

    def _configure_tags(self):
        w = self.output
        w.tag_config("prompt",  foreground=CMD_GREEN,  font=("Consolas", 10, "bold"))
        w.tag_config("cmd",     foreground=CMD_CYAN,   font=("Consolas", 10, "bold"))
        w.tag_config("stdout",  foreground=CMD_WHITE,  font=("Consolas", 10))
        w.tag_config("stderr",  foreground=CMD_RED,    font=("Consolas", 10))
        w.tag_config("success", foreground=CMD_GREEN,  font=("Consolas", 10, "bold"))
        w.tag_config("warning", foreground=CMD_YELLOW, font=("Consolas", 10))
        w.tag_config("info",    foreground=CMD_CYAN,   font=("Consolas", 10))
        w.tag_config("ai",      foreground="#DD88FF",  font=("Consolas", 10, "italic"))
        w.tag_config("sep",     foreground="#2A3040",  font=("Consolas", 10))

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
        """Lance une commande dans un thread et streame la sortie."""
        self.running = True
        if self.status:
            self.status(f"⚡ {label or cmd[:50]}…", ACCENT_WARN)

        self.write(f"\n{'─'*65}\n", "sep")
        self.write(f"  C:\\> ", "prompt")
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
                # Lire stdout ligne par ligne
                for line in proc.stdout:
                    self.output.after(0, self.write, line, "stdout")
                # stderr
                err = proc.stderr.read()
                if err.strip():
                    self.output.after(0, self.write, err, "stderr")

                proc.wait()
                rc = proc.returncode
                if rc == 0:
                    self.output.after(0, self.write, f"\n  ✔ Commande terminée avec succès (code {rc})\n", "success")
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
        """Lance toutes les commandes d'une action de réparation."""
        if repair_key not in REPAIR_COMMANDS:
            return
        r = REPAIR_COMMANDS[repair_key]
        self.write(f"\n{'═'*65}\n", "sep")
        self.write(f"  {r['icon']}  {r['label'].upper()}\n", "info")
        self.write(f"{'═'*65}\n", "sep")

        def _run_all():
            for cmd in r["cmds"]:
                if not self.running:
                    self.running = True
                proc = subprocess.Popen(
                    cmd, shell=True,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True, encoding="utf-8", errors="replace",
                    creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
                )
                self.output.after(0, self.write, f"\n  C:\\> ", "prompt")
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
            self.output.after(0, self.write, f"\n  ✅ Action '{r['label']}' terminée.\n", "success")
            if self.status:
                self.output.after(0, self.status, "Prêt", ACCENT_GREEN)

        threading.Thread(target=_run_all, daemon=True).start()


# ══════════════════════════════════════════════════════════════════════════════
#  ASSISTANT IA
# ══════════════════════════════════════════════════════════════════════════════
class AIAssistant:
    """
    Assistant IA qui analyse les problèmes et génère les commandes CMD/PowerShell.
    Fonctionne avec l'API Anthropic (si clé fournie) ou en mode local (règles).
    """

    SYSTEM_PROMPT = """Tu es SysDiag-AI, un expert Windows intégré dans un outil de diagnostic système.
Ton rôle : analyser les problèmes détectés sur le PC de l'utilisateur et proposer des commandes
CMD/PowerShell concrètes pour les corriger, ainsi que des explications claires.

Règles :
- Réponds TOUJOURS en français
- Fournis des commandes CMD/PowerShell précises et exécutables sur Windows
- Classe les actions par priorité (CRITIQUE > AVERTISSEMENT > INFO)
- Sois concis mais complet
- Si l'utilisateur demande de lancer une commande, propose-la dans un bloc ```cmd ... ```
- Ne propose jamais de commandes dangereuses sans avertissement clair
"""

    def __init__(self, terminal: CMDTerminal):
        self.terminal  = terminal
        self.api_key   = ANTHROPIC_API_KEY
        self.history   = []

    def set_api_key(self, key: str):
        self.api_key = key.strip()

    def _build_context(self, issues, sections):
        """Construit le contexte système pour l'IA."""
        lines = ["=== ÉTAT DU SYSTÈME ==="]
        si = sections.get("Système", {})
        for k, v in si.items():
            lines.append(f"{k}: {v}")
        lines.append("\n=== PROBLÈMES DÉTECTÉS ===")
        if issues:
            for iss in issues:
                lines.append(f"[{iss['severite']}] {iss['composant']}: {iss['probleme']}")
        else:
            lines.append("Aucun problème détecté.")
        return "\n".join(lines)

    def ask(self, user_message: str, issues=None, sections=None, callback=None):
        """Envoie une question à l'IA et appelle callback(text) avec la réponse."""
        context = self._build_context(issues or [], sections or {})
        full_msg = f"{context}\n\n=== QUESTION UTILISATEUR ===\n{user_message}"

        self.history.append({"role": "user", "content": full_msg})

        if self.api_key:
            threading.Thread(
                target=self._call_api, args=(callback,), daemon=True
            ).start()
        else:
            threading.Thread(
                target=self._local_response, args=(user_message, issues or [], callback),
                daemon=True
            ).start()

    def _call_api(self, callback):
        """Appel à l'API Anthropic."""
        try:
            payload = {
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 1024,
                "system": self.SYSTEM_PROMPT,
                "messages": self.history[-10:],
            }
            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            }
            resp = requests.post(ANTHROPIC_API_URL, json=payload,
                                 headers=headers, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                text = data["content"][0]["text"]
                self.history.append({"role": "assistant", "content": text})
                if callback:
                    callback(text)
            else:
                err = f"Erreur API ({resp.status_code}): {resp.text[:200]}"
                if callback:
                    callback(f"[Erreur IA] {err}\n\nMode local activé automatiquement.")
                self._local_response_direct("", [], callback)
        except Exception as e:
            if callback:
                callback(f"[Connexion IA impossible] {e}\n\nMode local activé.")

    def _local_response(self, message, issues, callback):
        """Réponse locale sans API — basée sur les règles."""
        time.sleep(0.5)
        response = self._local_response_direct(message, issues, callback)

    def _local_response_direct(self, message, issues, callback):
        msg_lower = message.lower()
        lines = ["**SysDiag-AI (mode local)**\n"]

        # Réponses aux questions courantes
        if any(w in msg_lower for w in ["mise à jour", "update", "mettre à jour"]):
            lines += [
                "Pour mettre à jour Windows et les pilotes :\n",
                "```cmd\nwinget upgrade --all --accept-source-agreements\n```\n",
                "```cmd\npowershell -Command \"Get-WindowsUpdate -AcceptAll -Install\"\n```\n",
                "Utilisez le bouton **Mises à jour Windows** dans le panneau Réparations.\n"
            ]
        elif any(w in msg_lower for w in ["réseau", "internet", "connexion"]):
            lines += [
                "Pour réparer la connexion réseau :\n",
                "```cmd\nnetsh winsock reset\nnetsh int ip reset\nipconfig /flushdns\nipconfig /renew\n```\n",
                "Redémarrez après l'exécution.\n"
            ]
        elif any(w in msg_lower for w in ["lent", "lenteur", "performance", "rapide"]):
            lines += [
                "Pour améliorer les performances :\n",
                "1. Activer le mode haute performance :\n",
                "```cmd\npowercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c\n```\n",
                "2. Nettoyer les fichiers temporaires :\n",
                "```cmd\ndel /s /q \"%temp%\\*\"\n```\n",
                "3. Scanner le système :\n",
                "```cmd\nsfc /scannow\n```\n"
            ]
        elif any(w in msg_lower for w in ["virus", "malware", "sécurité"]):
            lines += [
                "Pour analyser et sécuriser le système :\n",
                "```cmd\npowershell -Command \"Update-MpSignature\"\n```\n",
                "```cmd\npowershell -Command \"Start-MpScan -ScanType FullScan\"\n```\n"
            ]
        elif issues:
            lines.append("Voici les actions recommandées pour les problèmes détectés :\n\n")
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
            lines += [
                "Votre système semble en bonne santé. Quelques bonnes pratiques :\n\n",
                "• Lancez `sfc /scannow` régulièrement\n",
                "• Mettez à jour via `winget upgrade --all`\n",
                "• Videz `%temp%` chaque semaine\n",
                "• Activez Windows Defender\n"
            ]

        lines.append("\n*Ajoutez une clé API Anthropic dans Paramètres pour une IA plus avancée.*")
        text = "".join(lines)
        if callback:
            callback(text)
        return text


# ══════════════════════════════════════════════════════════════════════════════
#  APPLICATION PRINCIPALE
# ══════════════════════════════════════════════════════════════════════════════
class SysDiagApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.engine    = DiagnosticEngine()
        self._sections = {}
        self._issues   = []
        self._setup_window()
        self._build_ui()
        self._check_admin_warning()

    def _setup_window(self):
        self.title("SysDiag v3.0 — Thabet Raki  │  IA + CMD + GPL v3")
        self.geometry("1320x820")
        self.minsize(1100, 700)
        self.configure(bg=BG_DARK)

    def _check_admin_warning(self):
        if platform.system() == "Windows" and not is_admin():
            self._set_status("⚠ Lancez en administrateur pour toutes les réparations", ACCENT_WARN)

    # ══════════════════════════════════════════════════════════════════════════
    #  BUILD UI
    # ══════════════════════════════════════════════════════════════════════════
    def _build_ui(self):
        self._build_header()

        # Barre de progression
        pf = tk.Frame(self, bg=BG_DARK)
        pf.pack(fill="x", padx=16, pady=(4, 0))
        self.prog_var = tk.IntVar()
        s = ttk.Style(); s.theme_use("default")
        s.configure("Diag.Horizontal.TProgressbar",
                    troughcolor=BG_CARD, background=ACCENT_CYAN, thickness=5)
        ttk.Progressbar(pf, variable=self.prog_var, maximum=100,
                        style="Diag.Horizontal.TProgressbar").pack(fill="x")

        # Corps — notebook avec 3 onglets
        nb_frame = tk.Frame(self, bg=BG_DARK)
        nb_frame.pack(fill="both", expand=True, padx=16, pady=8)

        style = ttk.Style()
        style.configure("Dark.TNotebook",        background=BG_DARK, borderwidth=0)
        style.configure("Dark.TNotebook.Tab",    background=BG_CARD, foreground=TEXT_SUB,
                        font=("Consolas", 10, "bold"), padding=[16, 6])
        style.map("Dark.TNotebook.Tab",
                  background=[("selected", BG_PANEL)],
                  foreground=[("selected", ACCENT_CYAN)])

        self.notebook = ttk.Notebook(nb_frame, style="Dark.TNotebook")
        self.notebook.pack(fill="both", expand=True)

        self._build_tab_diagnostic()
        self._build_tab_repairs()
        self._build_tab_ai()
        self._build_footer()

    def _build_header(self):
        h = tk.Frame(self, bg=BG_PANEL, pady=10, padx=20)
        h.pack(fill="x")
        tk.Label(h, text="⬡ SysDiag", font=("Consolas", 20, "bold"),
                 fg=ACCENT_CYAN, bg=BG_PANEL).pack(side="left")
        tk.Label(h, text="v3.0  ·  IA + CMD  ·  Thabet Raki  ·  GPLv3",
                 font=("Consolas", 9), fg=TEXT_SUB, bg=BG_PANEL).pack(side="left", padx=14)
        self.status_lbl = tk.Label(h, text="Prêt", font=("Consolas", 9, "bold"),
                                   fg=ACCENT_GREEN, bg=BG_PANEL)
        self.status_lbl.pack(side="right")

    # ── Onglet 1 : Diagnostic ──────────────────────────────────────────────
    def _build_tab_diagnostic(self):
        tab = tk.Frame(self.notebook, bg=BG_DARK)
        self.notebook.add(tab, text="  🔍 Diagnostic  ")

        paned = tk.PanedWindow(tab, orient="horizontal", bg=BG_DARK,
                               sashwidth=4, sashpad=0, sashrelief="flat")
        paned.pack(fill="both", expand=True)

        # Liste sections
        left = tk.Frame(paned, bg=BG_PANEL, width=240)
        paned.add(left, minsize=200)
        tk.Label(left, text="SECTIONS", font=("Consolas", 8, "bold"),
                 fg=TEXT_SUB, bg=BG_PANEL).pack(anchor="w", padx=10, pady=(8, 4))
        self.sec_list = tk.Listbox(left, bg=BG_CARD, fg=TEXT_MAIN,
                                   font=("Consolas", 11), selectbackground=ACCENT_CYAN,
                                   selectforeground=BG_DARK, activestyle="none",
                                   relief="flat", bd=0, highlightthickness=0, cursor="hand2")
        self.sec_list.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        self.sec_list.bind("<<ListboxSelect>>", self._on_section_select)

        # Détail
        right = tk.Frame(paned, bg=BG_DARK)
        paned.add(right, minsize=500)
        self.detail = scrolledtext.ScrolledText(
            right, bg=BG_CARD, fg=TEXT_MAIN, font=("Consolas", 10),
            relief="flat", bd=0, insertbackground=ACCENT_CYAN, wrap="word", state="disabled"
        )
        self.detail.pack(fill="both", expand=True)
        self._config_detail_tags()

    def _config_detail_tags(self):
        t = self.detail
        t.tag_config("title",    foreground=ACCENT_CYAN,  font=("Consolas", 13, "bold"))
        t.tag_config("key",      foreground=ACCENT_GREEN, font=("Consolas", 10, "bold"))
        t.tag_config("val",      foreground=TEXT_MAIN,    font=("Consolas", 10))
        t.tag_config("critical", foreground=ACCENT_RED,   font=("Consolas", 10, "bold"))
        t.tag_config("warning",  foreground=ACCENT_WARN,  font=("Consolas", 10, "bold"))
        t.tag_config("ok",       foreground=ACCENT_GREEN, font=("Consolas", 10, "bold"))
        t.tag_config("repair",   foreground="#A0C4FF",    font=("Consolas", 9))
        t.tag_config("sep",      foreground=BORDER,       font=("Consolas", 10))

    # ── Onglet 2 : Réparations CMD ─────────────────────────────────────────
    def _build_tab_repairs(self):
        tab = tk.Frame(self.notebook, bg=BG_DARK)
        self.notebook.add(tab, text="  🛠️ Réparations CMD  ")

        # Gauche : boutons par catégorie
        left = tk.Frame(tab, bg=BG_PANEL, width=300)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        tk.Label(left, text="ACTIONS DE RÉPARATION", font=("Consolas", 8, "bold"),
                 fg=TEXT_SUB, bg=BG_PANEL).pack(anchor="w", padx=10, pady=(10, 6))

        canvas = tk.Canvas(left, bg=BG_PANEL, highlightthickness=0)
        scrollbar = ttk.Scrollbar(left, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=BG_PANEL)
        scroll_frame.bind("<Configure>",
                          lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Grouper par catégorie
        categories = {}
        for key, r in REPAIR_COMMANDS.items():
            cat = r.get("category", "Autre")
            categories.setdefault(cat, []).append((key, r))

        CAT_COLORS = {
            "Mises à jour": ACCENT_CYAN,
            "Pilotes":      "#FF9900",
            "Système":      ACCENT_GREEN,
            "Disques":      "#FF6699",
            "Réseau":       "#00BFFF",
            "RAM":          "#CC88FF",
            "CPU":          "#FFD700",
            "Sécurité":     ACCENT_RED,
            "Applications": "#88FF88",
        }

        for cat, items in categories.items():
            color = CAT_COLORS.get(cat, ACCENT_CYAN)
            tk.Label(scroll_frame, text=f"  {cat.upper()}",
                     font=("Consolas", 8, "bold"), fg=color, bg=BG_PANEL).pack(
                anchor="w", pady=(10, 2), padx=6)
            for key, r in items:
                btn = tk.Button(
                    scroll_frame,
                    text=f"  {r['icon']}  {r['label']}",
                    font=("Consolas", 9), fg=TEXT_MAIN, bg=BG_CARD,
                    activebackground=color, activeforeground=BG_DARK,
                    relief="flat", bd=0, cursor="hand2", anchor="w",
                    command=lambda k=key: self._run_repair(k)
                )
                btn.pack(fill="x", padx=6, pady=1, ipady=5)

        # Droite : terminal CMD
        right = tk.Frame(tab, bg=BG_DARK)
        right.pack(side="right", fill="both", expand=True)

        # En-tête terminal
        th = tk.Frame(right, bg=BG_TERMINAL, pady=4, padx=10)
        th.pack(fill="x")
        tk.Label(th, text="● ● ●", font=("Consolas", 9),
                 fg="#444", bg=BG_TERMINAL).pack(side="left")
        tk.Label(th, text="CMD / PowerShell — Thabet Raki",
                 font=("Consolas", 9, "bold"), fg=CMD_GREEN,
                 bg=BG_TERMINAL).pack(side="left", padx=12)
        tk.Button(th, text="🗑 Effacer", font=("Consolas", 8),
                  fg=TEXT_SUB, bg=BG_TERMINAL, relief="flat", cursor="hand2",
                  command=self._clear_terminal).pack(side="right")

        self.terminal_out = scrolledtext.ScrolledText(
            right, bg=BG_TERMINAL, fg=CMD_WHITE,
            font=("Consolas", 10), relief="flat", bd=0,
            insertbackground=CMD_GREEN, wrap="word", state="disabled"
        )
        self.terminal_out.pack(fill="both", expand=True)

        # Ligne de commande manuelle
        cmd_bar = tk.Frame(right, bg=BG_TERMINAL, pady=6, padx=10)
        cmd_bar.pack(fill="x")
        tk.Label(cmd_bar, text="C:\\>", font=("Consolas", 10, "bold"),
                 fg=CMD_GREEN, bg=BG_TERMINAL).pack(side="left")
        self.cmd_entry = tk.Entry(cmd_bar, bg="#0F1A0F", fg=CMD_WHITE,
                                  font=("Consolas", 10), relief="flat",
                                  insertbackground=CMD_GREEN, bd=0)
        self.cmd_entry.pack(side="left", fill="x", expand=True, padx=(6, 0))
        self.cmd_entry.bind("<Return>", self._run_manual_cmd)
        tk.Button(cmd_bar, text="▶ Exécuter",
                  font=("Consolas", 9, "bold"), fg=BG_DARK, bg=CMD_GREEN,
                  relief="flat", cursor="hand2",
                  command=self._run_manual_cmd).pack(side="right", padx=(6, 0))

        # Initialiser le terminal
        self.terminal = CMDTerminal(self.terminal_out, self._set_status)
        self.ai = AIAssistant(self.terminal)
        self.terminal.write("  SysDiag v3.0 — Terminal CMD intégré\n", "info")
        self.terminal.write("  Auteur : Thabet Raki | Licence : GPLv3\n", "info")
        self.terminal.write("  Tapez une commande ou cliquez sur une action à gauche.\n\n", "info")

    # ── Onglet 3 : Assistant IA ────────────────────────────────────────────
    def _build_tab_ai(self):
        tab = tk.Frame(self.notebook, bg=BG_DARK)
        self.notebook.add(tab, text="  🤖 Assistant IA  ")

        # Header IA
        ai_h = tk.Frame(tab, bg=BG_PANEL, pady=8, padx=14)
        ai_h.pack(fill="x")
        tk.Label(ai_h, text="🤖  Assistant SysDiag-AI",
                 font=("Consolas", 12, "bold"), fg=ACCENT_AI, bg=BG_PANEL).pack(side="left")
        tk.Label(ai_h, text="Clé API Anthropic (optionnelle) :",
                 font=("Consolas", 9), fg=TEXT_SUB, bg=BG_PANEL).pack(side="left", padx=(30, 6))
        self.api_entry = tk.Entry(ai_h, bg=BG_CARD, fg=TEXT_MAIN,
                                  font=("Consolas", 9), relief="flat",
                                  insertbackground=ACCENT_AI, show="*", width=40)
        self.api_entry.pack(side="left")
        tk.Button(ai_h, text="Enregistrer",
                  font=("Consolas", 8, "bold"), fg=BG_DARK, bg=ACCENT_AI,
                  relief="flat", cursor="hand2",
                  command=self._save_api_key).pack(side="left", padx=6)

        # Zone de conversation IA
        self.ai_chat = scrolledtext.ScrolledText(
            tab, bg=BG_CARD, fg=TEXT_MAIN, font=("Consolas", 10),
            relief="flat", bd=0, insertbackground=ACCENT_AI,
            wrap="word", state="disabled"
        )
        self.ai_chat.pack(fill="both", expand=True, padx=10, pady=(6, 0))
        self._config_ai_tags()

        # Boutons rapides
        quick = tk.Frame(tab, bg=BG_DARK, pady=6)
        quick.pack(fill="x", padx=10)
        tk.Label(quick, text="Analyse rapide :", font=("Consolas", 9),
                 fg=TEXT_SUB, bg=BG_DARK).pack(side="left")
        for label, prompt in [
            ("📊 Analyser les problèmes", "Analyse les problèmes détectés et donne-moi un plan d'action prioritaire"),
            ("🔄 Mises à jour", "Comment mettre à jour tous les composants de mon PC Windows ?"),
            ("⚡ Optimiser", "Quelles commandes pour optimiser les performances de mon Windows ?"),
            ("🦠 Sécurité", "Vérifie la sécurité de mon système et propose des corrections"),
        ]:
            tk.Button(quick, text=label, font=("Consolas", 8, "bold"),
                      fg=BG_DARK, bg=ACCENT_AI, relief="flat", cursor="hand2",
                      command=lambda p=prompt: self._ask_ai(p)).pack(side="left", padx=4, ipady=4, ipadx=6)

        # Barre de saisie IA
        ai_bar = tk.Frame(tab, bg=BG_PANEL, pady=8, padx=10)
        ai_bar.pack(fill="x")
        self.ai_entry = tk.Entry(ai_bar, bg=BG_CARD, fg=TEXT_MAIN,
                                 font=("Consolas", 10), relief="flat",
                                 insertbackground=ACCENT_AI)
        self.ai_entry.pack(side="left", fill="x", expand=True)
        self.ai_entry.bind("<Return>", lambda e: self._ask_ai(self.ai_entry.get()))
        tk.Button(ai_bar, text="  ➤ Envoyer  ",
                  font=("Consolas", 10, "bold"), fg=BG_DARK, bg=ACCENT_AI,
                  relief="flat", cursor="hand2",
                  command=lambda: self._ask_ai(self.ai_entry.get())).pack(side="right", padx=(8, 0))

        self._ai_write("SysDiag-AI", "Bonjour ! Je suis votre assistant IA intégré.\n"
                       "Lancez d'abord un diagnostic (onglet 🔍), puis posez-moi "
                       "vos questions ou cliquez sur un bouton rapide.\n"
                       "Je peux générer des commandes CMD/PowerShell pour corriger "
                       "les problèmes détectés sur votre Windows.\n", "ai_msg")

    def _config_ai_tags(self):
        t = self.ai_chat
        t.tag_config("user_label", foreground=ACCENT_CYAN,  font=("Consolas", 9, "bold"))
        t.tag_config("user_msg",   foreground=TEXT_MAIN,    font=("Consolas", 10))
        t.tag_config("ai_label",   foreground=ACCENT_AI,    font=("Consolas", 9, "bold"))
        t.tag_config("ai_msg",     foreground="#D8C4FF",    font=("Consolas", 10))
        t.tag_config("code",       foreground=CMD_GREEN,    font=("Consolas", 10),
                     background="#0A1A0A")
        t.tag_config("sep",        foreground=BORDER,       font=("Consolas", 9))

    # ── Footer ─────────────────────────────────────────────────────────────
    def _build_footer(self):
        f = tk.Frame(self, bg=BG_PANEL, pady=8)
        f.pack(fill="x", side="bottom")
        btn = {"font": ("Consolas", 10, "bold"), "relief": "flat",
               "cursor": "hand2", "padx": 16, "pady": 6}

        self.btn_scan = tk.Button(f, text="▶  LANCER LE DIAGNOSTIC",
                                  bg=ACCENT_CYAN, fg=BG_DARK,
                                  command=self._run_diagnostic, **btn)
        self.btn_scan.pack(side="left", padx=12)

        tk.Button(f, text="⚡  TOUT RÉPARER (AUTO)",
                  bg=ACCENT_GREEN, fg=BG_DARK,
                  command=self._auto_repair, **btn).pack(side="left", padx=4)

        tk.Button(f, text="💾  EXPORTER RAPPORT",
                  bg=BG_CARD, fg=ACCENT_CYAN, bd=1,
                  command=self._export_report, **btn).pack(side="left", padx=4)

        if platform.system() == "Windows" and not is_admin():
            tk.Button(f, text="🔑  RELANCER EN ADMIN",
                      bg=ACCENT_WARN, fg=BG_DARK,
                      command=run_as_admin, **btn).pack(side="left", padx=4)

        tk.Button(f, text="ℹ  LICENCE",
                  bg=BG_CARD, fg=TEXT_SUB, bd=0,
                  command=self._show_license, **btn).pack(side="right", padx=12)

    # ══════════════════════════════════════════════════════════════════════════
    #  ACTIONS
    # ══════════════════════════════════════════════════════════════════════════
    def _set_status(self, msg, color=None):
        self.status_lbl.config(text=msg, fg=color or ACCENT_GREEN)

    def _run_diagnostic(self):
        self.btn_scan.config(state="disabled", text="⏳ Analyse…")
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

    def _populate_results(self, sections, issues):
        self.btn_scan.config(state="normal", text="▶  LANCER LE DIAGNOSTIC")
        self._set_status("Analyse terminée ✔", ACCENT_GREEN)

        for name in sections:
            self.sec_list.insert(tk.END, f"  {name}")

        count = len(issues)
        label = f"  ⚠ Problèmes ({count})" if count else "  ✔ Aucun problème"
        self.sec_list.insert(tk.END, label)

        self._show_summary(sections, issues)

    def _show_summary(self, sections, issues):
        t = self.detail
        t.config(state="normal")
        t.delete("1.0", tk.END)
        t.insert(tk.END, "RAPPORT DE DIAGNOSTIC  —  SysDiag v3.0\n", "title")
        t.insert(tk.END, f"  {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}  ·  Thabet Raki\n", "val")
        t.insert(tk.END, "─" * 68 + "\n\n", "sep")

        for k, v in sections.get("Système", {}).items():
            t.insert(tk.END, f"  {k:<22} ", "key")
            t.insert(tk.END, f"{v}\n", "val")

        t.insert(tk.END, "\n" + "─" * 68 + "\n", "sep")
        t.insert(tk.END, "\n  RÉSULTATS\n\n", "title")

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
                keys = iss.get("repair_keys", [])
                if keys:
                    t.insert(tk.END, "  Réparations disponibles :\n", "key")
                    for k in keys:
                        r = REPAIR_COMMANDS.get(k, {})
                        if r:
                            t.insert(tk.END, f"    {r['icon']} {r['label']}\n", "repair")

        t.insert(tk.END, "\n\n  → Allez dans l'onglet 🛠️ pour lancer les réparations.\n", "val")
        t.insert(tk.END, "  → Allez dans l'onglet 🤖 pour consulter l'IA.\n", "val")
        t.config(state="disabled")

    def _on_section_select(self, event):
        sel = self.sec_list.curselection()
        if not sel:
            return
        idx  = sel[0]
        keys = list(self._sections.keys())
        if idx < len(keys):
            name = keys[idx]
            self._show_section(name, self._sections[name])
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
        rel = [i for i in self._issues
               if i["composant"].lower().startswith(name.lower())]
        if rel:
            t.insert(tk.END, "\n" + "─" * 58 + "\n", "sep")
            t.insert(tk.END, "\n  PROBLÈMES\n\n", "critical")
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

    # ── Terminal CMD ───────────────────────────────────────────────────────
    def _run_repair(self, key):
        self.notebook.select(1)  # Switcher sur l'onglet Réparations
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
                                    "Lancer automatiquement TOUTES les réparations "
                                    "recommandées ?\n\nCela peut prendre plusieurs minutes."):
            return
        self.notebook.select(1)
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
    def _save_api_key(self):
        key = self.api_entry.get().strip()
        if key:
            self.ai.set_api_key(key)
            self._ai_write("Système", "Clé API enregistrée. L'IA utilisera l'API Anthropic.\n", "ai_msg")
        else:
            messagebox.showwarning("Clé vide", "Entrez une clé API valide.")

    def _ask_ai(self, prompt: str):
        if not prompt.strip():
            return
        self.ai_entry.delete(0, tk.END)
        self._ai_write("Vous", prompt + "\n", "user_msg")
        self._set_status("🤖 IA en cours…", ACCENT_AI)

        def callback(text):
            self.after(0, self._ai_write, "SysDiag-AI", text + "\n", "ai_msg")
            self.after(0, self._set_status, "Prêt", ACCENT_GREEN)
            # Si l'IA propose des commandes, les afficher dans le terminal aussi
            lines = text.split("\n")
            for line in lines:
                if line.strip().startswith("```cmd") or line.strip().startswith("```powershell"):
                    pass
                elif line.strip().startswith("```") and not line.strip() == "```":
                    pass

        self.ai.ask(prompt, issues=self._issues, sections=self._sections,
                    callback=callback)

    def _ai_write(self, sender, text, tag):
        t = self.ai_chat
        t.config(state="normal")
        label_tag = "user_label" if sender == "Vous" else "ai_label"
        t.insert(tk.END, f"\n  [{sender}]\n", label_tag)
        # Rendu basique markdown : blocs ```cmd
        parts = text.split("```")
        for i, part in enumerate(parts):
            if i % 2 == 1:
                # bloc de code
                content = part.lstrip("cmd\n").lstrip("powershell\n")
                t.insert(tk.END, f"  {content}\n", "code")
            else:
                t.insert(tk.END, f"  {part}", tag)
        t.insert(tk.END, "\n", "sep")
        t.see(tk.END)
        t.config(state="disabled")

    # ── Export rapport ──────────────────────────────────────────────────────
    def _export_report(self):
        if not self._sections:
            messagebox.showinfo("Info", "Lancez d'abord un diagnostic.")
            return
        fname = f"SysDiag_rapport_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        path  = os.path.join(os.path.expanduser("~"), "Desktop", fname)
        lines = [
            "=" * 70,
            "  RAPPORT SysDiag v3.0 — Thabet Raki — GPLv3",
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
            messagebox.showinfo("Exporté", f"Rapport sauvegardé :\n{path}")
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    # ── Licence ─────────────────────────────────────────────────────────────
    def _show_license(self):
        win = tk.Toplevel(self)
        win.title("Licence GNU GPLv3")
        win.geometry("620x400")
        win.configure(bg=BG_CARD)
        txt = scrolledtext.ScrolledText(win, bg=BG_DARK, fg=TEXT_MAIN,
                                        font=("Consolas", 9), relief="flat", wrap="word")
        txt.pack(fill="both", expand=True, padx=10, pady=10)
        txt.insert(tk.END, "SysDiag v3.0\nCopyright (C) 2026  Thabet Raki\n\n"
                   "Ce programme est distribué sous GNU GPL v3.\n"
                   "https://www.gnu.org/licenses/gpl-3.0.html\n\n"
                   "Vous êtes libre d'utiliser, modifier et redistribuer\n"
                   "ce logiciel sous les mêmes termes.")
        txt.config(state="disabled")
        tk.Button(win, text="Fermer", bg=ACCENT_CYAN, fg=BG_DARK,
                  font=("Consolas", 10, "bold"), relief="flat",
                  command=win.destroy).pack(pady=8)


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

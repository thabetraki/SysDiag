#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          SysDiag - Outil de Diagnostic Système Avancé                       ║
║                                                                              ║
║  Copyright (C) 2026  Thabet Raki                                             ║
║                                                                              ║
║  Ce programme est un logiciel libre : vous pouvez le redistribuer et/ou     ║
║  le modifier selon les termes de la Licence Publique Générale GNU telle     ║
║  que publiée par la Free Software Foundation, soit la version 3 de la       ║
║  Licence, soit (à votre option) toute version ultérieure.                   ║
║                                                                              ║
║  Ce programme est distribué dans l'espoir qu'il sera utile,                 ║
║  mais SANS AUCUNE GARANTIE ; sans même la garantie implicite de             ║
║  COMMERCIALISABILITÉ ou d'ADÉQUATION À UN USAGE PARTICULIER.               ║
║  Voir la Licence Publique Générale GNU pour plus de détails.                ║
║                                                                              ║
║  Vous devriez avoir reçu une copie de la GNU General Public License        ║
║  avec ce programme. Sinon, voir <https://www.gnu.org/licenses/>.           ║
╚══════════════════════════════════════════════════════════════════════════════╝

SysDiag - System Diagnostic Tool
Auteur   : Thabet Raki
Version  : 2.0.0
Licence  : GNU General Public License v3 (GPLv3)
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import platform
import psutil
import os
import sys
import threading
import datetime
import shutil
import json
import socket
import time

# ─── Palette de couleurs ───────────────────────────────────────────────────────
BG_DARK      = "#0D0F14"
BG_PANEL     = "#141720"
BG_CARD      = "#1A1E2E"
ACCENT_CYAN  = "#00E5FF"
ACCENT_GREEN = "#00FF88"
ACCENT_RED   = "#FF4466"
ACCENT_WARN  = "#FFB300"
TEXT_MAIN    = "#E8EAF0"
TEXT_SUB     = "#6B7280"
BORDER       = "#2A2F45"

# ══════════════════════════════════════════════════════════════════════════════
#  MOTEUR DE DIAGNOSTIC
# ══════════════════════════════════════════════════════════════════════════════
class DiagnosticEngine:
    """Analyse le système et collecte toutes les informations de défaillances."""

    def __init__(self):
        self.results = []
        self.solutions = []

    # ── Infos système ──────────────────────────────────────────────────────────
    def get_system_info(self):
        info = {
            "OS"          : f"{platform.system()} {platform.release()} ({platform.version()})",
            "Architecture": platform.machine(),
            "Processeur"  : platform.processor() or "N/A",
            "Nom Machine" : platform.node(),
            "Python"      : platform.python_version(),
        }
        try:
            info["RAM Totale"] = f"{psutil.virtual_memory().total / (1024**3):.2f} Go"
        except Exception:
            info["RAM Totale"] = "N/A"
        return info

    # ── CPU ────────────────────────────────────────────────────────────────────
    def check_cpu(self):
        issues = []
        try:
            cpu_pct = psutil.cpu_percent(interval=1)
            freq    = psutil.cpu_freq()
            cores   = psutil.cpu_count(logical=False)
            threads = psutil.cpu_count(logical=True)

            if cpu_pct > 90:
                issues.append({
                    "composant" : "CPU",
                    "severite"  : "CRITIQUE",
                    "probleme"  : f"Utilisation CPU critique : {cpu_pct:.1f}%",
                    "solutions" : [
                        "Ouvrir le Gestionnaire des tâches et fermer les processus inutiles",
                        "Vérifier la présence de malwares (antivirus complet)",
                        "Désactiver les applications au démarrage",
                        "Vérifier le refroidissement (pâte thermique, ventilateurs)",
                        "Augmenter la RAM si swap excessif",
                    ]
                })
            elif cpu_pct > 70:
                issues.append({
                    "composant" : "CPU",
                    "severite"  : "AVERTISSEMENT",
                    "probleme"  : f"Utilisation CPU élevée : {cpu_pct:.1f}%",
                    "solutions" : [
                        "Surveiller les processus consommateurs via le gestionnaire des tâches",
                        "Planifier les tâches lourdes hors des heures de travail",
                    ]
                })

            if freq and freq.current < freq.max * 0.5:
                issues.append({
                    "composant" : "CPU",
                    "severite"  : "AVERTISSEMENT",
                    "probleme"  : f"Fréquence CPU réduite ({freq.current:.0f} MHz / max {freq.max:.0f} MHz) — Throttling détecté",
                    "solutions" : [
                        "Nettoyer le système de refroidissement (poussière, ventilateurs)",
                        "Renouveler la pâte thermique sur le processeur",
                        "Vérifier l'alimentation (PSU insuffisant ?)",
                        "Désactiver le mode Économie d'énergie Windows",
                        "Mettre à jour le BIOS / firmware",
                    ]
                })

            return {
                "Utilisation"    : f"{cpu_pct:.1f}%",
                "Fréquence"      : f"{freq.current:.0f} MHz" if freq else "N/A",
                "Cœurs physiques": str(cores),
                "Threads logiques": str(threads),
            }, issues

        except Exception as e:
            return {"Erreur": str(e)}, []

    # ── RAM ────────────────────────────────────────────────────────────────────
    def check_ram(self):
        issues = []
        try:
            vm   = psutil.virtual_memory()
            swap = psutil.swap_memory()
            pct  = vm.percent

            if pct > 90:
                issues.append({
                    "composant" : "RAM",
                    "severite"  : "CRITIQUE",
                    "probleme"  : f"RAM saturée : {pct:.1f}% utilisé ({vm.used/(1024**3):.1f}/{vm.total/(1024**3):.1f} Go)",
                    "solutions" : [
                        "Fermer les applications non utilisées immédiatement",
                        "Ajouter de la RAM physique (upgrade matériel)",
                        "Augmenter la taille du fichier d'échange Windows",
                        "Analyser les fuites mémoire avec RAMMap (Sysinternals)",
                        "Désactiver les extensions de navigateur inutiles",
                    ]
                })
            elif pct > 75:
                issues.append({
                    "composant" : "RAM",
                    "severite"  : "AVERTISSEMENT",
                    "probleme"  : f"RAM élevée : {pct:.1f}%",
                    "solutions" : [
                        "Envisager un upgrade RAM",
                        "Limiter les onglets de navigateur ouverts",
                    ]
                })

            if swap.percent > 50:
                issues.append({
                    "composant" : "SWAP",
                    "severite"  : "AVERTISSEMENT",
                    "probleme"  : f"Utilisation swap élevée : {swap.percent:.1f}% — Performance dégradée",
                    "solutions" : [
                        "Augmenter la RAM physique",
                        "Réduire le nombre de processus simultanés",
                        "Déplacer le fichier pagefile sur un SSD rapide",
                    ]
                })

            return {
                "Total"    : f"{vm.total/(1024**3):.2f} Go",
                "Utilisé"  : f"{vm.used/(1024**3):.2f} Go ({pct:.1f}%)",
                "Disponible": f"{vm.available/(1024**3):.2f} Go",
                "Swap"     : f"{swap.used/(1024**3):.2f}/{swap.total/(1024**3):.2f} Go ({swap.percent:.1f}%)",
            }, issues

        except Exception as e:
            return {"Erreur": str(e)}, []

    # ── Disques ────────────────────────────────────────────────────────────────
    def check_disks(self):
        issues = []
        disk_info = {}
        try:
            for part in psutil.disk_partitions(all=False):
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    label = part.device.replace("\\", "").replace(":", "")
                    pct   = usage.percent

                    disk_info[f"Disque {part.device}"] = (
                        f"{usage.used/(1024**3):.1f}/{usage.total/(1024**3):.1f} Go ({pct:.1f}%)"
                    )

                    if pct > 95:
                        issues.append({
                            "composant" : f"Disque {part.device}",
                            "severite"  : "CRITIQUE",
                            "probleme"  : f"Disque presque plein : {pct:.1f}% ({usage.free/(1024**3):.1f} Go libres)",
                            "solutions" : [
                                "Lancer l'outil Nettoyage de disque Windows (cleanmgr)",
                                "Supprimer les fichiers temporaires (%temp%)",
                                "Désinstaller les programmes inutilisés",
                                "Déplacer les fichiers volumineux vers un disque externe",
                                "Activer le Nettoyage automatique dans les Paramètres de stockage",
                                "Utiliser WinDirStat pour identifier les gros fichiers",
                            ]
                        })
                    elif pct > 85:
                        issues.append({
                            "composant" : f"Disque {part.device}",
                            "severite"  : "AVERTISSEMENT",
                            "probleme"  : f"Disque presque plein : {pct:.1f}%",
                            "solutions" : [
                                "Nettoyer les fichiers temporaires régulièrement",
                                "Archiver les anciens projets",
                            ]
                        })
                except PermissionError:
                    pass

            # Vitesse I/O
            io1 = psutil.disk_io_counters()
            time.sleep(0.3)
            io2 = psutil.disk_io_counters()
            if io1 and io2:
                read_mb  = (io2.read_bytes  - io1.read_bytes)  / (1024**2) / 0.3
                write_mb = (io2.write_bytes - io1.write_bytes) / (1024**2) / 0.3
                disk_info["I/O Lecture"] = f"{read_mb:.1f} Mo/s"
                disk_info["I/O Écriture"] = f"{write_mb:.1f} Mo/s"

        except Exception as e:
            disk_info["Erreur"] = str(e)

        return disk_info, issues

    # ── Réseau ─────────────────────────────────────────────────────────────────
    def check_network(self):
        issues = []
        net_info = {}
        try:
            # Connectivité
            try:
                socket.setdefaulttimeout(3)
                socket.create_connection(("8.8.8.8", 53))
                net_info["Connexion Internet"] = "✔ Connecté"
            except OSError:
                net_info["Connexion Internet"] = "✘ Déconnecté"
                issues.append({
                    "composant" : "Réseau",
                    "severite"  : "CRITIQUE",
                    "probleme"  : "Pas de connexion internet détectée",
                    "solutions" : [
                        "Vérifier le câble Ethernet ou le WiFi",
                        "Redémarrer le routeur/box (débrancher 30s)",
                        "Exécuter : netsh winsock reset (Admin)",
                        "Exécuter : ipconfig /release puis ipconfig /renew",
                        "Vérifier les pilotes de la carte réseau",
                        "Désactiver temporairement le pare-feu pour tester",
                    ]
                })

            # Stats réseau
            io = psutil.net_io_counters()
            net_info["Octets reçus"]  = f"{io.bytes_recv/(1024**2):.1f} Mo"
            net_info["Octets envoyés"] = f"{io.bytes_sent/(1024**2):.1f} Mo"
            net_info["Erreurs RX"]    = str(io.errin)
            net_info["Erreurs TX"]    = str(io.errout)

            if io.errin > 1000 or io.errout > 1000:
                issues.append({
                    "composant" : "Réseau",
                    "severite"  : "AVERTISSEMENT",
                    "probleme"  : f"Nombreuses erreurs réseau détectées (RX:{io.errin} / TX:{io.errout})",
                    "solutions" : [
                        "Vérifier le câble réseau (remplacer si endommagé)",
                        "Mettre à jour les pilotes de la carte réseau",
                        "Vérifier la qualité du signal WiFi",
                        "Tester avec un autre port du switch/routeur",
                    ]
                })

            # Interfaces actives
            addrs = psutil.net_if_addrs()
            active = [iface for iface, addrs_list in addrs.items()
                      if any(a.family == socket.AF_INET and not a.address.startswith("127.") for a in addrs_list)]
            net_info["Interfaces actives"] = ", ".join(active) if active else "Aucune"

        except Exception as e:
            net_info["Erreur"] = str(e)

        return net_info, issues

    # ── Processus suspects ────────────────────────────────────────────────────
    def check_processes(self):
        issues = []
        proc_info = {}
        try:
            procs = []
            for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    procs.append(p.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            # Top 5 CPU
            top_cpu = sorted(procs, key=lambda x: x.get('cpu_percent', 0) or 0, reverse=True)[:5]
            top_mem = sorted(procs, key=lambda x: x.get('memory_percent', 0) or 0, reverse=True)[:5]

            proc_info["Nombre total"] = str(len(procs))
            proc_info["Top CPU"] = " | ".join(
                f"{p['name']} ({p.get('cpu_percent',0):.1f}%)" for p in top_cpu[:3]
            )
            proc_info["Top RAM"] = " | ".join(
                f"{p['name']} ({p.get('memory_percent',0):.1f}%)" for p in top_mem[:3]
            )

            # Zombies
            zombies = []
            for p in procs:
                try:
                    if p.get('pid') and psutil.Process(p['pid']).status() == psutil.STATUS_ZOMBIE:
                        zombies.append(p)
                except Exception:
                    pass
            if zombies:
                issues.append({
                    "composant" : "Processus",
                    "severite"  : "AVERTISSEMENT",
                    "probleme"  : f"{len(zombies)} processus zombies détectés",
                    "solutions" : [
                        "Redémarrer le système pour libérer les processus zombies",
                        "Identifier et corriger l'application parente défaillante",
                    ]
                })

        except Exception as e:
            proc_info["Erreur"] = str(e)

        return proc_info, issues

    # ── Logs Windows ──────────────────────────────────────────────────────────
    def check_event_logs(self):
        issues = []
        log_info = {}
        if platform.system() != "Windows":
            log_info["Info"] = "Analyse des journaux d'événements : Windows uniquement"
            return log_info, issues

        try:
            result = subprocess.run(
                ["powershell", "-Command",
                 "Get-EventLog -LogName System -EntryType Error -Newest 10 | "
                 "Select-Object TimeGenerated,Source,Message | ConvertTo-Json"],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0 and result.stdout.strip():
                try:
                    events = json.loads(result.stdout)
                    if isinstance(events, dict):
                        events = [events]
                    log_info["Erreurs système récentes"] = f"{len(events)} erreur(s) trouvée(s)"
                    for ev in events[:3]:
                        src = ev.get("Source", "?")
                        msg = str(ev.get("Message", ""))[:80]
                        issues.append({
                            "composant" : "Journal Windows",
                            "severite"  : "AVERTISSEMENT",
                            "probleme"  : f"[{src}] {msg}...",
                            "solutions" : [
                                "Rechercher l'ID de l'événement sur https://learn.microsoft.com",
                                "Mettre à jour les pilotes associés à la source",
                                "Exécuter 'sfc /scannow' pour réparer les fichiers système",
                                "Exécuter 'DISM /Online /Cleanup-Image /RestoreHealth'",
                            ]
                        })
                except json.JSONDecodeError:
                    log_info["Info"] = "Journaux récupérés (format brut)"
            else:
                log_info["Journaux système"] = "Aucune erreur récente détectée ✔"

        except Exception as e:
            log_info["Journaux"] = f"Accès limité : {str(e)}"

        return log_info, issues

    # ── Diagnostic complet ────────────────────────────────────────────────────
    def run_full_diagnostic(self, progress_callback=None):
        all_issues   = []
        all_sections = {}

        steps = [
            ("Système",    self.get_system_info,   None),
            ("CPU",        self.check_cpu,          None),
            ("RAM",        self.check_ram,          None),
            ("Disques",    self.check_disks,        None),
            ("Réseau",     self.check_network,      None),
            ("Processus",  self.check_processes,    None),
            ("Journaux",   self.check_event_logs,   None),
        ]

        for i, (name, func, _) in enumerate(steps):
            if progress_callback:
                progress_callback(int((i / len(steps)) * 100), f"Analyse : {name}…")
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
#  INTERFACE GRAPHIQUE
# ══════════════════════════════════════════════════════════════════════════════
class SysDiagApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.engine = DiagnosticEngine()
        self._setup_window()
        self._build_ui()

    # ── Fenêtre ───────────────────────────────────────────────────────────────
    def _setup_window(self):
        self.title("SysDiag — Thabet Raki  │  GPL v3")
        self.geometry("1100x750")
        self.minsize(900, 600)
        self.configure(bg=BG_DARK)
        try:
            self.iconbitmap("")
        except Exception:
            pass

    # ── Construction UI ───────────────────────────────────────────────────────
    def _build_ui(self):
        # ── Header ────────────────────────────────────────────────────────────
        header = tk.Frame(self, bg=BG_PANEL, pady=12, padx=20)
        header.pack(fill="x")

        tk.Label(header, text="⬡  SysDiag", font=("Courier New", 20, "bold"),
                 fg=ACCENT_CYAN, bg=BG_PANEL).pack(side="left")

        tk.Label(header, text="Outil de Diagnostic Système  ·  Thabet Raki  ·  GPLv3",
                 font=("Courier New", 9), fg=TEXT_SUB, bg=BG_PANEL).pack(side="left", padx=16)

        self.status_lbl = tk.Label(header, text="Prêt", font=("Courier New", 9, "bold"),
                                   fg=ACCENT_GREEN, bg=BG_PANEL)
        self.status_lbl.pack(side="right")

        # ── Barre de progression ───────────────────────────────────────────────
        prog_frame = tk.Frame(self, bg=BG_DARK)
        prog_frame.pack(fill="x", padx=20, pady=(6, 0))

        self.progress_var = tk.IntVar(value=0)
        self.progress = ttk.Progressbar(prog_frame, variable=self.progress_var,
                                        maximum=100, length=400)
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TProgressbar", troughcolor=BG_CARD, background=ACCENT_CYAN,
                         thickness=6)
        self.progress.pack(fill="x")

        # ── Corps principal (paned) ────────────────────────────────────────────
        paned = tk.PanedWindow(self, orient="horizontal", bg=BG_DARK,
                               sashwidth=4, sashpad=2, sashrelief="flat")
        paned.pack(fill="both", expand=True, padx=12, pady=8)

        # Panneau gauche ── sections
        left = tk.Frame(paned, bg=BG_PANEL, width=320)
        paned.add(left, minsize=250)

        tk.Label(left, text="SECTIONS", font=("Courier New", 9, "bold"),
                 fg=TEXT_SUB, bg=BG_PANEL).pack(anchor="w", padx=12, pady=(10, 4))

        self.section_list = tk.Listbox(
            left, bg=BG_CARD, fg=TEXT_MAIN, font=("Courier New", 11),
            selectbackground=ACCENT_CYAN, selectforeground=BG_DARK,
            activestyle="none", relief="flat", borderwidth=0,
            highlightthickness=0, cursor="hand2"
        )
        self.section_list.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.section_list.bind("<<ListboxSelect>>", self._on_section_select)

        # Panneau droit ── détail
        right = tk.Frame(paned, bg=BG_DARK)
        paned.add(right, minsize=400)

        self.detail_text = scrolledtext.ScrolledText(
            right, bg=BG_CARD, fg=TEXT_MAIN, font=("Courier New", 10),
            relief="flat", borderwidth=0, insertbackground=ACCENT_CYAN,
            wrap="word", state="disabled"
        )
        self.detail_text.pack(fill="both", expand=True)
        self._configure_tags()

        # ── Bas de page ────────────────────────────────────────────────────────
        footer = tk.Frame(self, bg=BG_PANEL, pady=8)
        footer.pack(fill="x", side="bottom")

        btn_style = {"font": ("Courier New", 10, "bold"), "relief": "flat",
                     "cursor": "hand2", "padx": 18, "pady": 6}

        self.btn_scan = tk.Button(footer, text="▶  LANCER LE DIAGNOSTIC",
                                  bg=ACCENT_CYAN, fg=BG_DARK,
                                  command=self._run_diagnostic, **btn_style)
        self.btn_scan.pack(side="left", padx=12)

        tk.Button(footer, text="💾  EXPORTER RAPPORT",
                  bg=BG_CARD, fg=ACCENT_CYAN, bd=1,
                  command=self._export_report, **btn_style).pack(side="left", padx=4)

        tk.Button(footer, text="ℹ  LICENCE",
                  bg=BG_CARD, fg=TEXT_SUB, bd=0,
                  command=self._show_license, **btn_style).pack(side="right", padx=12)

        self._sections_data = {}
        self._issues_data   = []

    def _configure_tags(self):
        t = self.detail_text
        t.tag_config("title",    foreground=ACCENT_CYAN,  font=("Courier New", 13, "bold"))
        t.tag_config("key",      foreground=ACCENT_GREEN, font=("Courier New", 10, "bold"))
        t.tag_config("val",      foreground=TEXT_MAIN,    font=("Courier New", 10))
        t.tag_config("critical", foreground=ACCENT_RED,   font=("Courier New", 10, "bold"))
        t.tag_config("warning",  foreground=ACCENT_WARN,  font=("Courier New", 10, "bold"))
        t.tag_config("ok",       foreground=ACCENT_GREEN, font=("Courier New", 10, "bold"))
        t.tag_config("solution", foreground="#A0C4FF",    font=("Courier New", 9))
        t.tag_config("sep",      foreground=BORDER,       font=("Courier New", 10))

    # ── Lancement diagnostic (thread) ──────────────────────────────────────────
    def _run_diagnostic(self):
        self.btn_scan.config(state="disabled", text="⏳  Analyse en cours…")
        self.section_list.delete(0, tk.END)
        self._write_detail("", clear=True)

        def work():
            sections, issues = self.engine.run_full_diagnostic(
                progress_callback=self._update_progress
            )
            self._sections_data = sections
            self._issues_data   = issues
            self.after(0, self._populate_results, sections, issues)

        threading.Thread(target=work, daemon=True).start()

    def _update_progress(self, value, message):
        self.after(0, lambda: self.progress_var.set(value))
        self.after(0, lambda: self.status_lbl.config(text=message))

    # ── Affichage résultats ────────────────────────────────────────────────────
    def _populate_results(self, sections, issues):
        self.btn_scan.config(state="normal", text="▶  RELANCER LE DIAGNOSTIC")

        # Ajouter sections dans la liste
        for name in sections:
            self.section_list.insert(tk.END, f"  {name}")

        # Ajouter section Problèmes détectés
        count = len(issues)
        label = f"  ⚠ Problèmes ({count})" if count else "  ✔ Aucun problème"
        self.section_list.insert(tk.END, label)

        # Afficher le résumé global
        self._show_summary(sections, issues)

    def _show_summary(self, sections, issues):
        t = self.detail_text
        t.config(state="normal")
        t.delete("1.0", tk.END)

        t.insert(tk.END, "RAPPORT DE DIAGNOSTIC SYSTÈME\n", "title")
        t.insert(tk.END, f"  Généré le : {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n", "val")
        t.insert(tk.END, f"  Auteur    : Thabet Raki\n", "val")
        t.insert(tk.END, "─" * 70 + "\n\n", "sep")

        # OS
        si = sections.get("Système", {})
        for k, v in si.items():
            t.insert(tk.END, f"  {k:<20} ", "key")
            t.insert(tk.END, f"{v}\n", "val")

        t.insert(tk.END, "\n" + "─" * 70 + "\n", "sep")
        t.insert(tk.END, f"\n  RÉSULTATS DU DIAGNOSTIC\n\n", "title")

        critiques = [i for i in issues if i["severite"] == "CRITIQUE"]
        avert     = [i for i in issues if i["severite"] == "AVERTISSEMENT"]

        if not issues:
            t.insert(tk.END, "  ✔  Aucun problème détecté ! Votre système semble en bonne santé.\n", "ok")
        else:
            t.insert(tk.END, f"  ✘  {len(critiques)} problème(s) CRITIQUE(S)\n", "critical")
            t.insert(tk.END, f"  ⚠  {len(avert)} avertissement(s)\n\n", "warning")

            for issue in issues:
                sev_tag = "critical" if issue["severite"] == "CRITIQUE" else "warning"
                t.insert(tk.END, f"\n  [{issue['severite']}] {issue['composant']}\n", sev_tag)
                t.insert(tk.END, f"  {issue['probleme']}\n", "val")
                t.insert(tk.END, "  Solutions recommandées :\n", "key")
                for s in issue["solutions"]:
                    t.insert(tk.END, f"    → {s}\n", "solution")

        t.config(state="disabled")

    def _on_section_select(self, event):
        sel = self.section_list.curselection()
        if not sel:
            return
        idx  = sel[0]
        keys = list(self._sections_data.keys())

        if idx < len(keys):
            name = keys[idx]
            data = self._sections_data[name]
            self._show_section(name, data)
        else:
            self._show_issues(self._issues_data)

    def _show_section(self, name, data):
        t = self.detail_text
        t.config(state="normal")
        t.delete("1.0", tk.END)
        t.insert(tk.END, f"  {name.upper()}\n", "title")
        t.insert(tk.END, "─" * 60 + "\n\n", "sep")
        for k, v in data.items():
            t.insert(tk.END, f"  {k:<28} ", "key")
            t.insert(tk.END, f"{v}\n", "val")

        # Problèmes liés à cette section
        rel = [i for i in self._issues_data if i["composant"].lower().startswith(name.lower())]
        if rel:
            t.insert(tk.END, "\n" + "─" * 60 + "\n", "sep")
            t.insert(tk.END, "\n  PROBLÈMES DÉTECTÉS\n\n", "critical")
            for issue in rel:
                sev_tag = "critical" if issue["severite"] == "CRITIQUE" else "warning"
                t.insert(tk.END, f"  [{issue['severite']}] {issue['probleme']}\n", sev_tag)
                t.insert(tk.END, "  Solutions :\n", "key")
                for s in issue["solutions"]:
                    t.insert(tk.END, f"    → {s}\n", "solution")

        t.config(state="disabled")

    def _show_issues(self, issues):
        t = self.detail_text
        t.config(state="normal")
        t.delete("1.0", tk.END)
        t.insert(tk.END, "  TOUS LES PROBLÈMES DÉTECTÉS\n", "title")
        t.insert(tk.END, "─" * 60 + "\n\n", "sep")

        if not issues:
            t.insert(tk.END, "  ✔  Aucun problème détecté.\n", "ok")
        else:
            for issue in issues:
                sev_tag = "critical" if issue["severite"] == "CRITIQUE" else "warning"
                t.insert(tk.END, f"\n  [{issue['severite']}]  {issue['composant']}\n", sev_tag)
                t.insert(tk.END, f"  {issue['probleme']}\n", "val")
                t.insert(tk.END, "  Solutions recommandées :\n", "key")
                for s in issue["solutions"]:
                    t.insert(tk.END, f"    → {s}\n", "solution")
                t.insert(tk.END, "\n", "val")

        t.config(state="disabled")

    def _write_detail(self, text, clear=False):
        t = self.detail_text
        t.config(state="normal")
        if clear:
            t.delete("1.0", tk.END)
        t.insert(tk.END, text)
        t.config(state="disabled")

    # ── Export rapport ─────────────────────────────────────────────────────────
    def _export_report(self):
        if not self._sections_data:
            messagebox.showinfo("Info", "Lancez d'abord un diagnostic.")
            return

        filename = f"rapport_sysdiag_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        path = os.path.join(os.path.expanduser("~"), "Desktop", filename)

        lines = [
            "=" * 70,
            "  RAPPORT DE DIAGNOSTIC SYSTÈME — SysDiag",
            f"  Auteur  : Thabet Raki",
            f"  Licence : GNU General Public License v3 (GPLv3)",
            f"  Date    : {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            "=" * 70, "",
        ]

        for section, data in self._sections_data.items():
            lines.append(f"\n[{section.upper()}]")
            if isinstance(data, dict):
                for k, v in data.items():
                    lines.append(f"  {k:<28} {v}")

        if self._issues_data:
            lines += ["", "=" * 70, "  PROBLÈMES ET SOLUTIONS", "=" * 70]
            for issue in self._issues_data:
                lines.append(f"\n  [{issue['severite']}] {issue['composant']}")
                lines.append(f"  {issue['probleme']}")
                lines.append("  Solutions :")
                for s in issue["solutions"]:
                    lines.append(f"    → {s}")
        else:
            lines += ["", "  ✔  Aucun problème détecté."]

        lines += ["", "=" * 70,
                  "  Rapport généré par SysDiag — Thabet Raki — GPLv3",
                  "  https://www.gnu.org/licenses/gpl-3.0.html",
                  "=" * 70]

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            messagebox.showinfo("Rapport exporté", f"Rapport sauvegardé :\n{path}")
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    # ── Licence ────────────────────────────────────────────────────────────────
    def _show_license(self):
        win = tk.Toplevel(self)
        win.title("Licence GNU GPLv3")
        win.geometry("660x440")
        win.configure(bg=BG_CARD)
        win.resizable(False, False)

        txt = scrolledtext.ScrolledText(win, bg=BG_DARK, fg=TEXT_MAIN,
                                        font=("Courier New", 9), relief="flat",
                                        borderwidth=0, wrap="word")
        txt.pack(fill="both", expand=True, padx=12, pady=12)
        txt.insert(tk.END, """SysDiag — Outil de Diagnostic Système
Copyright (C) 2026  Thabet Raki

Ce programme est un logiciel libre distribué sous les termes de la
Licence Publique Générale GNU version 3 (GPLv3).

Vous êtes libre de :
  → Utiliser ce programme à toute fin
  → Étudier et modifier le code source
  → Redistribuer des copies
  → Distribuer vos versions modifiées

Sous les conditions suivantes :
  → Toute redistribution doit inclure le code source
  → Les travaux dérivés doivent rester sous GPLv3
  → Le nom de l'auteur original doit être conservé

Texte intégral de la licence :
https://www.gnu.org/licenses/gpl-3.0.html

Ce programme est distribué SANS AUCUNE GARANTIE.
""")
        txt.config(state="disabled")
        tk.Button(win, text="Fermer", bg=ACCENT_CYAN, fg=BG_DARK,
                  font=("Courier New", 10, "bold"), relief="flat",
                  command=win.destroy).pack(pady=8)


# ══════════════════════════════════════════════════════════════════════════════
#  POINT D'ENTRÉE
# ══════════════════════════════════════════════════════════════════════════════
def main():
    # Vérification dépendances
    try:
        import psutil
    except ImportError:
        print("Installation de psutil…")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil", "--quiet"])
        import psutil  # noqa

    app = SysDiagApp()
    app.mainloop()


if __name__ == "__main__":
    main()

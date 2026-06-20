# Créer SysDiag_v4.exe — Guide complet

## ⚠️ Pré-requis important

PyInstaller compile **pour l'OS sur lequel il s'exécute**. Comme SysDiag est une app Windows (tkinter + ctypes.windll + commandes PowerShell), tu dois lancer le build **sur une machine Windows** — ou une VM Windows, ou un service comme GitHub Actions avec un runner `windows-latest`. Le compiler depuis Linux/Mac ne produira pas un .exe utilisable.

## Fichiers fournis

| Fichier | Rôle |
|---|---|
| `SysDiag_v4.py` | Le script source (déjà fourni précédemment) |
| `sysdiag.spec` | Configuration PyInstaller (imports cachés, options exe) |
| `sysdiag.manifest` | Manifeste Windows qui déclenche l'élévation UAC automatiquement au lancement |
| `version_info.txt` | Métadonnées affichées dans les propriétés du fichier .exe (clic droit → Propriétés) |
| `build_exe.bat` | Script tout-en-un : crée un venv, installe les dépendances, compile |

## Étapes (sur Windows)

1. **Installer Python 3.10+** si ce n'est pas déjà fait (cocher "Add to PATH" à l'installation).
2. Place ces 5 fichiers **dans le même dossier** :
   - `SysDiag_v4.py`
   - `sysdiag.spec`
   - `sysdiag.manifest`
   - `version_info.txt`
   - `build_exe.bat`
3. (Optionnel) Ajoute une icône nommée exactement `sysdiag.ico` dans ce même dossier. Sans elle, retire la ligne `icon='sysdiag.ico'` dans `sysdiag.spec`, sinon le build échouera.
4. Double-clique sur `build_exe.bat`.
5. Le fichier final apparaît dans `dist\SysDiag_v4.exe`.

## Ce que fait `sysdiag.spec` pour toi

- **`console=False`** : pas de fenêtre noire de terminal derrière ton interface graphique.
- **`uac_admin=True` + manifeste** : Windows demande l'élévation administrateur **avant** même de lancer le programme (UAC), plutôt que de laisser ton script se relancer lui-même via `ShellExecuteW`. C'est plus propre et évite un flash de fenêtre. Tu peux garder ta logique `is_admin()` / `run_as_admin()` actuelle comme filet de sécurité, elle ne posera pas de problème.
- **`hiddenimports`** : PyInstaller ne détecte pas toujours automatiquement `psutil` et les sous-modules de `requests`. Sans ça, l'exe plante au lancement avec une erreur `ModuleNotFoundError` invisible (fenêtre qui s'ouvre puis se ferme aussitôt).
- **`onefile` n'est PAS activé** : le `.spec` actuel produit un dossier `dist\SysDiag_v4\` avec l'exe + ses dépendances, plus rapide à lancer. Si tu préfères **un seul fichier .exe portable** (plus simple à distribuer mais démarrage plus lent, ~2-5 sec), dis-le-moi et je modifie le `.spec` pour utiliser `--onefile`.

## Pièges fréquents à connaître

### 1. Faux positifs antivirus
Les `.exe` PyInstaller (surtout en mode `--onefile`) sont **fréquemment signalés à tort** par Windows Defender et d'autres antivirus, car le pattern de compression/auto-extraction ressemble à celui de certains malwares. C'est un problème connu et très courant pour ce type de packaging, pas un bug de ton code.

**Solutions :**
- Privilégier le mode dossier (non-onefile, déjà configuré dans le `.spec` fourni) — moins de faux positifs.
- **Signer numériquement l'exe** (section suivante) — la mesure la plus efficace.
- Soumettre l'exe à Microsoft pour analyse si Defender le bloque : https://www.microsoft.com/en-us/wdsi/filesubmission

### 2. Signature numérique (code signing)
Sans signature, Windows affichera "Éditeur inconnu" au lancement (SmartScreen), ce qui fait fuir des acheteurs. Pour signer :
- Acheter un certificat de signature de code (Code Signing Certificate) chez une autorité reconnue (DigiCert, Sectigo, SSL.com…), généralement 70-400 USD/an selon le type (un certificat **EV** supprime l'avertissement SmartScreen immédiatement ; un certificat standard nécessite d'accumuler une réputation dans le temps).
- Signer avec `signtool.exe` (fourni avec le Windows SDK) :
  ```
  signtool sign /f moncertificat.pfx /p motmotdepasse /tr http://timestamp.digicert.com /td sha256 /fd sha256 dist\SysDiag_v4.exe
  ```

### 3. psutil / requests qui demandent une réinstallation au premier lancement
Ton script contient un `try/except ImportError` qui réinstalle `psutil`/`requests` via pip s'ils manquent. **Une fois packagé en .exe, ce mécanisme ne sert plus à rien** (l'utilisateur final n'a pas forcément Python/pip), mais il ne casse rien non plus puisque `hiddenimports` garantit que ces deux modules sont déjà inclus dans l'exe. Je te conseille de le laisser tel quel par sécurité (defensive code), sauf si tu veux que je le retire pour alléger.

### 4. Antivirus + élévation UAC
Comme ton app exécute des commandes PowerShell/CMD avec droits admin, certains antivirus d'entreprise peuvent la mettre en quarantaine par prudence. C'est attendu pour ce type d'outil (comme CCleaner, Advanced SystemCare, etc.) — la signature numérique reste la meilleure réponse.

## Build automatique via GitHub Actions (alternative sans VM Windows)

Si tu n'as pas accès à une machine Windows, je peux te préparer un fichier `.github/workflows/build.yml` qui compile automatiquement le `.exe` sur un runner Windows à chaque push, et le rend téléchargeable en artifact. Dis-le-moi si tu veux cette option.

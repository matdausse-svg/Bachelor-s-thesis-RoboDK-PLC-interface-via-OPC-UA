# RoboDK ↔ CODESYS OPC UA Interface

[Français](#français) | [English](#english)

---

## Français

### Interface générique entre cellules robotiques virtuelles RoboDK et SPS CODESYS via OPC UA

Une interface qui pilote des cellules robotiques virtuelles RoboDK depuis une SPS CODESYS, via OPC UA. Pour intégrer une nouvelle station, le projet SPS ne change pas : on ajoute un programme Python dans la station, on préfixe les programmes à piloter par `CMD_` et on leur ajoute les instructions IO du standard. La liste des programmes remonte ensuite d'elle-même dans l'IHM CODESYS.

Réalisé seul dans le cadre de ma Bachelorarbeit au Labor für Automatisierung und Robotik de la Hochschule München (novembre 2025 à mars 2026).

### Architecture

| Élément | Rôle |
|---|---|
| CODESYS | Serveur OPC UA, IHM, génération des commandes |
| Programme Python (dans RoboDK) | Client OPC UA, logique d'interface, synchronisation des IO |
| RoboDK | Exécution des programmes robot |

```
CODESYS → OPC UA → Python → RoboDK
RoboDK → Python → OPC UA → CODESYS
```

Le client Python se connecte à `opc.tcp://localhost:4840` et échange avec la SPS toutes les 90 ms environ.

### Contenu du dépôt

```
python/Generisch4.py     Client OPC UA à ajouter comme programme Python dans la station RoboDK
codesys/GVL.st           Liste de variables globales (lisible sans CODESYS)
codesys/PLC_PRG.st       Logique de démarrage et d'arrêt (lisible sans CODESYS)
codesys/Generisch_V4.3._OPCUA_Codesys.project   Projet CODESYS complet
robodk/GenerischV4_OPCUA_cubestation.rdk        Station RoboDK d'exemple
docs/                    Standard d'implémentation avec captures (PDF et Word, en anglais)
```

### Prérequis

- CODESYS V3.5 SP20 Patch 1 (CODESYS Control Win V3)
- RoboDK 5.9
- Python 3.10 et la bibliothèque python-opcua 0.9.3 (`pip install opcua`), disponible dans l'interpréteur Python utilisé par RoboDK

### Mise en service

Le guide pas à pas avec captures d'écran est dans `docs/Implementation_Standard_EN.pdf`. Voici l'essentiel.

**1. Sécurité CODESYS (une seule fois)**
Dans l'onglet Device, clic droit sur l'appareil, « Change Execution Security Policy », puis activer « Allow anonymous connection ». Sans ce réglage, aucune connexion OPC UA n'est possible. Ce réglage convient à une simulation locale, pas à une installation réelle.

**2. Station RoboDK**
- Les programmes à piloter ne doivent pas contenir d'espace dans leur nom.
- Clic droit sur la station, « Paramètres de la station », puis ajouter un paramètre `CMD_<NomDuProgramme>` pour chaque programme (exemple : `CMD_Cube_1`).
- Ajouter aussi le paramètre `IO_Run`.
- Ajouter `Generisch4.py` à la station comme programme Python.

**3. Structure des programmes RoboDK**
Chaque programme piloté est associé à un signal `IO_n`. L'ordre des instructions est obligatoire.

Programme intégré RoboDK :
```
Wait IO_n = 1
Set IO_Run = 1
... (programme)
Set IO_Run = 0
Set IO_n = 0
```

Programme Python :
```python
RDK = Robolink()
while RDK.getParam("IO_n") != "1":
    time.sleep(0.05)
RDK.setParam("IO_Run", "1")
# ... (programme)
RDK.setParam("IO_Run", "0")
RDK.setParam("running", "0")
RDK.setParam("IO_n", "0")
```

Pour un sous-programme piloté appelé depuis un autre programme, l'activation de son IO se fait dans le programme appelant, juste avant l'appel (`Set IO_3 = 1` puis `Call ...`). Pour une fonction interne de RoboDK sans instruction IO (par exemple un réglage de soudage), le début et la fin sont simulés dans le programme principal (`Set IO_n = 1`, `Call ...`, `Set IO_n = 0`).

**4. Lancement**
1. Ouvrir la station RoboDK.
2. Ouvrir le projet CODESYS.
3. Démarrer la runtime CODESYS.
4. Démarrer le programme Python dans RoboDK.

Si le programme Python est lancé avant la runtime, la connexion OPC UA échoue : il suffit de l'arrêter et de le relancer. Si les boutons et voyants de la visualisation CODESYS n'apparaissent pas, copier le dossier « Application », supprimer l'original puis le recoller dans « Logik API ».

**5. Utilisation**
1. Choisir un programme dans la liste déroulante.
2. Appuyer sur `Trigger` pour confirmer.
3. Appuyer sur `IO` pour lancer le programme (signal `Start_IO`).

Si l'on choisit un autre programme après `Trigger`, il faut d'abord appuyer sur `Stop`.

### Limites connues

- Pas de sécurité OPC UA (ni authentification, ni chiffrement, ni gestion de certificats).
- Fonctionnement par polling (cycle de 90 ms) : un programme plus court qu'un cycle n'allume pas `IO_Run` dans l'IHM, et l'état s'affiche avec environ 0,5 s de décalage.
- Un seul programme principal à la fois : un second lancement pendant un cycle est ignoré.
- Plusieurs stations RoboDK ouvertes en même temps sur un PC peuvent brouiller l'affichage des états.

### État du test

Le système a été validé sur quatre stations et 24 programmes avec RoboDK 5.9.4 et CODESYS Control Win V3 SP20 Patch 1 sous Windows 11, début 2026. Je n'ai plus les licences depuis : il n'a pas été retesté, et le code Python de ce dépôt est la version de la thèse avec des commentaires et des messages traduits en anglais.

### Licence

Mon code est publié sous licence MIT (voir `LICENSE`). La station d'exemple peut contenir des éléments de la bibliothèque RoboDK, soumis aux conditions de RoboDK.

---

## English

### Generic interface between RoboDK virtual robot cells and a CODESYS PLC via OPC UA

An interface that drives virtual RoboDK robot cells from a CODESYS PLC over OPC UA. To integrate a new station, the PLC project stays the same: you add a Python program to the station, prefix the programs to control with `CMD_` and add the standard's IO instructions to them. The program list then shows up in the CODESYS HMI on its own.

Developed on my own as my Bachelor's thesis at the Labor für Automatisierung und Robotik of Hochschule München (November 2025 to March 2026).

### Architecture

| Element | Role |
|---|---|
| CODESYS | OPC UA server, HMI, generation of control commands |
| Python program (inside RoboDK) | OPC UA client, interface logic, IO synchronization |
| RoboDK | Execution of the robot programs |

```
CODESYS → OPC UA → Python → RoboDK
RoboDK → Python → OPC UA → CODESYS
```

The Python client connects to `opc.tcp://localhost:4840` and exchanges data with the PLC roughly every 90 ms.

### Repository content

```
python/Generisch4.py     OPC UA client, to be added as a Python program in the RoboDK station
codesys/GVL.st           Global variable list (readable without CODESYS)
codesys/PLC_PRG.st       Start and stop logic (readable without CODESYS)
codesys/Generisch_V4.3._OPCUA_Codesys.project   Full CODESYS project
robodk/GenerischV4_OPCUA_cubestation.rdk        Example RoboDK station
docs/                    Implementation standard with screenshots (PDF and Word, in English)
```

### Requirements

- CODESYS V3.5 SP20 Patch 1 (CODESYS Control Win V3)
- RoboDK 5.9
- Python 3.10 and the python-opcua 0.9.3 library (`pip install opcua`), available in the Python interpreter used by RoboDK

### Setup

The step-by-step guide with screenshots is in `docs/Implementation_Standard_EN.pdf`. Here are the essentials.

**1. CODESYS security (once)**
In the Device tab, right-click the device, choose "Change Execution Security Policy", then enable "Allow anonymous connection". Without it, no OPC UA connection can be made. This setting suits a local simulation, not a real installation.

**2. RoboDK station**
- Programs to control must not contain spaces in their name.
- Right-click the station, open "Station parameters", then add a `CMD_<ProgramName>` parameter for each program (example: `CMD_Cube_1`).
- Also add the `IO_Run` parameter.
- Add `Generisch4.py` to the station as a Python program.

**3. Structure of the RoboDK programs**
Each controlled program is tied to an `IO_n` signal. The order of the instructions is mandatory.

Built-in RoboDK program:
```
Wait IO_n = 1
Set IO_Run = 1
... (program)
Set IO_Run = 0
Set IO_n = 0
```

Python program:
```python
RDK = Robolink()
while RDK.getParam("IO_n") != "1":
    time.sleep(0.05)
RDK.setParam("IO_Run", "1")
# ... (program)
RDK.setParam("IO_Run", "0")
RDK.setParam("running", "0")
RDK.setParam("IO_n", "0")
```

For a controlled subprogram called from another program, its IO is set in the calling program, right before the call (`Set IO_3 = 1`, then `Call ...`). For a built-in RoboDK function with no IO instruction (a welding setting, for instance), the start and end are simulated in the main program (`Set IO_n = 1`, `Call ...`, `Set IO_n = 0`).

**4. Startup**
1. Open the RoboDK station.
2. Open the CODESYS project.
3. Start the CODESYS runtime.
4. Start the Python program in RoboDK.

If the Python program starts before the runtime, the OPC UA connection fails: just stop it and start it again. If the buttons and lamps of the CODESYS visualization do not show up, copy the "Application" folder, delete the original and paste it back into "Logik API".

**5. Usage**
1. Pick a program in the drop-down list.
2. Press `Trigger` to confirm.
3. Press `IO` to start the program (`Start_IO` signal).

If you pick another program after `Trigger`, press `Stop` first.

### Known limits

- No OPC UA security (no authentication, encryption or certificate management).
- Polling-based (90 ms cycle): a program shorter than one cycle does not light `IO_Run` in the HMI, and the state appears with about 0.5 s of delay.
- Only one main program at a time: a second start during a cycle is ignored.
- Several RoboDK stations open at once on one PC can scramble the status display.

### Test status

The system was validated on four stations and 24 programs with RoboDK 5.9.4 and CODESYS Control Win V3 SP20 Patch 1 on Windows 11, in early 2026. I no longer have the licenses, so it has not been retested since, and the Python code in this repository is the thesis version with comments and messages translated to English.

### License

My code is released under the MIT license (see `LICENSE`). The example station may contain elements from the RoboDK library, which are subject to RoboDK's terms.

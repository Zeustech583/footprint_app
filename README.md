# Flux-Footprint-App (Streamlit)

Lokale Web-App: Rohdaten aufbereiten → Obukhov-Länge → Footprint als Bilder oder Video.

## Start
- **Windows:** Doppelklick auf `start_windows.bat`
- **Mac/Linux:** `./start_mac_linux.sh`

Beim ersten Start wird eine virtuelle Umgebung angelegt und alles aus `requirements.txt`
installiert (Python 3.10+ und Internet nötig). Danach öffnet sich der Browser (http://localhost:8501).

## Ordner (alle relativ zum Programmordner)
```
app.py                  Startseite
pages/                  Seiten im Menü links
core/                   Rechenlogik (Aufbereitung, Obukhov, FFP-Modell, Ausgabe)
daten/rohdaten          Rohdateien (LI-710-CSV, Wetterstation-XLS)
daten/ergebnisse_kwf    Kinematischer_Waerme_Fluss.csv
daten/ergebnisse_wind   Windeigenschaften.xls
daten/obukhov           Obukhov_Ergebnis.csv
daten/bilder            Footprint-PNGs
daten/video             footprint_zeitverlauf.mp4
```
Auf einen anderen Rechner umziehen: Programmordner kopieren und dort `start_…` ausführen.
Soll der Datenordner woanders liegen (z. B. Netzlaufwerk), die Umgebungsvariable
`FOOTPRINT_DATEN` auf den Pfad setzen.

"""Zentrale Pfade und Einstellungen.

Alle Pfade sind RELATIV zum Programmordner. Dadurch läuft die App ohne
Anpassung auf jedem Rechner. Optional kann der Datenordner mit der
Umgebungsvariable FOOTPRINT_DATEN auf ein Netzlaufwerk gelegt werden.
"""
import json
import os
from pathlib import Path

BASIS = Path(__file__).resolve().parent.parent
DATEN = Path(os.environ.get("FOOTPRINT_DATEN", BASIS / "daten"))

ROHDATEN = DATEN / "rohdaten"                 # hochgeladene / abgelegte Rohdateien
KWF_DIR = DATEN / "ergebnisse_kwf"            # aufbereitete LI-710-Datei
WIND_DIR = DATEN / "ergebnisse_wind"          # aufbereitete Winddatei
OBUKHOV_DIR = DATEN / "obukhov"               # Ergebnis der Obukhov-Länge
BILDER_DIR = DATEN / "bilder"                 # Footprint-Bilder (PNG)
VIDEO_DIR = DATEN / "video"                   # Footprint-Video (MP4)
CACHE_DIR = DATEN / "cache"                   # Hintergrundkarten (werden nur einmal geladen)

KWF_DATEI = KWF_DIR / "Kinematischer_Waerme_Fluss.csv"
WIND_DATEI = WIND_DIR / "Windeigenschaften.xls"
OBUKHOV_DATEI = OBUKHOV_DIR / "Obukhov_Ergebnis.csv"
VIDEO_DATEI = VIDEO_DIR / "footprint_zeitverlauf.mp4"
EINSTELLUNGEN = DATEN / "einstellungen.json"

ORDNER = {
    "Rohdaten": ROHDATEN,
    "Aufbereitete LI-710-Datei": KWF_DIR,
    "Aufbereitete Winddatei": WIND_DIR,
    "Obukhov-Länge": OBUKHOV_DIR,
    "Footprint-Bilder": BILDER_DIR,
    "Footprint-Video": VIDEO_DIR,
}

STANDARD = {
    "zm": 2.0,            # Messhöhe [m]
    "z0": 0.03,           # Rauigkeitslänge [m]
    "h": 800.0,           # Grenzschichthöhe [m]
    "lat0": 53.3705,      # Position des Sensors
    "lon0": 9.0170,
    "epsg": "EPSG:32632", # UTM-Zone 32N
    "domain": 300,        # Domäne ± [m]
    "dx": 2,              # Gitterauflösung [m]
    "rs": [10, 30, 50, 80],
    "sigmav_faktor": 2.0, # sigma_v ≈ Faktor * u*
    "u_star_faktor": 1.25,
}


def ordner_anlegen():
    for p in (*ORDNER.values(), CACHE_DIR):
        p.mkdir(parents=True, exist_ok=True)


def lade_einstellungen():
    werte = dict(STANDARD)
    try:
        werte.update(json.loads(EINSTELLUNGEN.read_text(encoding="utf-8")))
    except Exception:
        pass
    return werte


def speichere_einstellungen(werte):
    ordner_anlegen()
    EINSTELLUNGEN.write_text(json.dumps(werte, indent=2, ensure_ascii=False), encoding="utf-8")

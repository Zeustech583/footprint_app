"""Schritt 1: Rohdaten aufbereiten (aus den Skripten Rohdaten_obukhov_aufbereiten.py
und Rohdateien_wind_aufbereiten.py)."""
import io
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import escape

import pandas as pd

from . import pfade

# Anfang des Rohdaten-Spaltennamens -> Name, den die Obukhov-Berechnung erwartet
UMBENENNUNG_LI710 = {
    "Date": "Date",
    "Sensible Heat Flux": "Sensible_Heat_Flux",
    "Air Temperature": "Air_Temperature",
    "Atmospheric Pressure": "Atmospheric_Pressure",
    "W - Standard Deviation": "W_StandardDeviation",
}
NEUE_NAMEN_WIND = ["Zeit", "Wind_Speed", "Wind_Speed_max", "Wind_Direction"]
NS = {"ss": "urn:schemas-microsoft-com:office:spreadsheet"}


# --------------------------------------------------------------------------- LI-710
def li710_aufbereiten(quelle):
    """quelle: Pfad oder Bytes der LI-710-CSV. Gibt den aufbereiteten DataFrame zurück."""
    if isinstance(quelle, (bytes, bytearray)):
        quelle = io.BytesIO(quelle)
    roh = pd.read_csv(quelle, low_memory=False)

    neu = pd.DataFrame()
    for anfang, neuer_name in UMBENENNUNG_LI710.items():
        # Spalte über den Namensanfang finden (der Rest enthält die Sensor-ID)
        treffer = [c for c in roh.columns if c == anfang or c.startswith(anfang + " (")]
        if not treffer:
            raise KeyError(f"Spalte '{anfang}' nicht in der Rohdatei gefunden.")
        neu[neuer_name] = roh[treffer[0]]

    # Zeilen ohne Flussmessung (Logger-Statuszeilen) entfernen
    return neu.dropna(subset=["Sensible_Heat_Flux", "Air_Temperature",
                              "Atmospheric_Pressure", "W_StandardDeviation"])


def speichere_kwf(df, pfad=None):
    pfad = Path(pfad or pfade.KWF_DATEI)
    pfad.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(pfad, sep=";", decimal=",", index=False, encoding="utf-8-sig")
    return pfad


# --------------------------------------------------------------------------- Wetterstation
def _lese_raster(daten: bytes):
    """Liest die Datei als Zeilenliste (XML-basiertes oder echtes Excel)."""
    kopf = daten[:100].lstrip(b"\xef\xbb\xbf").lstrip()
    if not kopf.startswith(b"<?xml"):
        return pd.read_excel(io.BytesIO(daten), header=None).fillna("").astype(object).values.tolist()
    idx, mrg = f"{{{NS['ss']}}}Index", f"{{{NS['ss']}}}MergeAcross"
    wurzel = ET.fromstring(daten.lstrip(b"\xef\xbb\xbf"))
    zeilen = []
    for z in wurzel.findall(".//ss:Row", NS):
        werte = []
        for c in z.findall("ss:Cell", NS):
            if c.get(idx):                               # übersprungene leere Zellen
                werte += [""] * (int(c.get(idx)) - 1 - len(werte))
            dat = c.find("ss:Data", NS)
            werte.append(dat.text if dat is not None and dat.text else "")
            werte += [""] * int(c.get(mrg, 0))           # verbundene Zellen auffüllen
        zeilen.append(werte)
    return zeilen


def wind_aufbereiten(quelle):
    """quelle: Pfad oder Bytes der Roh-Winddatei. Gibt DataFrame Zeit/Wind_Speed/... zurück."""
    daten = quelle if isinstance(quelle, (bytes, bytearray)) else Path(quelle).read_bytes()
    zeilen = _lese_raster(bytes(daten))
    n = max(len(z) for z in zeilen[:2])
    kopf0 = (zeilen[0] + [""] * n)[:n]
    kopf1 = (zeilen[1] + [""] * n)[:n]
    for j in range(1, n):                                # obere Überschrift nach rechts auffüllen
        if not str(kopf0[j]).strip():
            kopf0[j] = kopf0[j - 1]
    namen = [f"{a} | {b}".lower() for a, b in zip(kopf0, kopf1)]

    def finde(*teile):
        for j, nm in enumerate(namen):
            if all(t.lower() in nm for t in teile):
                return j
        raise KeyError(f"Spalte mit {teile} nicht in der Rohdatei gefunden.")

    spalten = [0,
               finde("Windgeschwindigkeit", "Durchschn"),
               finde("Windgeschwindigkeit", "max"),
               finde("Windrichtung")]

    rest = [z + [""] * (n - len(z)) for z in zeilen[2:] if z and str(z[0]).strip()]
    neu = pd.DataFrame([[r[j] for j in spalten] for r in rest], columns=NEUE_NAMEN_WIND)
    neu["Zeit"] = pd.to_datetime(neu["Zeit"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    for c in NEUE_NAMEN_WIND[1:]:
        neu[c] = pd.to_numeric(neu[c], errors="coerce")
    return neu


def _zelle(wert):
    if pd.isna(wert):
        return '<Cell><Data ss:Type="String"></Data></Cell>'
    if isinstance(wert, str):
        return f'<Cell><Data ss:Type="String">{escape(wert)}</Data></Cell>'
    return f'<Cell><Data ss:Type="Number">{wert}</Data></Cell>'


def speichere_wind(df, pfad=None):
    """Schreibt das XML-basierte "Schein-Excel": 2 Kopfzeilen + Daten."""
    pfad = Path(pfad or pfade.WIND_DATEI)
    pfad.parent.mkdir(parents=True, exist_ok=True)
    zeilen_xml = ["<Row>" + "".join(_zelle(x) for x in NEUE_NAMEN_WIND) + "</Row>",
                  "<Row>" + "".join(_zelle(x) for x in ["UTC", "m/s", "m/s", "deg"]) + "</Row>"]
    for r in df.itertuples(index=False):
        zeilen_xml.append("<Row>" + "".join(_zelle(x) for x in r) + "</Row>")
    xml = ('<?xml version="1.0"?>\n'
           '<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet" '
           'xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">\n'
           '<Worksheet ss:Name="Wind"><Table>\n' + "\n".join(zeilen_xml) +
           '\n</Table></Worksheet>\n</Workbook>\n')
    pfad.write_text(xml, encoding="utf-8")
    return pfad


def lese_wind(pfad):
    """Liest die aufbereitete Winddatei (2 Kopfzeilen, 4 Spalten)."""
    try:
        w = pd.read_excel(pfad, header=None, skiprows=2)          # echtes Excel
    except Exception:
        wurzel = ET.fromstring(Path(pfad).read_bytes().lstrip(b"\xef\xbb\xbf"))
        daten = []
        for z in wurzel.findall(".//ss:Row", NS)[2:]:
            werte = [(c.find("ss:Data", NS).text if c.find("ss:Data", NS) is not None else None)
                     for c in z.findall("ss:Cell", NS)]
            daten.append((werte + [None] * 4)[:4])
        w = pd.DataFrame(daten)
    w = w.iloc[:, :4]
    w.columns = NEUE_NAMEN_WIND
    w["Zeit"] = pd.to_datetime(w["Zeit"])
    for c in NEUE_NAMEN_WIND[1:]:
        w[c] = pd.to_numeric(w[c], errors="coerce")
    return w

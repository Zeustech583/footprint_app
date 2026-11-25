"""Startseite der Footprint-App.  Start:  streamlit run startseite.py"""
import streamlit as st

from core import pfade

st.set_page_config(page_title="Footprint-App", page_icon="🗺️", layout="wide")
pfade.ordner_anlegen()

st.title("🗺️ Flux-Footprint")
st.write("Von den Rohdaten des LI-710 und der Wetterstation bis zum Footprint-Bild oder -Video "
         "Anhand(Modell nach Kljun et al., 2015) ")

# Status der Schritte
def vorhanden(p):
    return " vorhanden✅" if p.exists() else "⚠️ noch nicht erzeugt"

schritte = [
    ("1 · Dateien bearbeiten", "pages/1_Dateien_bearbeiten.py", "🗂️",
     "Rohdaten (LI-710-CSV und Wetterstation-XLS) hochladen und aufbereiten.",
     f"LI-710: {vorhanden(pfade.KWF_DATEI)}  \nWind: {vorhanden(pfade.WIND_DATEI)}"),
    ("2 · Obukhov-Länge", "pages/2_Obukhov_Laenge.py", "🌡️",
     "Luftdichte, kinematischen Wärmefluss, u* und Obukhov-Länge berechnen.",
     f"Ergebnis: {vorhanden(pfade.OBUKHOV_DATEI)}"),
    ("3 · Footprint", "pages/3_Footprint.py", "🛰️",
     "Footprints berechnen und als Bilder und/oder Video ausgeben.",
     f"Bilder: {len(list(pfade.BILDER_DIR.glob('footprint_*.png')))} · "
     f"Video: {'✅' if pfade.VIDEO_DATEI.exists()  else '–'}"),
]
spalten = st.columns(3)
for sp, (titel, seite, icon, text, status) in zip(spalten, schritte):
    with sp.container(border=True):
        st.subheader(titel)
        st.write(text)
        st.caption(status)
        st.page_link(seite, label="Öffnen", icon=icon)

st.divider()
st.subheader("So gehen Sie vor :")
st.markdown(
    "1. **Dateien bearbeiten** – Rohdateien hochladen oder im Ordner `rohdaten` auswählen, aufbereiten.\n"
    "2. **Obukhov-Länge** – berechnen und speichern.\n"
    "3. **Footprint** – Sensor-Position und Modellparameter prüfen, Ausgabe wählen "
    "(Bilder, Video oder beides) und starten."
)

# ---------------------------------------------------------------- Ordner
st.subheader("Wo liegen meine Dateien?")
st.caption("Alle Ordner liegen neben der App und sind relativ – der Programmordner kann einfach auf einen "
           "anderen Rechner kopiert werden.")
zeilen = []
for name, p in pfade.ORDNER.items():
    dateien = [f for f in p.glob("*") if f.is_file()] if p.exists() else []
    zeilen.append({"Inhalt": name, "Ordner": str(p), "Dateien": len(dateien)})
st.dataframe(zeilen, hide_index=True, use_container_width=True)

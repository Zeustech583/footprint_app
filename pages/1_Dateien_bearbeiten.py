import streamlit as st

from core import aufbereitung as ab
from core import pfade

st.set_page_config(page_title="Dateien bearbeiten", page_icon="🗂️", layout="wide")
pfade.ordner_anlegen()
st.title("🗂️ Dateien bearbeiten")
st.write("Rohdateien werden auf die benötigten Spalten reduziert und im Ordner "
         "`daten/ergebnisse_…` gespeichert. Die Spaltennamen der Rohdaten müssen unverändert bleiben.")


def quelle_waehlen(schluessel, endungen):
    """Datei hochladen (wird in 'rohdaten' abgelegt) oder aus 'rohdaten' auswählen."""
    modus = st.radio("Quelle", ["Datei aus Ordner „rohdaten“", "Neue Datei hochladen"],
                     horizontal=True, key=f"modus_{schluessel}")
    if modus.startswith("Neue"):
        up = st.file_uploader("Rohdatei", type=endungen, key=f"up_{schluessel}")
        if up is None:
            return None
        ziel = pfade.ROHDATEN / up.name
        ziel.write_bytes(up.getvalue())
        st.caption(f"Gespeichert unter {ziel}")
        return ziel
    dateien = sorted(f.name for f in pfade.ROHDATEN.glob("*") if f.suffix.lower().lstrip(".") in endungen)
    if not dateien:
        st.info("Der Ordner „rohdaten“ enthält noch keine passende Datei – bitte eine hochladen.")
        return None
    return pfade.ROHDATEN / st.selectbox("Datei", dateien, key=f"sel_{schluessel}")


tab_li, tab_wind = st.tabs(["LI-710 (Wärmefluss)", "Wetterstation (Wind)"])

with tab_li:
    st.markdown("**Eingabe:** LI-710-CSV`eine CSV Datei ist erwartet` · **Ausgabe:** `Kinematischer_Waerme_Fluss.csv` "
                "(Trennzeichen `;`, Dezimalkomma)")
    quelle = quelle_waehlen("li", ["csv"])
    if quelle and st.button("LI-710-Datei aufbereiten", type="primary"):
        try:
            with st.spinner("Bereite auf …"):
                df = ab.li710_aufbereiten(quelle)
                ziel = ab.speichere_kwf(df)
            st.success(f"{len(df)} Zeilen gespeichert in {ziel}")
            st.dataframe(df.head(20), use_container_width=True)
        except Exception as e:
            st.error(f"Fehler: {e}")
    if pfade.KWF_DATEI.exists():
        with st.expander("Aktuelle aufbereitete Datei"):
            st.caption(str(pfade.KWF_DATEI))
            st.download_button("Herunterladen", pfade.KWF_DATEI.read_bytes(),
                               file_name=pfade.KWF_DATEI.name, key="dl_kwf")

with tab_wind:
    st.markdown("**Eingabe:** Wetterstation-XLS · **Ausgabe:** `Windeigenschaften.xls` "
                "(Zeit, Windgeschwindigkeit Ø und max, Windrichtung)")
    quelle = quelle_waehlen("wind", ["xls", "xlsx"])
    if quelle and st.button("Winddatei aufbereiten", type="primary"):
        try:
            with st.spinner("Bereite auf …"):
                df = ab.wind_aufbereiten(quelle)
                ziel = ab.speichere_wind(df)
            st.success(f"{len(df)} Zeilen gespeichert in {ziel}")
            st.dataframe(df.head(20), use_container_width=True)
        except Exception as e:
            st.error(f"Fehler: {e}")
    if pfade.WIND_DATEI.exists():
        with st.expander("Aktuelle aufbereitete Datei"):
            st.caption(str(pfade.WIND_DATEI))
            st.download_button("Herunterladen", pfade.WIND_DATEI.read_bytes(),
                               file_name=pfade.WIND_DATEI.name, key="dl_wind")

st.divider()
st.page_link("pages/2_Obukhov_Laenge.py", label="Weiter zu Schritt 2: Obukhov-Länge", icon="➡️")

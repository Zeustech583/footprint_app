import streamlit as st

from core import obukhov as ob
from core import pfade

st.set_page_config(page_title="Obukhov-Länge", page_icon="🌡️", layout="wide")
pfade.ordner_anlegen()
st.title("🌡️ Obukhov-Länge")
st.write("Berechnet aus `Kinematischer_Waerme_Fluss.csv`: Luftdichte → kinematischer Wärmefluss → u* → Obukhov-Länge.")

if not pfade.KWF_DATEI.exists():
    st.warning("Die aufbereitete LI-710-Datei fehlt. Bitte zuerst Schritt 1 ausführen.")
    st.page_link("pages/1_Dateien_bearbeiten.py", label="Zu Schritt 1", icon="🗂️")
    st.stop()

einst = pfade.lade_einstellungen()
faktor = st.number_input("u* = σw / Faktor", min_value=0.5, max_value=3.0, step=0.05,
                         value=float(einst["u_star_faktor"]),
                         help="Näherung: Die Standardabweichung von w ist nicht exakt u*. Standard: 1,25.")

if st.button("Obukhov-Länge berechnen", type="primary"):
    try:
        df = ob.berechne(ob.lade_kwf(), u_star_faktor=faktor)
        ziel = ob.speichere(df)
        einst["u_star_faktor"] = faktor
        pfade.speichere_einstellungen(einst)
        st.success(f"{len(df)} Zeilen gespeichert in {ziel}")
    except Exception as e:
        st.error(f"Fehler: {e}")

if pfade.OBUKHOV_DATEI.exists():
    df = ob.lade_ergebnis()
    st.subheader("Letztes Ergebnis")
    c1, c2, c3 = st.columns(3)
    c1.metric("Zeilen", len(df))
    c2.metric("Gültige Obukhov-Längen", int(df["Obukhov_Laenge"].notna().sum()))
    c3.metric("Mittleres u* [m/s]", f"{df['u_star'].mean():.3f}")
    st.dataframe(df[["Date", "Luftdichte", "kinematischer_waermefluss", "u_star", "Obukhov_Laenge"]],
                 use_container_width=True, height=300)
    g1, g2 = st.columns(2)
    verlauf = df.set_index("Date")
    g1.caption("u* [m/s]")
    g1.line_chart(verlauf["u_star"])
    g2.caption("Kinematischer Wärmefluss [K m/s]")
    g2.line_chart(verlauf["kinematischer_waermefluss"])
    st.caption(f"Datei: {pfade.OBUKHOV_DATEI}")
    st.download_button("Ergebnis herunterladen", pfade.OBUKHOV_DATEI.read_bytes(),
                       file_name=pfade.OBUKHOV_DATEI.name)
    st.divider()
    st.page_link("pages/3_Footprint.py", label="Weiter zu Schritt 3: Footprint", icon="➡️")

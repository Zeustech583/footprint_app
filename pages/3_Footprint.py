import streamlit as st

from core import footprint as fp
from core import pfade

st.set_page_config(page_title="Footprint", page_icon="🛰️", layout="wide")
pfade.ordner_anlegen()
st.title("🛰️ Footprint")

fehlend = [n for n, p in (("Obukhov-Ergebnis (Schritt 2)", pfade.OBUKHOV_DATEI),
                          ("Winddatei (Schritt 1)", pfade.WIND_DATEI)) if not p.exists()]
tab_neu, tab_bilder, tab_video = st.tabs(["Berechnen", "Bilder ansehen", "Video ansehen"])

# =============================================================== Berechnen
with tab_neu:
    if fehlend:
        st.warning("Es fehlt noch: " + ", ".join(fehlend))
        st.stop()

    e = pfade.lade_einstellungen()
    with st.expander("Sensor und Modellparameter", expanded=True):
        a, b, c = st.columns(3)
        zm = a.number_input("Messhöhe zm [m]", value=float(e["zm"]), min_value=0.1, step=0.1)
        z0 = a.number_input("Rauigkeitslänge z0 [m]", value=float(e["z0"]), min_value=0.001,
                            step=0.01, format="%.3f")
        h = a.number_input("Grenzschichthöhe h [m]", value=float(e["h"]), min_value=100.0, step=50.0)
        lat0 = b.number_input("Breitengrad Sensor", value=float(e["lat0"]), format="%.5f")
        lon0 = b.number_input("Längengrad Sensor", value=float(e["lon0"]), format="%.5f")
        epsg = b.text_input("UTM-Zone (EPSG)", value=e["epsg"],
                            help="Norddeutschland: EPSG:32632 · Frankreich West: EPSG:32630 · Ost: EPSG:32631")
        domain = c.number_input("Domäne ± [m]", value=int(e["domain"]), min_value=50, step=50)
        dx = c.number_input("Gitterauflösung [m]", value=int(e["dx"]), min_value=1, step=1)
        rs = c.multiselect("Konturen [% der Quellfläche]", [10, 20, 30, 40, 50, 60, 70, 80, 90],
                           default=e["rs"])
        sigmav_faktor = st.number_input("σv ≈ Faktor · u*", value=float(e["sigmav_faktor"]), step=0.1,
                                        help="σv wird nicht gemessen und daher aus u* genähert.")
        if st.button("Als Standard speichern"):
            pfade.speichere_einstellungen({**e, "zm": zm, "z0": z0, "h": h, "lat0": lat0, "lon0": lon0,
                                           "epsg": epsg, "domain": domain, "dx": dx, "rs": rs,
                                           "sigmav_faktor": sigmav_faktor})
            st.success("Gespeichert.")

    p = {"zm": zm, "z0": z0, "h": h, "lat0": lat0, "lon0": lon0, "epsg": epsg, "domain": domain,
         "dx": dx, "rs": rs or [50], "sigmav_faktor": sigmav_faktor}

    try:
        tab_alle, n_flux = fp.lade_tabelle()
        tab_gueltig, n_ung = fp.filtere_gueltig(tab_alle, zm)
    except Exception as ex:
        st.error(f"Dateien konnten nicht gelesen werden: {ex}")
        st.stop()
    if tab_gueltig.empty:
        st.error("Keine gültigen Zeitschritte (u* > 0,1 m/s und zm/L > −15,5 nötig).")
        st.stop()

    st.info(f"{len(tab_alle)} Zeitschritte mit Fluss UND Wind (von {n_flux}); "
            f"{n_ung} außerhalb der FFP-Gültigkeit werden übersprungen → "
            f"**{len(tab_gueltig)} Footprints möglich**.")

    t0, t1 = tab_gueltig["Zeit"].min().to_pydatetime(), tab_gueltig["Zeit"].max().to_pydatetime()
    zeitraum = st.slider("Zeitraum", min_value=t0, max_value=t1, value=(t0, t1), format="DD.MM.YY HH:mm")
    auswahl = tab_gueltig[(tab_gueltig["Zeit"] >= zeitraum[0]) & (tab_gueltig["Zeit"] <= zeitraum[1])]

    c1, c2 = st.columns(2)
    ausgabe = c1.radio("Ausgabe", ["Bilder", "Video", "Bilder und Video"], horizontal=True)
    hg = c2.selectbox("Hintergrundkarte", list(fp.HINTERGRUND))
    sek = 3.0
    if "Video" in ausgabe:
        sek = st.slider("Sekunden pro Bild im Video", 0.5, 10.0, 3.0, 0.5)
    loeschen = st.checkbox("Alte Bilder im Ordner vor dem Lauf löschen", value=True) if "Bilder" in ausgabe else False
    if hg != "Ohne Hintergrundkarte":
        st.caption("Die Hintergrundkarte braucht beim ersten Mal Internet und wird danach zwischengespeichert.")

    if st.button(f"{len(auswahl)} Footprints erzeugen", type="primary", disabled=auswahl.empty):
        balken = st.progress(0.0, text="Starte …")
        try:
            res = fp.erzeuge_ausgaben(auswahl, p, bilder="Bilder" in ausgabe, video="Video" in ausgabe,
                                      sek_pro_bild=sek, hintergrund_name=hg, alte_bilder_loeschen=loeschen,
                                      fortschritt=lambda x, t: balken.progress(min(x, 1.0), text=t))
            balken.progress(1.0, text="Fertig")
            if res.get("hinweis"):
                st.warning(res["hinweis"])
            if res.get("anzahl"):
                st.success(f"{res['anzahl']} Footprints erzeugt. Ergebnisse in den Reitern „Bilder ansehen“ / "
                           f"„Video ansehen“.")
            if res["meldungen"]:
                with st.expander(f"{len(res['meldungen'])} Meldungen"):
                    st.write("\n".join(res["meldungen"]))
        except Exception as ex:
            st.error(f"Fehler: {ex}")

# =============================================================== Bilder
with tab_bilder:
    bilder = fp.bilder_liste()
    if not bilder:
        st.info("Noch keine Bilder. Erst unter „Berechnen“ erzeugen.")
    else:
        st.caption(f"{len(bilder)} Bilder in {pfade.BILDER_DIR}")
        namen = [b.stem.replace("footprint_", "") for b in bilder]
        wahl = st.select_slider("Zeitschritt (JJJJMMTT_HHMM)", options=namen, value=namen[0])
        st.image(str(bilder[namen.index(wahl)]), use_container_width=True)
        if st.checkbox("ZIP aller Bilder vorbereiten"):
            st.download_button("ZIP herunterladen", fp.bilder_als_zip(), file_name="footprint_bilder.zip")

# =============================================================== Video
with tab_video:
    if not pfade.VIDEO_DATEI.exists():
        st.info("Noch kein Video. Erst unter „Berechnen“ mit Ausgabe „Video“ erzeugen.")
    else:
        st.caption(str(pfade.VIDEO_DATEI))
        daten = pfade.VIDEO_DATEI.read_bytes()
        st.video(daten)
        st.download_button("Video herunterladen", daten, file_name=pfade.VIDEO_DATEI.name, mime="video/mp4")

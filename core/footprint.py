"""Schritt 3: Footprints berechnen und als Bilder / Video ausgeben
(aus footprints_erzeugen.py, footprints_Video_erzeugen.py und plot_footprint_osm)."""
import hashlib
import io
from pathlib import Path

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")                     # kein Fenster: nur Dateien erzeugen
import matplotlib.pyplot as plt

from . import pfade
from .aufbereitung import lese_wind
from .ffp_modell import FFP_climatology

USER_AGENT = "FFP-Footprint-Uni/1.0 (i.tzeutong@ostfalia.de)"

# Name in der Oberfläche -> Funktion, die den contextily-Anbieter liefert
HINTERGRUND = {
    "Satellit (Esri WorldImagery)": lambda cx: cx.providers.Esri.WorldImagery,
    "OpenStreetMap": lambda cx: cx.providers.OpenStreetMap.Mapnik,
    "Topographie (OpenTopoMap)": lambda cx: cx.providers.OpenTopoMap,
    "Ohne Hintergrundkarte": None,
}


# --------------------------------------------------------------------------- Daten
def lade_tabelle(flux_pfad=None, wind_pfad=None):
    """Fluss/Obukhov-Datei und Winddatei zusammenführen (nur identische Zeiten)."""
    flux = pd.read_csv(flux_pfad or pfade.OBUKHOV_DATEI, sep=";", decimal=",", encoding="utf-8-sig")
    flux.columns = [c.strip() for c in flux.columns]
    # "26-10-25 11:00:00 +0000" -> das "+0000" wird abgeschnitten
    flux["Zeit"] = pd.to_datetime(flux["Date"].str[:17], format="%y-%m-%d %H:%M:%S")
    wind = lese_wind(wind_pfad or pfade.WIND_DATEI)
    tab = flux.merge(wind, on="Zeit")
    tab = tab.dropna(subset=["Obukhov_Laenge", "u_star", "Wind_Direction"]).reset_index(drop=True)
    return tab, len(flux)


def filtere_gueltig(tab, zm):
    """Nur Zeitschritte innerhalb der FFP-Gültigkeit (u* > 0,1 und zm/L > -15,5)."""
    gueltig = (tab["u_star"] > 0.1) & (zm / tab["Obukhov_Laenge"] > -15.5)
    return tab[gueltig].reset_index(drop=True), int((~gueltig).sum())


# --------------------------------------------------------------------------- Berechnung
def berechne_footprints(tab, p, fortschritt=None):
    """Ein Footprint pro Zeile von tab. Gibt (Liste[(zeit, F, fr)], Gitter, Meldungen) zurück."""
    d = p["domain"]
    ergebnisse, meldungen, gitter = [], [], None
    n = len(tab)
    for i in range(n):
        zeit = tab["Zeit"].iloc[i]
        try:
            FFP = FFP_climatology(
                zm=p["zm"], z0=p["z0"], umean=None, h=[p["h"]],
                ol=[tab["Obukhov_Laenge"].iloc[i]],
                sigmav=[p["sigmav_faktor"] * tab["u_star"].iloc[i]],
                ustar=[tab["u_star"].iloc[i]],
                wind_dir=[tab["Wind_Direction"].iloc[i]],
                domain=[-d, d, -d, d], dx=p["dx"], dy=p["dx"],
                rs=[r / 100 for r in p["rs"]], fig=False, verbosity=0)
            if FFP["n"] > 0:
                if gitter is None:
                    gitter = (FFP["x_2d"], FFP["y_2d"])
                ergebnisse.append((zeit, FFP["fclim_2d"].astype(np.float32), FFP["fr"]))
            else:
                meldungen.append(f"{zeit}: ignoriert (ungültige FFP-Werte)")
        except Exception as fehler:
            meldungen.append(f"{zeit}: Fehler – {fehler}")
        if fortschritt:
            fortschritt((i + 1) / n * 0.4, f"Berechne Footprints … {i + 1}/{n}")
    return ergebnisse, gitter, meldungen


# --------------------------------------------------------------------------- Hintergrundkarte
def _utm(p):
    from pyproj import Transformer
    return Transformer.from_crs("EPSG:4326", p["epsg"], always_xy=True)


def lade_hintergrund(p, quelle):
    """Lädt die Kartenkacheln EINMAL für den ganzen Ausschnitt (alle Bilder haben denselben).
    Gibt (bild, extent) oder (None, None) zurück; Ergebnis wird im Cache-Ordner abgelegt."""
    if quelle not in HINTERGRUND or HINTERGRUND[quelle] is None:
        return None, None
    schluessel = hashlib.md5(repr((quelle, p["lat0"], p["lon0"], p["epsg"], p["domain"],
                                    p.get("zoom"))).encode()).hexdigest()[:12]
    cache = pfade.CACHE_DIR / f"hintergrund_{schluessel}.npz"
    if cache.exists():
        z = np.load(cache)
        return z["bild"], tuple(z["extent"])

    import contextily as cx
    from pyproj import Transformer
    d = p["domain"]
    x0, y0 = _utm(p).transform(p["lon0"], p["lat0"])
    zurueck = Transformer.from_crs(p["epsg"], "EPSG:4326", always_xy=True)
    ecken = [zurueck.transform(x0 + sx * d, y0 + sy * d) for sx in (-1, 1) for sy in (-1, 1)]
    west, east = min(e[0] for e in ecken), max(e[0] for e in ecken)
    south, north = min(e[1] for e in ecken), max(e[1] for e in ecken)

    cx.tile.USER_AGENT = USER_AGENT
    anbieter = HINTERGRUND[quelle](cx)
    bild, ext = cx.bounds2img(west, south, east, north, zoom=p.get("zoom") or "auto",
                              source=anbieter, ll=True)
    bild, ext = cx.warp_tiles(bild, ext, t_crs=p["epsg"])
    np.savez_compressed(cache, bild=bild, extent=np.array(ext))
    return bild, tuple(ext)


# --------------------------------------------------------------------------- Zeichnen
def zeichne(zeit, F, fr, gitter, p, vmax, hintergrund, cmap="jet", alpha=0.55):
    x0, y0 = _utm(p).transform(p["lon0"], p["lat0"])
    X, Y = gitter[0] + x0, gitter[1] + y0

    fig, ax = plt.subplots(figsize=(10, 8))
    # nahezu null liegende Werte ausblenden (0,1 % des Maximums)
    F_masked = np.ma.masked_less_equal(F, F.max() * 0.001)
    im = ax.pcolormesh(X, Y, F_masked, cmap=cmap, alpha=alpha, shading="auto", vmin=0, vmax=vmax)

    levels = sorted([f for f in fr if f is not None])
    if levels:
        try:
            ax.contour(X, Y, F, levels=levels, colors="k", linewidths=0.8)
        except Exception:
            pass
    ax.plot(x0, y0, "r^", markersize=10, label="Sensor LI-710")

    if hintergrund[0] is not None:
        ax.imshow(hintergrund[0], extent=hintergrund[1], zorder=-1, interpolation="bilinear")
    ax.set_xlim(X.min(), X.max())
    ax.set_ylim(Y.min(), Y.max())

    fig.colorbar(im, ax=ax, label="Flussbeitrag [m$^{-2}$]", format="%.2e")
    ax.set_xlabel("Rechtswert / Easting [m] (UTM)")
    ax.set_ylabel("Hochwert / Northing [m] (UTM)")
    ax.set_title(f"Footprint {zeit:%Y-%m-%d %H:%M} UTC")
    ax.legend(loc="upper right")
    return fig


# --------------------------------------------------------------------------- Ausgabe
def erzeuge_ausgaben(tab, p, bilder=True, video=False, sek_pro_bild=3.0, hintergrund_name=None,
                     alte_bilder_loeschen=True, fortschritt=None):
    """Kompletter Ablauf: rechnen -> Bilder (PNG) und/oder Video (MP4) speichern."""
    pfade.ordner_anlegen()
    ergebnisse, gitter, meldungen = berechne_footprints(tab, p, fortschritt)
    if not ergebnisse:
        return {"bilder": 0, "video": None, "meldungen": meldungen, "hinweis": "Keine gültigen Footprints."}

    hinweis = ""
    try:
        hg = lade_hintergrund(p, hintergrund_name)
    except Exception as e:
        hg = (None, None)
        hinweis = f"Hintergrundkarte konnte nicht geladen werden ({e}). Bilder ohne Karte erzeugt."

    vmax = max(float(F.max()) for _, F, _ in ergebnisse)    # gleiche Farbskala für alle Bilder
    if bilder and alte_bilder_loeschen:
        for f in pfade.BILDER_DIR.glob("footprint_*.png"):
            f.unlink()

    writer, video_pfad = None, None
    dpi_video, ausgabe_fps = 100, 10
    if video:
        video_pfad = pfade.VIDEO_DATEI
        video_pfad.parent.mkdir(parents=True, exist_ok=True)
        writer = _video_writer(video_pfad, ausgabe_fps)
    wiederholungen = max(1, round(sek_pro_bild * ausgabe_fps))
    breite, hoehe = int(round(10 * dpi_video)), int(round(8 * dpi_video))

    n = len(ergebnisse)
    try:
        for i, (zeit, F, fr) in enumerate(ergebnisse):
            fig = zeichne(zeit, F, fr, gitter, p, vmax, hg)
            if bilder:
                fig.savefig(pfade.BILDER_DIR / f"footprint_{zeit:%Y%m%d_%H%M}.png", dpi=150)
            if writer is not None:
                puffer = io.BytesIO()
                fig.savefig(puffer, format="rgba", dpi=dpi_video)
                bild = np.frombuffer(puffer.getvalue(), np.uint8).reshape(hoehe, breite, 4)[..., :3]
                for _ in range(wiederholungen):
                    writer.append_data(bild)
            plt.close(fig)
            if fortschritt:
                fortschritt(0.4 + (i + 1) / n * 0.6, f"Erzeuge Ausgabe … {i + 1}/{n}")
    finally:
        if writer is not None:
            writer.close()

    return {"bilder": n if bilder else 0, "video": video_pfad, "meldungen": meldungen,
            "hinweis": hinweis, "anzahl": n}


def _video_writer(pfad, fps):
    """H.264-MP4 (läuft auch im Browser). Benötigt imageio-ffmpeg."""
    import imageio.v2 as imageio
    return imageio.get_writer(str(pfad), fps=fps, codec="libx264", pixelformat="yuv420p",
                              macro_block_size=2, quality=7,
                              ffmpeg_params=["-movflags", "+faststart"])


def bilder_liste():
    return sorted(pfade.BILDER_DIR.glob("footprint_*.png"))


def bilder_als_zip():
    puffer = io.BytesIO()
    import zipfile
    with zipfile.ZipFile(puffer, "w", zipfile.ZIP_STORED) as z:
        for f in bilder_liste():
            z.write(f, f.name)
    return puffer.getvalue()

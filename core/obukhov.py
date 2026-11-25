"""Schritt 2: Luftdichte, kinematischer Wärmefluss, u* und Obukhov-Länge
(aus Obukhov.py)."""
from pathlib import Path

import numpy as np
import pandas as pd

from . import pfade

RD = 287.058            # spezifische Gaskonstante trockene Luft [J/(kg K)]
CP = 1005               # spezifische Wärmekapazität [J/(kg K)]
KARMAN_KONSTANTE = 0.40
G = 9.81                # Erdbeschleunigung

BENOETIGT = ["Sensible_Heat_Flux", "Air_Temperature", "Atmospheric_Pressure", "W_StandardDeviation"]


def lade_kwf(pfad=None):
    df = pd.read_csv(pfad or pfade.KWF_DATEI, sep=";", decimal=",", encoding="utf-8-sig")
    df.columns = [c.strip() for c in df.columns]
    return df


def berechne(df, u_star_faktor=1.25):
    """Berechnet Luftdichte, kinematischen Wärmefluss, u* und Obukhov-Länge."""
    df = df.copy()
    for col in BENOETIGT:
        if col not in df.columns:
            raise ValueError(f"Die benötigte Spalte '{col}' fehlt in der Datei.")

    df["Luftdichte"] = (df["Atmospheric_Pressure"] * 1000) / (RD * (df["Air_Temperature"] + 273.15))
    df["kinematischer_waermefluss"] = np.where(
        df["Luftdichte"] > 0, df["Sensible_Heat_Flux"] / (df["Luftdichte"] * CP), np.nan)

    # Näherung: u* = Standardabweichung von w / Faktor (Standard 1,25)
    u_star = df["W_StandardDeviation"] / u_star_faktor
    df["u_star"] = u_star
    df["Obukhov_Laenge"] = np.where(
        df["kinematischer_waermefluss"] != 0,
        -(u_star ** 3) * (df["Air_Temperature"] + 273.15)
        / (KARMAN_KONSTANTE * G * df["kinematischer_waermefluss"]),
        np.nan)
    return df


def speichere(df, pfad=None):
    pfad = Path(pfad or pfade.OBUKHOV_DATEI)
    pfad.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(pfad, sep=";", decimal=",", index=False, encoding="utf-8-sig")
    return pfad


def lade_ergebnis(pfad=None):
    df = pd.read_csv(pfad or pfade.OBUKHOV_DATEI, sep=";", decimal=",", encoding="utf-8-sig")
    df.columns = [c.strip() for c in df.columns]
    return df

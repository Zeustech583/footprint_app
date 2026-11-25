#!/usr/bin/env bash
# Startet die Footprint-App (beim ersten Mal wird alles installiert).
cd "$(dirname "$0")"
[ -d .venv ] || python3 -m venv .venv
if [ ! -f .venv/installiert.txt ]; then
  .venv/bin/python -m pip install --upgrade pip
  .venv/bin/python -m pip install -r requirements.txt && echo ok > .venv/installiert.txt
fi
.venv/bin/python -m streamlit run app.py

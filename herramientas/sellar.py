#!/usr/bin/env python3
"""Sella un pick ANTES del saque sin revelarlo (commit-reveal).

Publica solo: id, hora de sello, partido, liga, mercado y un HASH.
El pick real (lado/linea/cuota) + un nonce secreto se guardan aparte
(picks_pendientes/, NO se sube al repo) hasta que se revela tras el partido.
Asi queda probado que el pick existia antes del saque, sin regalarselo a nadie.

Uso:
  python3 sellar.py --partido "Angouleme-Agen" --liga "Pro D2" \
     --mercado handicap --seleccion "Local -7.5" --linea -7.5 --cuota 1.78 \
     --confianza baja --saque 2026-11-21T20:00:00+01:00
"""
import argparse, json, hashlib, secrets, datetime, os, pathlib

BASE = pathlib.Path(__file__).resolve().parent.parent
REG = BASE / "registro_publico.jsonl"
PEND = BASE / "picks_pendientes"

def ahora_madrid():
    # offset fijo +01:00 (CET); en verano el usuario pasa +02:00 a mano si hace falta
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=1))).isoformat()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--partido", required=True)
    ap.add_argument("--liga", required=True)
    ap.add_argument("--mercado", required=True, choices=["handicap","total"])
    ap.add_argument("--seleccion", required=True, help="p.ej. 'Local -7.5' o 'Mas de 50.5'")
    ap.add_argument("--linea", required=True, type=float)
    ap.add_argument("--cuota", required=True, type=float)
    ap.add_argument("--confianza", default="baja")
    ap.add_argument("--saque", required=True, help="ISO del saque, p.ej 2026-11-21T20:00:00+01:00")
    a = ap.parse_args()

    seal_ts = ahora_madrid()
    # id legible y unico
    n = sum(1 for _ in REG.open()) + 1 if REG.exists() else 1
    pid = f"{n:04d}-{a.partido.replace(' ','_').replace('/','-')[:30]}-{a.mercado}"

    secreto = {
        "partido": a.partido, "liga": a.liga, "mercado": a.mercado,
        "seleccion": a.seleccion, "linea": a.linea, "cuota": a.cuota,
        "confianza": a.confianza, "saque": a.saque, "seal_ts": seal_ts,
        "nonce": secrets.token_hex(16),
    }
    plano = json.dumps(secreto, sort_keys=True, ensure_ascii=False)
    commit = hashlib.sha256(plano.encode("utf-8")).hexdigest()

    PEND.mkdir(exist_ok=True)
    (PEND / f"{pid}.json").write_text(json.dumps(secreto, ensure_ascii=False, indent=2), encoding="utf-8")

    publico = {
        "id": pid, "sellado_ts": seal_ts, "partido": a.partido, "liga": a.liga,
        "mercado": a.mercado, "saque": a.saque, "commit_sha256": commit,
        "estado": "SELLADO", "revelado": None,
    }
    with REG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(publico, ensure_ascii=False) + "\n")

    print(f"✅ SELLADO {pid}")
    print(f"   hora de sello: {seal_ts}")
    print(f"   hash publico : {commit}")
    print(f"   (pick guardado en secreto; se revela tras el partido con revelar.py)")

if __name__ == "__main__":
    main()

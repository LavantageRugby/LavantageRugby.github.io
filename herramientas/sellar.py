#!/usr/bin/env python3
"""Sella un pick ANTES del saque sin revelarlo (commit-reveal ENCADENADO).

Publica solo: id, seq, hora de sello, partido, liga, mercado, saque, el HASH del
pick y el hash del pick ANTERIOR (prev_hash). El pick real (lado/linea/cuota) + un
nonce secreto se guardan aparte (picks_pendientes/, NO se sube al repo) hasta que se
revela tras el partido.

Por que ENCADENADO (anti-cherry-picking): cada sello incluye el hash del anterior, asi
que la lista es una cadena. No se puede borrar, insertar ni reordenar un pick sin romper
la cadena. Y como verificar.py exige que TODO sello pasado su saque este revelado, no se
puede esconder un perdido "dejandolo sellado para siempre": salta solo.

Prueba de HORA: la fecha del commit de git NO prueba nada (la pone el autor). La prueba
real es la HORA DE PUSH que registra GitHub (no reescribible) -> SELLAR Y EMPUJAR (push)
ANTES del saque. Ver METODOLOGIA.md.

Uso:
  python3 sellar.py --partido "Angouleme-Agen" --liga "Pro D2" \
     --mercado handicap --seleccion "Local -7.5" --linea -7.5 --cuota 1.78 \
     --confianza baja --saque 2026-11-21T20:00:00+01:00
"""
import argparse, json, hashlib, secrets, datetime, pathlib

BASE = pathlib.Path(__file__).resolve().parent.parent
REG = BASE / "registro_publico.jsonl"
PEND = BASE / "picks_pendientes"
GENESIS = "GENESIS"  # prev_hash del primer pick

def ahora_madrid():
    # offset fijo +01:00 (CET); en verano el usuario pasa +02:00 a mano si hace falta
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=1))).isoformat()

def leer_registro():
    return [json.loads(l) for l in REG.open(encoding="utf-8")] if REG.exists() else []

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
    filas = leer_registro()
    seq = len(filas) + 1
    prev_hash = filas[-1]["commit_sha256"] if filas else GENESIS
    pid = f"{seq:04d}-{a.partido.replace(' ','_').replace('/','-')[:30]}-{a.mercado}"

    # El secreto INCLUYE seq y prev_hash -> quedan fijados en el hash (no se pueden alterar luego).
    secreto = {
        "seq": seq, "prev_hash": prev_hash,
        "partido": a.partido, "liga": a.liga, "mercado": a.mercado,
        "seleccion": a.seleccion, "linea": a.linea, "cuota": a.cuota,
        "confianza": a.confianza, "saque": a.saque, "seal_ts": seal_ts,
        "nonce": secrets.token_hex(16),
    }
    plano = json.dumps(secreto, sort_keys=True, ensure_ascii=False)
    commit = hashlib.sha256(plano.encode("utf-8")).hexdigest()

    PEND.mkdir(exist_ok=True)
    (PEND / f"{pid}.json").write_text(json.dumps(secreto, ensure_ascii=False, indent=2), encoding="utf-8")

    # prev_hash y seq van tambien en la linea PUBLICA -> la cadena es comprobable por cualquiera.
    publico = {
        "id": pid, "seq": seq, "prev_hash": prev_hash, "sellado_ts": seal_ts,
        "partido": a.partido, "liga": a.liga, "mercado": a.mercado, "saque": a.saque,
        "commit_sha256": commit, "estado": "SELLADO", "revelado": None,
    }
    with REG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(publico, ensure_ascii=False) + "\n")

    print(f"SELLADO #{seq} {pid}")
    print(f"   hora de sello: {seal_ts}")
    print(f"   prev_hash    : {prev_hash[:16]}{'...' if prev_hash!=GENESIS else ''}")
    print(f"   hash publico : {commit}")
    print(f"   AVISO: EMPUJA (git push) AHORA, ANTES del saque: la hora del push de GitHub es la prueba.")

if __name__ == "__main__":
    main()

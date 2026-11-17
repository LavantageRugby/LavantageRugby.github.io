#!/usr/bin/env python3
"""Verificador PUBLICO. Cualquiera puede ejecutarlo para comprobar que el registro
es honesto. Falla (codigo de salida 1) si detecta cualquier trampa:

  1) HASH: cada pick revelado coincide EXACTAMENTE con el hash que se sello antes del
     saque -> imposible cambiar el pick despues.
  2) SELLO ANTES DEL SAQUE: la hora de sello es anterior al saque.
  3) CADENA (anti-cherry-picking): cada pick incluye el hash del anterior (prev_hash);
     la cadena tiene que ser continua y en orden. No se puede borrar, insertar ni
     reordenar picks.
  4) SIN PERDIDOS ESCONDIDOS: ningun pick puede quedar SELLADO (sin revelar) despues de
     su saque. Si el partido ya se jugo, el pick DEBE estar revelado. Asi un perdido
     escondido "dejandolo sellado" salta solo.

OJO con la HORA: la fecha del commit de git NO es prueba (la pone el autor). La prueba de
que el pick existia antes del saque es la HORA DE PUSH de GitHub (no reescribible) + la
rama protegida sin force-push. Ver METODOLOGIA.md.

Uso:  python3 verificar.py
"""
import json, hashlib, pathlib, datetime, sys

BASE = pathlib.Path(__file__).resolve().parent.parent
REG = BASE / "registro_publico.jsonl"
SELL = BASE / "picks_sellados"
GENESIS = "GENESIS"
HASH_KEYS = ("seq","prev_hash","partido","liga","mercado","seleccion","linea",
             "cuota","confianza","saque","seal_ts","nonce")

def dt(s):
    return datetime.datetime.fromisoformat(s)

def main():
    if not REG.exists() or REG.stat().st_size == 0:
        print("No hay registro todavia. (Arrancamos muy pronto.)"); return 0
    filas = [json.loads(l) for l in REG.open(encoding="utf-8")]
    filas.sort(key=lambda r: r.get("seq", 0))
    ahora = datetime.datetime.now(datetime.timezone.utc)

    problemas = []
    ok=0; aciertos=fallos=0; neto=0.0; clvs=[]; antes=0; total_rev=0
    prev = GENESIS
    seq_esperada = 1

    for r in filas:
        rid = r["id"]
        # 3) CADENA
        if r.get("seq") != seq_esperada:
            problemas.append(f"CADENA rota: esperaba seq {seq_esperada} y hay {r.get('seq')} ({rid})")
        if r.get("prev_hash") != prev:
            problemas.append(f"CADENA rota en {rid}: prev_hash no apunta al pick anterior")
        seq_esperada += 1
        prev = r["commit_sha256"]

        if r["estado"] == "REVELADO":
            total_rev += 1
            sec = json.loads((SELL / f"{rid}.json").read_text(encoding="utf-8"))
            base = {k: sec[k] for k in HASH_KEYS}
            h = hashlib.sha256(json.dumps(base, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            if h == r["commit_sha256"]:
                ok += 1
                if dt(sec["seal_ts"]) < dt(sec["saque"]):
                    antes += 1
                else:
                    problemas.append(f"{rid}: sellado DESPUES del saque")
            else:
                problemas.append(f"{rid}: HASH NO COINCIDE (pick alterado tras sellar)")
            rv = r["revelado"]
            if rv["resultado"] == "acierto": aciertos += 1
            elif rv["resultado"] == "fallo": fallos += 1
            neto += rv["neto"]
            if rv.get("clv_ev") is not None: clvs.append(rv["clv_ev"])
        else:
            # 4) SELLADO: no puede estar vencido sin revelar
            if dt(r["saque"]) < ahora:
                problemas.append(f"{rid}: SELLADO pero su saque ({r['saque']}) ya paso y NO se ha revelado "
                                 f"(posible perdido escondido)")

    print("="*58)
    print(f"Picks en el registro : {len(filas)}  (revelados {total_rev})")
    print(f"Hash correcto        : {ok}/{total_rev}")
    print(f"Sellados ANTES saque : {antes}/{ok}")
    print(f"Balance              : {aciertos}-{fallos}   neto {neto:+.3f} u")
    if clvs:
        m = sum(clvs)/len(clvs); baten = sum(1 for c in clvs if c>0)
        print(f"CLV medio vs cierre  : {m:+.2%}  ({baten}/{len(clvs)} baten el cierre)")
    print("="*58)
    if problemas:
        print(f"INTEGRIDAD: {len(problemas)} PROBLEMA(S) -- registro NO fiable:")
        for p in problemas: print(f"   - {p}")
        return 1
    print("INTEGRIDAD: OK -- cadena continua, todo sello revelado a tiempo, ningun hash alterado.")
    return 0

if __name__ == "__main__":
    sys.exit(main())

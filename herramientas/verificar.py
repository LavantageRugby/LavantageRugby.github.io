#!/usr/bin/env python3
"""Verificador PUBLICO. Cualquiera puede ejecutarlo para comprobar que:
  1) cada pick revelado coincide EXACTAMENTE con el hash que se sello antes del saque
     (imposible cambiar el pick despues -> anti-truco),
  2) la hora de sello es anterior al saque.
Y resume el balance y el CLV.

Uso:  python3 verificar.py
"""
import json, hashlib, pathlib, datetime

BASE = pathlib.Path(__file__).resolve().parent.parent
REG = BASE / "registro_publico.jsonl"
SELL = BASE / "picks_sellados"

def main():
    if not REG.exists():
        print("No hay registro todavia."); return
    filas = [json.loads(l) for l in REG.open(encoding="utf-8")]
    ok=bad=0; aciertos=fallos=0; neto=0.0; clvs=[]; antes=0; total_rev=0
    for r in filas:
        if r["estado"] != "REVELADO":
            continue
        total_rev += 1
        sec = json.loads((SELL / f"{r['id']}.json").read_text(encoding="utf-8"))
        base = {k:sec[k] for k in ("partido","liga","mercado","seleccion","linea",
                                   "cuota","confianza","saque","seal_ts","nonce")}
        h = hashlib.sha256(json.dumps(base, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        if h == r["commit_sha256"]:
            ok += 1
            # sello anterior al saque?
            if datetime.datetime.fromisoformat(sec["seal_ts"]) < datetime.datetime.fromisoformat(sec["saque"]):
                antes += 1
        else:
            bad += 1
            print(f"  ❌ HASH NO COINCIDE en {r['id']} (pick alterado!)")
        rv = r["revelado"]
        if rv["resultado"]=="acierto": aciertos+=1
        elif rv["resultado"]=="fallo": fallos+=1
        neto += rv["neto"]
        if rv.get("clv_ev") is not None: clvs.append(rv["clv_ev"])

    print("="*52)
    print(f"Picks revelados      : {total_rev}")
    print(f"Hash correcto        : {ok}/{total_rev}" + ("  ✅ todo integro" if bad==0 else f"  ⚠️ {bad} alterados"))
    print(f"Sellados ANTES saque : {antes}/{ok}")
    print(f"Balance              : {aciertos}-{fallos}   neto {neto:+.3f} u")
    if clvs:
        m = sum(clvs)/len(clvs); baten = sum(1 for c in clvs if c>0)
        print(f"CLV medio vs cierre  : {m:+.2%}  ({baten}/{len(clvs)} baten el cierre)")
    print("="*52)

if __name__ == "__main__":
    main()

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
ANCLAS = BASE / "anclas_ots"
GENESIS = "GENESIS"
HASH_KEYS = ("seq","prev_hash","partido","liga","estrategia","mercado","seleccion","linea",
             "cuota","casa","pin_sello","pin_contrario","limite","fixture_id","market_id",
             "outcome_id","snapshot_sha256","ejecucion","confianza","saque","seal_ts",
             "mins_antes_saque","nonce")

def dt(s):
    return datetime.datetime.fromisoformat(s)

def main():
    if not REG.exists() or REG.stat().st_size == 0:
        print("No hay registro todavia. (Arrancamos muy pronto.)"); return 0
    filas = [json.loads(l) for l in REG.open(encoding="utf-8")]
    filas.sort(key=lambda r: r.get("seq", 0))
    ahora = datetime.datetime.now(datetime.timezone.utc)

    problemas = []
    ok=0; aciertos=fallos=0; neto=0.0; staked=0.0; clvs=[]; mins=[]; antes=0; total_rev=0
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

        # ANCLA OTS: cada pick debe tener su prueba de hora permanente, y el hash anclado
        # debe ser el del pick. (La verificacion Bitcoin completa: `ots verify` -- ver METODOLOGIA.)
        hf = ANCLAS / f"{rid}.sha256"; proof = ANCLAS / f"{rid}.sha256.ots"
        if not proof.exists():
            problemas.append(f"{rid}: FALTA la prueba OpenTimestamps (anclas_ots/{rid}.sha256.ots)")
        elif not hf.exists() or hf.read_text(encoding="utf-8").strip() != r["commit_sha256"]:
            problemas.append(f"{rid}: el hash anclado en OTS NO coincide con el commit del pick")

        # SNAPSHOT de mercado (si el pick declara uno): el fichero debe existir y casar con su hash.
        if r.get("snapshot_sha256"):
            snf = BASE / "snapshots" / f"{rid}.json"
            if not snf.exists() or hashlib.sha256(snf.read_bytes()).hexdigest() != r["snapshot_sha256"]:
                problemas.append(f"{rid}: el snapshot de mercado falta o no casa con su hash")

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
            staked += sec.get("stake", 0) or 0
            if sec.get("mins_antes_saque") is not None: mins.append(sec["mins_antes_saque"])
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
    roi = (neto/staked) if staked else 0.0
    print(f"Balance              : {aciertos}-{fallos}   neto {neto:+.3f} u sobre {staked:.1f} u jugadas")
    print(f"ROI                  : {roi:+.2%}   (muestra n={total_rev}; sin volumen NO concluye nada)")
    if clvs:
        m = sum(clvs)/len(clvs); baten = sum(1 for c in clvs if c>0)
        print(f"CLV medio vs cierre  : {m:+.2%}  ({baten}/{len(clvs)} baten el cierre)  -- leer SIEMPRE junto al ROI")
    if mins:
        mm = sorted(mins)[len(mins)//2]
        print(f"Antelacion al saque  : mediana {mm} min  (min {min(mins)} / max {max(mins)})")
    print("="*58)
    if problemas:
        print(f"INTEGRIDAD: {len(problemas)} PROBLEMA(S) -- registro NO fiable:")
        for p in problemas: print(f"   - {p}")
        return 1
    print("INTEGRIDAD: OK -- cadena continua, todo sello revelado a tiempo, ningun hash alterado,")
    print("            y cada pick tiene su prueba de hora OpenTimestamps (verificable con `ots verify`).")
    return 0

if __name__ == "__main__":
    sys.exit(main())

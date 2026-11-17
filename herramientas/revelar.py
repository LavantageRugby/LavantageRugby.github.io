#!/usr/bin/env python3
"""Revela un pick ya sellado, tras el partido, y anota el resultado.

Publica el pick completo + marcador + acierto/fallo + (opcional) cierre de
Pinnacle para el CLV. El hash original NO cambia: cualquiera puede comprobar
con verificar.py que lo revelado coincide con lo que se sello antes del saque.

Uso:
  python3 revelar.py --id 0001-Angouleme-Agen-handicap \
     --marcador "36-22" --resultado acierto \
     --cierre_pin 1.70        # cuota de cierre de Pinnacle en esa seleccion (opcional)
"""
import argparse, json, pathlib

BASE = pathlib.Path(__file__).resolve().parent.parent
REG = BASE / "registro_publico.jsonl"
PEND = BASE / "picks_pendientes"
SELL = BASE / "picks_sellados"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--marcador", required=True)
    ap.add_argument("--resultado", required=True, choices=["acierto","fallo","nula"])
    ap.add_argument("--cierre_pin", type=float, default=None,
                    help="cuota de cierre de Pinnacle en NUESTRA seleccion y A LA MISMA LINEA (para CLV)")
    ap.add_argument("--cierre_contrario", type=float, default=None,
                    help="cuota de cierre de Pinnacle del LADO CONTRARIO a la misma linea; con esto el CLV se mide SIN MARGEN (de-vig), que es lo correcto")
    a = ap.parse_args()

    pend = PEND / f"{a.id}.json"
    if not pend.exists():
        raise SystemExit(f"No encuentro el pick pendiente {a.id}")
    secreto = json.loads(pend.read_text(encoding="utf-8"))

    # neto en unidades a stake de la confianza (1 baja, 1.5 media-baja, 2 media, 2.5 media-alta, 3 alta)
    stake = {"baja":1,"media-baja":1.5,"media":2,"media-alta":2.5,"alta":3}.get(secreto["confianza"],1)
    if a.resultado == "acierto": neto = round(stake*(secreto["cuota"]-1),3)
    elif a.resultado == "fallo": neto = -stake
    else: neto = 0.0

    # CLV = EV de nuestra cuota contra el cierre de Pinnacle a la MISMA linea.
    # Lo correcto es contra el cierre SIN MARGEN (de-vig): si tenemos el lado contrario,
    # quitamos el margen; si no, usamos 1/cierre (con margen -> CLV algo infravalorado) y se avisa.
    clv = None; clv_metodo = None
    if a.cierre_pin:
        if a.cierre_contrario:
            p_fair = (1/a.cierre_pin) / (1/a.cierre_pin + 1/a.cierre_contrario)  # de-vig 2 vias
            clv_metodo = "sin_margen"
        else:
            p_fair = 1/a.cierre_pin
            clv_metodo = "con_margen"  # aproximado; falta el lado contrario
        clv = round(secreto["cuota"]*p_fair - 1, 4)  # >0 = batio el cierre

    SELL.mkdir(exist_ok=True)
    revel = dict(secreto, marcador=a.marcador, resultado=a.resultado, stake=stake, neto=neto,
                 cierre_pinnacle=a.cierre_pin, cierre_contrario=a.cierre_contrario,
                 clv_ev=clv, clv_metodo=clv_metodo)
    (SELL / f"{a.id}.json").write_text(json.dumps(revel, ensure_ascii=False, indent=2), encoding="utf-8")

    # actualizar la linea publica del registro
    lineas = [json.loads(l) for l in REG.open(encoding="utf-8")] if REG.exists() else []
    for r in lineas:
        if r["id"] == a.id:
            r["estado"] = "REVELADO"
            r["revelado"] = {k:secreto[k] for k in ("seleccion","linea","cuota","casa","confianza")}
            r["revelado"].update(marcador=a.marcador, resultado=a.resultado, stake=stake, neto=neto,
                                 cierre_pinnacle=a.cierre_pin, cierre_contrario=a.cierre_contrario,
                                 clv_ev=clv, clv_metodo=clv_metodo)
    with REG.open("w", encoding="utf-8") as f:
        for r in lineas: f.write(json.dumps(r, ensure_ascii=False)+"\n")

    pend.unlink()  # ya no es secreto
    nota_clv = ""
    if clv is not None:
        nota_clv = f" | CLV {clv:+.3%} ({'sin margen' if clv_metodo=='sin_margen' else 'con margen, aprox.'})"
    print(f"✅ REVELADO {a.id}: {secreto['seleccion']} @ {secreto['cuota']} ({secreto.get('casa','?')}) "
          f"-> {a.resultado} ({neto:+.3f} u){nota_clv}")

if __name__ == "__main__":
    main()

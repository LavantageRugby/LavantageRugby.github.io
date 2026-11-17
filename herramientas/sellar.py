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
     --casa Winamax --confianza baja --saque 2026-11-21T20:00:00+01:00 \
     --pin_sello 1.74 --limite "400 EUR"      # pin_sello/limite opcionales; en 1x2 se omite --linea
"""
import argparse, json, hashlib, secrets, datetime, pathlib, subprocess, os

BASE = pathlib.Path(__file__).resolve().parent.parent
REG = BASE / "registro_publico.jsonl"
PEND = BASE / "picks_pendientes"
ANCLAS = BASE / "anclas_ots"
OTS = os.environ.get("OTS", os.path.expanduser("~/.venv_ots/bin/ots"))
GENESIS = "GENESIS"  # prev_hash del primer pick

def anclar_ots(pid, commit):
    """Crea una prueba de hora PERMANENTE del hash con OpenTimestamps (anclada a Bitcoin).
    Deja anclas_ots/<pid>.sha256 (el hash) y <pid>.sha256.ots (la prueba). Cualquiera la
    verifica para siempre con `ots verify`, sin fiarse de nadie. Es la prueba que dura
    (la hora de push de GitHub caduca ~90 dias)."""
    ANCLAS.mkdir(exist_ok=True)
    hf = ANCLAS / f"{pid}.sha256"
    hf.write_text(commit + "\n", encoding="utf-8")
    if not pathlib.Path(OTS).exists():
        return ("FALTA_OTS", "no se encontro 'ots' (instala opentimestamps-client en ~/.venv_ots)")
    try:
        r = subprocess.run([OTS, "stamp", str(hf)], capture_output=True, text=True, timeout=90)
    except Exception as e:
        return ("ERROR", str(e))
    if (ANCLAS / f"{pid}.sha256.ots").exists():
        return ("OK", "")
    return ("ERROR", (r.stderr or r.stdout)[-200:])

def ahora_madrid():
    # offset fijo +01:00 (CET); en verano el usuario pasa +02:00 a mano si hace falta
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=1))).isoformat()

def leer_registro():
    return [json.loads(l) for l in REG.open(encoding="utf-8")] if REG.exists() else []

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--partido", required=True)
    ap.add_argument("--liga", required=True)
    ap.add_argument("--estrategia", default="PRE-NUM",
                    help="estrategia (se reporta por separado; solo algunas tienen senal): "
                         "DESC-TOT (total al descanso, regla T9), BLANDA-T30 (casa blanda >=3%% sobre justo ~30min antes), "
                         "PRE-NUM (numero a ciegas prepartido, es el CONTROL)")
    ap.add_argument("--mercado", required=True, choices=["handicap","total","1x2"])
    ap.add_argument("--seleccion", required=True,
                    help="p.ej. 'Local -7.5' (handicap), 'Mas de 50.5' (total), 'Local'/'Empate'/'Visitante' (1x2)")
    ap.add_argument("--linea", type=float, default=None,
                    help="linea del handicap/total; en 1x2 se OMITE (no aplica)")
    ap.add_argument("--cuota", required=True, type=float)
    ap.add_argument("--casa", required=True, help="casa de apuestas donde estaba esa cuota (bet365, Winamax, Betfair...)")
    ap.add_argument("--confianza", default="baja")
    ap.add_argument("--saque", required=True, help="ISO del saque, p.ej 2026-11-21T20:00:00+01:00")
    ap.add_argument("--pin_sello", type=float, default=None,
                    help="cuota de Pinnacle en ESA MISMA seleccion/linea en el momento del sello (prueba de que el precio existia y contexto de mercado)")
    ap.add_argument("--limite", default=None,
                    help="cuanto se podia jugar a ese precio: limite de la casa o liquidez en Betfair, p.ej '500 EUR'")
    # Referencia a OddsPapi: lo que hace la prueba de la cuota INDEPENDIENTE (cualquiera la re-consulta
    # en /historical-odds, no tiene que fiarse de nuestro JSON). Lo rellenan las sesiones de cuotas.
    ap.add_argument("--fixture_id", default=None, help="OddsPapi fixture_id (re-verificar en /historical-odds)")
    ap.add_argument("--market_id", default=None, help="OddsPapi market id")
    ap.add_argument("--outcome_id", default=None, help="OddsPapi outcome id")
    ap.add_argument("--pin_contrario", type=float, default=None,
                    help="cuota de Pinnacle del LADO CONTRARIO a la misma linea, al sellar")
    ap.add_argument("--snapshot_json", default=None,
                    help="ruta al JSON crudo de OddsPapi en el momento del sello; se copia al repo, se hashea y se ancla con OTS")
    ap.add_argument("--ejecucion", default="sellada_sin_ejecucion_comprobada",
                    help="estado de ejecucion. Por defecto 'cuota sellada, sin ejecucion comprobada' (historico). Si se jugo de verdad, se anota la cuota obtenida al revelar (slippage).")
    ap.add_argument("--op_foto", default=None,
                    help="ruta al JSON que saca `sello_op.py foto --casa pinnacle` (sesion de cuotas): rellena fixture/market/outcome/pin_sello/pin_contrario/limite que no pongas a mano")
    ap.add_argument("--op_crudo", default=None,
                    help="ruta al crudo .json.gz que cita ese JSON (datos/sellos_op/...); se descomprime, se guarda como snapshot y su sha256 debe casar con crudo_sha256")
    a = ap.parse_args()

    # Integracion con sello_op.py: rellenar SOLO los huecos (los flags explicitos mandan).
    op_sha_esperado = None
    if a.op_foto:
        op = json.loads(pathlib.Path(a.op_foto).read_text(encoding="utf-8"))
        if a.fixture_id is None: a.fixture_id = op.get("fixture_id")
        if a.market_id is None: a.market_id = op.get("market_id")
        if a.outcome_id is None: a.outcome_id = op.get("outcome_id")
        if a.limite is None: a.limite = (op.get("sello") or {}).get("limite")
        # pin_sello/pin_contrario solo si la foto es de Pinnacle (son la referencia de CLV)
        if op.get("casa") == "pinnacle":
            if a.pin_sello is None: a.pin_sello = (op.get("sello") or {}).get("cuota")
            if a.pin_contrario is None: a.pin_contrario = (op.get("contrario") or {}).get("cuota")
        else:
            print(f"   AVISO: --op_foto es de casa '{op.get('casa')}', no Pinnacle: no relleno pin_sello/pin_contrario.")
        op_sha_esperado = op.get("crudo_sha256")
        if a.op_crudo and a.snapshot_json is None:
            import gzip, tempfile
            plano = gzip.open(a.op_crudo, "rt", encoding="utf-8").read()
            tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
            tmp.write(plano); tmp.close(); a.snapshot_json = tmp.name

    if a.mercado in ("handicap","total") and a.linea is None:
        raise SystemExit("--linea es obligatoria para handicap/total (en 1x2 se omite).")

    # hash del snapshot de mercado (si se aporta) -> queda fijado en el sello y se ancla con OTS
    snap_sha = None
    if a.snapshot_json:
        snap_sha = hashlib.sha256(pathlib.Path(a.snapshot_json).read_bytes()).hexdigest()
        if op_sha_esperado and snap_sha != op_sha_esperado:
            raise SystemExit(f"El snapshot descomprimido NO casa con crudo_sha256 de OddsPapi "
                             f"({snap_sha[:12]} != {op_sha_esperado[:12]}); no sello con un snapshot dudoso.")

    # minutos de antelacion al saque (cuanto antes del cierre se sello)
    seal_ts = ahora_madrid()
    filas = leer_registro()
    seq = len(filas) + 1
    prev_hash = filas[-1]["commit_sha256"] if filas else GENESIS
    pid = f"{seq:04d}-{a.partido.replace(' ','_').replace('/','-')[:30]}-{a.mercado}"
    # antelacion al saque, en minutos: cuanto antes del cierre se sello (lo pide el sindicato)
    mins_antes = round((datetime.datetime.fromisoformat(a.saque)
                        - datetime.datetime.fromisoformat(seal_ts)).total_seconds() / 60)

    # El secreto INCLUYE seq y prev_hash -> quedan fijados en el hash (no se pueden alterar luego).
    secreto = {
        "seq": seq, "prev_hash": prev_hash,
        "partido": a.partido, "liga": a.liga, "estrategia": a.estrategia, "mercado": a.mercado,
        "seleccion": a.seleccion, "linea": a.linea, "cuota": a.cuota, "casa": a.casa,
        "pin_sello": a.pin_sello, "pin_contrario": a.pin_contrario, "limite": a.limite,
        "fixture_id": a.fixture_id, "market_id": a.market_id, "outcome_id": a.outcome_id,
        "snapshot_sha256": snap_sha, "ejecucion": a.ejecucion,
        "confianza": a.confianza, "saque": a.saque, "seal_ts": seal_ts,
        "mins_antes_saque": mins_antes, "nonce": secrets.token_hex(16),
    }
    plano = json.dumps(secreto, sort_keys=True, ensure_ascii=False)
    commit = hashlib.sha256(plano.encode("utf-8")).hexdigest()

    PEND.mkdir(exist_ok=True)
    (PEND / f"{pid}.json").write_text(json.dumps(secreto, ensure_ascii=False, indent=2), encoding="utf-8")

    # prev_hash y seq van tambien en la linea PUBLICA -> la cadena es comprobable por cualquiera.
    # fixture_id publico: permite re-verificar la cuota en OddsPapi/historical-odds SIN fiarse de nosotros.
    publico = {
        "id": pid, "seq": seq, "prev_hash": prev_hash, "sellado_ts": seal_ts,
        "partido": a.partido, "liga": a.liga, "estrategia": a.estrategia,
        "mercado": a.mercado, "casa": a.casa, "saque": a.saque, "mins_antes_saque": mins_antes,
        "fixture_id": a.fixture_id, "snapshot_sha256": snap_sha, "ejecucion": a.ejecucion,
        "commit_sha256": commit, "estado": "SELLADO", "revelado": None,
    }
    with REG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(publico, ensure_ascii=False) + "\n")

    # Copiar y ANCLAR el snapshot crudo de mercado (si se aporto): asi la foto de Pinnacle del
    # momento queda con su propia prueba de hora OTS. (La autenticidad real la da re-consultar el
    # fixture_id en OddsPapi/historical-odds; esto solo prueba que lo teniamos a esa hora.)
    if a.snapshot_json:
        SNAPS = BASE / "snapshots"; SNAPS.mkdir(exist_ok=True)
        dest = SNAPS / f"{pid}.json"
        dest.write_bytes(pathlib.Path(a.snapshot_json).read_bytes())
        if pathlib.Path(OTS).exists():
            try: subprocess.run([OTS, "stamp", str(dest)], capture_output=True, text=True, timeout=90)
            except Exception: pass

    estado_ots, detalle = anclar_ots(pid, commit)

    print(f"SELLADO #{seq} {pid}")
    print(f"   hora de sello: {seal_ts}  ({mins_antes} min antes del saque, casa: {a.casa})")
    print(f"   prev_hash    : {prev_hash[:16]}{'...' if prev_hash!=GENESIS else ''}")
    print(f"   hash publico : {commit}")
    if estado_ots == "OK":
        print(f"   OTS          : prueba de hora PERMANENTE creada (anclas_ots/{pid}.sha256.ots)")
    else:
        print(f"   OTS          : AVISO no se pudo anclar la hora ({detalle})")
    print(f"   SIGUIENTE: git add -A && git commit && git push AHORA, ANTES del saque.")

if __name__ == "__main__":
    main()

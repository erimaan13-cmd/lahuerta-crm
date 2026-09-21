"""Evaluación del clasificador sobre corpus etiquetados (data/eval/*.json).

Uso:
  python -m scripts.eval_corpus dev                 # conjunto de ajuste
  python -m scripts.eval_corpus holdout independiente --sweep
Métricas: exactitud top-1, precisión/recall por categoría, cobertura automática (% que NO va a revisión),
exactitud entre los auto-clasificados y barrido de umbral.
"""
import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from app import config
from app.classifier import engine
from app.classifier.extract import CatalogItem
from app.seed import PRODUCTS

EVAL = Path(__file__).resolve().parent.parent / "data" / "eval"
FILES = {"dev": "dev.json", "holdout": "test_holdout.json", "independiente": "test_independiente.json"}
CATALOG = [CatalogItem(sku, sku, name, kw.split(",")) for sku, name, _, kw in PRODUCTS]


def check_frozen():
    expected = dict(line.split()[::-1] for line in (EVAL / "HOLDOUT.sha256").read_text().splitlines())
    for name, h in expected.items():
        if hashlib.sha256((EVAL / name).read_bytes()).hexdigest() != h:
            raise SystemExit(f"¡{name} fue modificado después de congelarse!")


def run(items):
    out = []
    for it in items:
        r = engine.classify(engine.ClassifierInput(it["subject"], it["body"], it["from_email"], None,
                                                   it["sender_kind"], CATALOG))
        out.append((it, r))
    return out


def report(name, results, verbose=False):
    n = len(results)
    ok = sum(r.classification == it["label"] for it, r in results)
    auto = [(it, r) for it, r in results if not r.needs_review]
    auto_ok = sum(r.classification == it["label"] for it, r in auto)
    print(f"\n=== {name} · {n} correos · versión {engine.CLASSIFIER_VERSION} ===")
    print(f"Exactitud top-1: {ok}/{n} = {ok/n:.1%}")
    print(f"Cobertura automática: {len(auto)}/{n} = {len(auto)/n:.1%} · exactitud entre auto: "
          f"{auto_ok}/{len(auto)} = {(auto_ok/len(auto) if auto else 0):.1%}")
    print(f"Errores que habrían pasado SIN revisión: {len(auto)-auto_ok}")
    tp, fp, fn = Counter(), Counter(), Counter()
    for it, r in results:
        if r.classification == it["label"]:
            tp[it["label"]] += 1
        else:
            fp[r.classification] += 1
            fn[it["label"]] += 1
    print(f"{'categoría':24} {'prec':>6} {'recall':>6}")
    for cat in sorted(set(tp) | set(fp) | set(fn)):
        p = tp[cat] / (tp[cat] + fp[cat]) if tp[cat] + fp[cat] else 0
        rc = tp[cat] / (tp[cat] + fn[cat]) if tp[cat] + fn[cat] else 0
        print(f"{cat:24} {p:6.0%} {rc:6.0%}")
    conf = defaultdict(Counter)
    for it, r in results:
        if r.classification != it["label"]:
            conf[it["label"]][r.classification] += 1
    if conf:
        print("Confusiones (real → predicho):", "; ".join(
            f"{k}→{dict(v)}" for k, v in sorted(conf.items())))
    if verbose:
        for it, r in results:
            if r.classification != it["label"]:
                flag = "AUTO!" if not r.needs_review else "rev "
                print(f"  {flag} {it['id']} gold={it['label']} pred={r.classification} conf={r.confidence:.2f} "
                      f"scores={r.scores} | {it['subject'][:40]} | {it['body'][:110]!r}")
    return {"n": n, "acc": ok / n, "coverage": len(auto) / n, "auto_acc": auto_ok / len(auto) if auto else 0,
            "auto_errors": len(auto) - auto_ok}


def sweep(results):
    print("umbral  cobertura  exactitud-auto  errores-sin-revisión")
    orig = config.CLASSIFIER_THRESHOLD
    for th in [0.4, 0.5, 0.55, 0.6, 0.65, 0.7, 0.8]:
        auto = [(it, r) for it, r in results
                if r.confidence >= th and r.margin >= config.CLASSIFIER_MIN_MARGIN
                and r.classification not in config.CLASSIFIER_ALWAYS_REVIEW]
        ok = sum(r.classification == it["label"] for it, r in auto)
        print(f"{th:5.2f}  {len(auto)/len(results):9.0%}  {(ok/len(auto) if auto else 0):14.0%}  {len(auto)-ok:5d}")
    config.CLASSIFIER_THRESHOLD = orig


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("sets", nargs="+", choices=list(FILES))
    ap.add_argument("-v", "--verbose", action="store_true")
    ap.add_argument("--sweep", action="store_true")
    a = ap.parse_args()
    check_frozen()
    for s in a.sets:
        res = run(json.loads((EVAL / FILES[s]).read_text(encoding="utf-8")))
        report(s, res, a.verbose)
        if a.sweep:
            sweep(res)

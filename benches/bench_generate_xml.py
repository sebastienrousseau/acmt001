#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""What an acmt message costs to build, and which ones batch.

`generate_xml_string` runs three steps: a preparer flattens the input
rows into a template context, Jinja renders the template, and the result
is validated against the XSD. Two things about that are worth measuring,
and one of them is a trap.

* **The XSD is compiled once, not per message.** The first message pays
  for schema compilation; every message after it in the same process is
  an order of magnitude cheaper. A service that generates one message
  per process pays the compilation every time and looks slow for reasons
  that have nothing to do with the message.

* **Only some message types batch.** `_build_context` puts the first row
  at the top level and also exposes every row as ``records``. Whether
  those extra rows reach the output is the *template's* decision: seven
  of the thirty-four iterate ``records``, and twenty-seven describe a
  single account and ignore the rest.

That second point is why this benchmark reports output size next to the
timings. Handing five hundred accounts to a single-account message type
gets faster per record the more rows you add, which reads like a batching
win and is the opposite: the extra rows are dropped, the output stays the
same size, and the cost per record falls only because it is being divided
by rows that were never rendered. The size column is what gives it away
-- flat bytes means flat output, however good the per-record number
looks.

Run::

    python benches/bench_generate_xml.py
    python benches/bench_generate_xml.py --json
    python benches/bench_generate_xml.py --quick     # what CI runs

Nothing here asserts a threshold: wall-clock is not comparable between
machines, and a flaky performance gate teaches people to ignore red. CI
runs ``--quick`` so a benchmark that has stopped compiling against the
current API fails the build instead of rotting into a file that reads as
verified and is not.
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from acmt001 import generate_xml_string

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "acmt001" / "templates"

#: A message type whose template iterates ``records``, so rows accumulate.
BATCHING = "acmt.013.001.04"

#: A message type describing one account, which ignores rows after the
#: first. Included precisely because its per-record cost looks excellent.
SINGLE = "acmt.007.001.05"


def paths(message_type: str) -> tuple[str, str]:
    """The template and XSD paths bundled for ``message_type``."""
    base = TEMPLATES / message_type
    return str(base / "template.xml"), str(base / f"{message_type}.xsd")


def build(rows: int) -> list[dict]:
    """``rows`` account-management records with distinct identifiers."""
    source = json.loads(
        (ROOT / "examples" / "accounts.json").read_text(encoding="utf-8")
    )[0]
    return [
        dict(
            source,
            msg_id=f"MSG-{i:07d}",
            account_id=f"GB29NWBK6016{i:07d}",
        )
        for i in range(rows)
    ]


def _best(call, repeats: int) -> float:
    """Best-of timing after one untimed warm-up.

    The minimum is the least noisy estimator available; the mean follows
    whatever else the machine is doing.
    """
    call()
    samples = []
    for _ in range(repeats):
        start = time.perf_counter()
        call()
        samples.append(time.perf_counter() - start)
    return min(samples)


def measure(message_type: str, sizes: list[int], repeats: int) -> dict:
    """Cost and output size for ``message_type`` across ``sizes``."""
    template, xsd = paths(message_type)
    rendered: list[dict] = []
    for count in sizes:
        data = build(count)
        size = len(generate_xml_string(data, message_type, template, xsd))
        seconds = _best(
            lambda d=data: generate_xml_string(d, message_type, template, xsd),
            repeats,
        )
        rendered.append(
            {
                "rows": count,
                "ms": seconds * 1e3,
                "us_per_row": seconds * 1e6 / count,
                "bytes": size,
            }
        )
    first, last = rendered[0], rendered[-1]
    # Measured over the largest pair rather than the whole range: the
    # small sizes are dominated by fixed per-message overhead, which
    # drags the exponent toward zero and hides the marginal behaviour.
    marginal = None
    if len(rendered) >= 2:
        prev = rendered[-2]
        if prev["ms"] > 0 and prev["rows"] != last["rows"]:
            marginal = math.log(last["ms"] / prev["ms"]) / math.log(
                last["rows"] / prev["rows"]
            )
    return {
        "message_type": message_type,
        "sizes": rendered,
        "marginal_exponent": marginal,
        "output_grows": last["bytes"] > first["bytes"],
    }


def cold_start() -> dict:
    """First message versus later ones, measured in a fresh interpreter.

    Run as a subprocess because the schema cache is process-wide: once
    this process has generated anything, there is no cold path left to
    measure.
    """
    script = (
        "import json,time,sys;"
        "from pathlib import Path;"
        f"sys.path.insert(0, {str(ROOT)!r});"
        "from acmt001 import generate_xml_string;"
        f"mt={SINGLE!r};"
        f"base=Path({str(TEMPLATES)!r})/mt;"
        "tpl=str(base/'template.xml');xsd=str(base/(mt+'.xsd'));"
        f"row=json.loads(Path({str(ROOT / 'examples' / 'accounts.json')!r})"
        ".read_text())[0];"
        "t=time.perf_counter();generate_xml_string([row],mt,tpl,xsd);"
        "cold=time.perf_counter()-t;"
        "s=[];\n"
        "for _ in range(5):\n"
        "    t=time.perf_counter();generate_xml_string([row],mt,tpl,xsd);"
        "s.append(time.perf_counter()-t)\n"
        "print(cold, min(s))"
    )
    out = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    cold, warm = float(out[0]), float(out[1])
    return {
        "cold_ms": cold * 1e3,
        "warm_ms": warm * 1e3,
        "ratio": cold / warm if warm else 0.0,
    }


def run(quick: bool) -> dict:
    sizes = [1, 10, 100] if quick else [1, 10, 100, 500]
    repeats = 2 if quick else 5
    return {
        "cold_start": cold_start(),
        "batching": measure(BATCHING, sizes, repeats),
        "single": measure(SINGLE, sizes, repeats),
    }


def _render_one(result: dict) -> None:
    """Print one message type's table and its verdict."""
    print(f"\n  {result['message_type']}")
    print(f"    {'rows':>6}{'ms':>10}{'us/row':>12}{'output bytes':>15}")
    for row in result["sizes"]:
        print(
            f"    {row['rows']:>6}{row['ms']:>10.2f}"
            f"{row['us_per_row']:>12.1f}{row['bytes']:>15,}"
        )
    if result["output_grows"]:
        exponent = result["marginal_exponent"]
        if exponent is None:
            shape = "not enough sizes to say"
        elif exponent < 0.8:
            # Below 1.0 does not mean sublinear work; it means the fixed
            # per-message cost (schema lookup, envelope, validation) is
            # still being spread over too few rows to have amortised.
            shape = "fixed per-message cost still dominating at these sizes"
        elif exponent <= 1.3:
            shape = "linear, as it should be"
        else:
            shape = "worse than linear -- check for re-walking per row"
        print(
            f"    Output grows with the input: rows are being rendered. "
            f"Marginal exponent {exponent:.2f}\n    ({shape})."
        )
    else:
        print(
            "    Output size is FLAT while us/row falls. Rows after the "
            "first are ignored -- this\n    message type describes one "
            "account. The falling per-row cost is division, not batching."
        )


def render(results: dict) -> None:
    cold = results["cold_start"]
    print(
        f"  First message in a fresh process: {cold['cold_ms']:.1f} ms\n"
        f"  Later messages, same process:     {cold['warm_ms']:.2f} ms\n"
        f"  The XSD is compiled once and reused -- {cold['ratio']:.0f}x. A "
        f"service that\n  generates one message per process pays that "
        f"compilation every time."
    )
    _render_one(results["batching"])
    _render_one(results["single"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument(
        "--quick", action="store_true", help="small sizes, as CI runs"
    )
    args = parser.parse_args()

    results = run(quick=args.quick)
    if args.json:
        json.dump(results, sys.stdout, indent=1)
        print()
    else:
        render(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

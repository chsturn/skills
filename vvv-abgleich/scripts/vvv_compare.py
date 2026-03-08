#!/usr/bin/env python3
"""
VVV-Abgleich: Vergleicht Vermögensverwaltungsverträge (PDFs) mit JSON-Testdaten.

Verwendung:
    python3 vvv_compare.py <verzeichnis> [--output <report.md>]

Das Verzeichnis sollte should_onboard_* Ordner enthalten.
"""

import json
import os
import re
import shutil
import sys
import subprocess
import glob
import argparse
from datetime import datetime
from typing import Optional


# ─── Strategie-Mapping ───
STRATEGIE_MAP = {
    "value20fund": ["Value 20"],
    "value40fund": ["Value 40"],
    "value60fund": ["Value 60"],
    "value80fund": ["Value 80"],
    "value100fund": ["Value 100"],
    "value100millercrypto": ["Miller Krypto", "CRYPTOSTRATEGIE"],
    "value100secure": ["Sicherungsstrategie", "SECURE"],
    "valueGreen": ["Value Green"],
}

# ─── Bank-Mapping ───
BANK_MAP = {
    "baader": "Baader Bank",
    "llb": "Liechtensteinische Landesbank",
}

# ─── Länder-Mapping ───
LAND_MAP = {
    "DE": "Deutschland",
    "AT": "Österreich",
    "CH": "Schweiz",
    "LI": "Liechtenstein",
    "IT": "Italien",
    "FR": "Frankreich",
}


class VVVComparer:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.results = {}

    def find_test_dirs(self) -> list[str]:
        """Findet alle should_onboard_* Verzeichnisse."""
        pattern = os.path.join(self.base_dir, "should_onboard_*")
        dirs = sorted(glob.glob(pattern))
        return [d for d in dirs if os.path.isdir(d)]

    @staticmethod
    def check_pdftotext() -> bool:
        """Prüft ob pdftotext installiert ist."""
        return shutil.which("pdftotext") is not None

    def extract_pdf_text(self, pdf_path: str) -> str:
        """Extrahiert Text aus PDF mit pdftotext -layout."""
        if not self.check_pdftotext():
            return "FEHLER bei PDF-Extraktion: pdftotext nicht installiert. Installiere mit: brew install poppler (macOS) oder apt install poppler-utils (Linux)"
        tmp_path = f"/tmp/vvv_extract_{os.getpid()}.txt"
        try:
            subprocess.run(
                ["pdftotext", "-layout", pdf_path, tmp_path],
                check=True,
                capture_output=True,
            )
            with open(tmp_path, "r") as f:
                return f.read()
        except subprocess.CalledProcessError as e:
            return f"FEHLER bei PDF-Extraktion: {e.stderr.decode()}"
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def load_json(self, path: str) -> Optional[dict | list]:
        """Lädt eine JSON-Datei, gibt None zurück wenn nicht vorhanden."""
        if not os.path.exists(path):
            return None
        with open(path) as f:
            return json.load(f)

    def check_value(self, label: str, value: str, pdf_text: str) -> dict:
        """Prüft ob ein Wert im PDF-Text vorkommt."""
        if not value or not str(value).strip():
            return {"label": label, "value": value, "status": "skip", "reason": "Leerer Wert"}

        value_str = str(value).strip()
        found = value_str in pdf_text

        # Fallback: Case-insensitive Suche
        if not found:
            found = value_str.lower() in pdf_text.lower()

        return {
            "label": label,
            "value": value_str,
            "status": "ok" if found else "fail",
        }

    def compare_single(self, test_dir: str) -> dict:
        """Führt den Abgleich für einen einzelnen Testordner durch."""
        dirname = os.path.basename(test_dir)
        # Extrahiere Testname aus Verzeichnisname
        parts = dirname.replace("should_onboard_successfully_with_", "")
        # Entferne Timestamp (generisch: _YYYY-MM-DD... am Ende)
        test_label = re.sub(r'_\d{4}-\d{2}-\d{2}.*$', '', parts)
        # Extrahiere Testdatum aus Ordnername (für Datum-Check im PDF)
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', dirname)
        test_date = date_match.group(1) if date_match else None

        result = {
            "dir": dirname,
            "label": test_label,
            "checks": [],
            "errors": [],
        }

        # ─── Dateien laden ───
        qdata = self.load_json(os.path.join(test_dir, "questionnaire-data.json"))
        broker = self.load_json(os.path.join(test_dir, "broker-data.json"))
        partners = self.load_json(os.path.join(test_dir, "partner-data.json"))

        if not qdata:
            result["errors"].append("questionnaire-data.json nicht gefunden!")
            return result

        # Frage-Lookup
        q = {}
        for question in qdata.get("questions", []):
            q[question["name"]] = question.get("answer", {})

        # ─── PDF finden und extrahieren ───
        pdf_path = os.path.join(test_dir, "estably", "Vermögensverwaltungsvertrag Estably.pdf")
        if not os.path.exists(pdf_path):
            result["errors"].append("Vermögensverwaltungsvertrag PDF nicht gefunden!")
            return result

        pdf_text = self.extract_pdf_text(pdf_path)
        if pdf_text.startswith("FEHLER"):
            result["errors"].append(pdf_text)
            return result

        # ═══════════════════════════════════════
        # ABGLEICH: questionnaire-data.json
        # ═══════════════════════════════════════

        # --- Persönliche Daten ---
        angabe = q.get("angabe", {})
        addr = q.get("personlichen-daten", {})

        result["checks"].append({"section": "Persönliche Daten"})

        result["checks"].append(self.check_value("Nachname", angabe.get("nachname"), pdf_text))
        result["checks"].append(self.check_value("Vorname", angabe.get("vorname"), pdf_text))

        # Geburtsdatum: ISO → DD.MM.YYYY
        geb_raw = angabe.get("geburtsdatum", "")
        if geb_raw:
            try:
                dt = datetime.fromisoformat(geb_raw.replace("Z", "+00:00"))
                geb_fmt = dt.strftime("%d.%m.%Y")
                result["checks"].append(self.check_value("Geburtsdatum", geb_fmt, pdf_text))
            except ValueError:
                result["checks"].append({"label": "Geburtsdatum", "value": geb_raw, "status": "fail", "reason": "Parse-Fehler"})

        result["checks"].append(self.check_value("Familienstand", angabe.get("familienstand"), pdf_text))

        # Adresse: Straße + Hausnummer
        strasse = addr.get("strasse", "")
        hausnr = addr.get("hausnummer", "")
        if strasse:
            full_addr = f"{strasse} {hausnr}".strip() if hausnr else strasse
            result["checks"].append(self.check_value("Adresse", full_addr, pdf_text))

        plz = addr.get("plz", "")
        wohnort = addr.get("wohnort", "")
        if plz and wohnort:
            result["checks"].append(self.check_value("PLZ/Ort", f"{plz} {wohnort}", pdf_text))

        # E-Mail
        result["checks"].append(self.check_value("E-Mail", qdata.get("email"), pdf_text))

        # Telefon
        mobile = addr.get("mobile", "")
        if mobile:
            result["checks"].append(self.check_value("Telefon", mobile, pdf_text))

        # Land (Kürzel → Klartext)
        land = addr.get("land", "")
        if land:
            land_text = LAND_MAP.get(land, land)
            result["checks"].append(self.check_value("Land", land_text, pdf_text))

        # --- Berufliche Daten ---
        result["checks"].append({"section": "Berufliche Daten"})
        ap = q.get("angabe-person", {})
        employments = ap.get("employments", [{}])
        if employments:
            job = employments[0].get("job", "")
            result["checks"].append(self.check_value("Beruf", job, pdf_text))
        education = ap.get("educationDescriptionOther", "")
        if education:
            result["checks"].append(self.check_value("Ausbildung", education, pdf_text))

        # --- Strategie & Bank ---
        result["checks"].append({"section": "Strategie & Bank"})

        strat_key = q.get("strategie-auswahl", {}).get("strategie", "")
        strat_variants = STRATEGIE_MAP.get(strat_key, [strat_key])
        strat_found = any(v.lower() in pdf_text.lower() for v in strat_variants)
        result["checks"].append({
            "label": "Strategie",
            "value": f"{strat_key} → {strat_variants}",
            "status": "ok" if strat_found else "fail",
        })

        bank_key = q.get("bank-wahl", {}).get("bank", "")
        bank_name = BANK_MAP.get(bank_key, bank_key)
        result["checks"].append(self.check_value("Bank", bank_name, pdf_text))

        # --- Risikoprofil & Anlageziele ---
        result["checks"].append({"section": "Risikoprofil & Anlageziele"})

        # Anlageziel
        ziel = q.get("geldanlage-ziel", {})
        if ziel.get("aufbau"):
            result["checks"].append(self.check_value("Vermögensaufbau", "Vermögensaufbau", pdf_text))
        if ziel.get("preserveAssets"):
            result["checks"].append(self.check_value("Vermögenserhalt", "Vermögenserhalt", pdf_text))

        # Nachhaltigkeit
        sust = q.get("sustainable", {})
        if sust.get("interested") == "no":
            result["checks"].append(self.check_value("Nachhaltigkeit neutral", "keine Nachhaltigkeitspräferenz", pdf_text))

        # Risikoprofil Score-Range
        wm = q.get("wertminerung", {}).get("wertminerung", "")
        risk_map = {
            "0%": "0-3",
            "10%": "4-7",
            "20%": "8-11",
            "30%": "12-15",
            "40%": "16-19",
            "50%": "20-24",
        }
        risk_range = risk_map.get(wm, "")
        if risk_range:
            result["checks"].append(self.check_value(f"Risikoprofil ({wm})", risk_range, pdf_text))

        # --- Wirtschaftlich berechtigte Person ---
        result["checks"].append({"section": "Wirtschaftlich berechtigte Person"})
        result["checks"].append(self.check_value(
            "Selbst wirtschaftlich berechtigt",
            "selbst letztlich wirtschaftlich berechtigte Person",
            pdf_text,
        ))

        # --- Steuerliche Status ---
        result["checks"].append({"section": "Steuerliche Status"})
        # Datum aus dem Ordnernamen verwenden (= Testlauf-Datum), nicht das heutige Datum
        if test_date:
            try:
                dt_test = datetime.strptime(test_date, "%Y-%m-%d")
                test_date_fmt = dt_test.strftime("%d.%m.%Y")
                result["checks"].append(self.check_value("Vertragsdatum", test_date_fmt, pdf_text))
            except ValueError:
                result["checks"].append({"label": "Vertragsdatum", "value": test_date, "status": "skip", "reason": "Datum nicht parsbar"})
        if wohnort:
            result["checks"].append(self.check_value("Unterschriftsort", wohnort, pdf_text))

        # ═══════════════════════════════════════
        # ABGLEICH: broker-data.json
        # ═══════════════════════════════════════
        if broker and broker.get("generateBrokerAttachment"):
            result["checks"].append({"section": "Broker/Tippgeber (broker-data.json)"})
            for field, key in [
                ("Broker Firma", "companyName"),
                ("Broker Straße", "street"),
                ("Broker PLZ", "postalCode"),
                ("Broker Stadt", "city"),
            ]:
                result["checks"].append(self.check_value(field, broker.get(key), pdf_text))
            # Land: Kürzel → Klartext (gleiche Logik wie beim Kunden)
            broker_land = broker.get("country", "")
            if broker_land:
                broker_land_text = LAND_MAP.get(broker_land, broker_land)
                result["checks"].append(self.check_value("Broker Land", broker_land_text, pdf_text))

        # ═══════════════════════════════════════
        # ABGLEICH: partner-data.json
        # ═══════════════════════════════════════
        if partners:
            # Finde den relevanten Partner basierend auf der Strategie
            strat_group_name = ""
            if "millercrypto" in strat_key:
                strat_group_name = "millercrypto"
            elif "secure" in strat_key:
                strat_group_name = "secure"

            for partner in partners:
                groups = [g.get("groupName", "") for g in partner.get("strategyGroups", [])]
                if strat_group_name and strat_group_name in groups:
                    result["checks"].append({"section": f"Partner: {partner.get('companyName', '?')} (partner-data.json)"})
                    for field, key in [
                        ("Partner Firma", "companyName"),
                        ("Partner Straße", "street"),
                        ("Partner PLZ", "postalCode"),
                        ("Partner Stadt", "city"),
                    ]:
                        val = partner.get(key)
                        if val:  # Manche Partner haben leere Adressfelder
                            result["checks"].append(self.check_value(field, val, pdf_text))
                    # Land: Kürzel → Klartext
                    partner_land = partner.get("country", "")
                    if partner_land:
                        partner_land_text = LAND_MAP.get(partner_land, partner_land)
                        result["checks"].append(self.check_value("Partner Land", partner_land_text, pdf_text))

        return result

    def run_batch(self) -> list[dict]:
        """Führt den Abgleich für alle Testordner durch."""
        test_dirs = self.find_test_dirs()
        if not test_dirs:
            print(f"Keine should_onboard_* Verzeichnisse in {self.base_dir} gefunden!")
            return []

        results = []
        for d in test_dirs:
            result = self.compare_single(d)
            results.append(result)
        return results

    def generate_report(self, results: list[dict], fmt: str = "md") -> str:
        """Erzeugt einen Report im gewünschten Format."""
        if fmt == "html":
            return self._generate_html_report(results)
        return self._generate_md_report(results)

    def _count_checks(self, results: list[dict]) -> tuple[int, int, int, list[tuple[str, int, int, int]]]:
        """Zählt OK/Fail/Skip für alle Results. Gibt (total_ok, total_fail, total_skip, per_test) zurück."""
        total_ok = total_fail = total_skip = 0
        per_test = []
        for result in results:
            ok = fail = skip = 0
            for check in result["checks"]:
                if "section" in check:
                    continue
                s = check.get("status", "")
                if s == "ok":
                    ok += 1
                elif s == "fail":
                    fail += 1
                else:
                    skip += 1
            total_ok += ok
            total_fail += fail
            total_skip += skip
            per_test.append((result["label"], ok, fail, skip))
        return total_ok, total_fail, total_skip, per_test

    def _generate_html_report(self, results: list[dict]) -> str:
        """Erzeugt einen HTML-Report."""
        from html import escape
        total_ok, total_fail, total_skip, per_test = self._count_checks(results)
        total_checked = total_ok + total_fail
        rate = (total_ok / total_checked * 100) if total_checked > 0 else 0
        now = datetime.now().strftime("%d.%m.%Y %H:%M")

        h = []
        h.append("""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VVV-Abgleich Report</title>
<style>
  :root {
    --bg: #f8f9fa; --card: #fff; --border: #dee2e6;
    --ok: #198754; --ok-bg: #d1e7dd; --fail: #dc3545; --fail-bg: #f8d7da;
    --skip: #6c757d; --skip-bg: #e9ecef; --text: #212529; --muted: #6c757d;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
         background: var(--bg); color: var(--text); line-height: 1.5; padding: 2rem; }
  .container { max-width: 960px; margin: 0 auto; }
  h1 { font-size: 1.75rem; margin-bottom: .25rem; }
  .meta { color: var(--muted); font-size: .875rem; margin-bottom: 1.5rem; }

  /* Summary cards */
  .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
             gap: .75rem; margin-bottom: 2rem; }
  .summary-card { background: var(--card); border: 1px solid var(--border);
                  border-radius: 8px; padding: 1rem; text-align: center; }
  .summary-card .num { font-size: 2rem; font-weight: 700; }
  .summary-card .lbl { font-size: .75rem; text-transform: uppercase; color: var(--muted); letter-spacing: .05em; }
  .summary-card.ok .num { color: var(--ok); }
  .summary-card.fail .num { color: var(--fail); }
  .summary-card.rate .num { color: var(--ok); }

  /* Test section */
  .test-section { background: var(--card); border: 1px solid var(--border);
                  border-radius: 8px; margin-bottom: 1.25rem; overflow: hidden; }
  .test-header { padding: 1rem 1.25rem; cursor: pointer; display: flex;
                 align-items: center; justify-content: space-between; user-select: none; }
  .test-header:hover { background: #f1f3f5; }
  .test-header h2 { font-size: 1.1rem; margin: 0; }
  .test-header .badge { font-size: .8rem; padding: .2em .6em; border-radius: 12px;
                        font-weight: 600; white-space: nowrap; }
  .badge-ok { background: var(--ok-bg); color: var(--ok); }
  .badge-fail { background: var(--fail-bg); color: var(--fail); }
  .test-body { padding: 0 1.25rem 1.25rem; }
  .test-dir { font-size: .75rem; color: var(--muted); font-family: monospace;
              word-break: break-all; margin-bottom: .75rem; }

  /* Section within a test */
  .section-title { font-size: .9rem; font-weight: 600; margin: 1rem 0 .4rem; color: var(--muted);
                   text-transform: uppercase; letter-spacing: .04em; }

  /* Table */
  table { width: 100%; border-collapse: collapse; font-size: .875rem; margin-bottom: .5rem; }
  th, td { text-align: left; padding: .45rem .6rem; border-bottom: 1px solid var(--border); }
  th { font-weight: 600; color: var(--muted); font-size: .75rem; text-transform: uppercase; letter-spacing: .04em; }
  td.val { font-family: 'SF Mono', Menlo, monospace; font-size: .8rem; word-break: break-all; }
  .st { font-weight: 600; text-align: center; width: 3.5rem; }
  .st-ok { color: var(--ok); }
  .st-fail { color: var(--fail); }
  .st-skip { color: var(--skip); }

  .test-result { font-size: .875rem; font-weight: 600; padding-top: .5rem; }

  .error { background: var(--fail-bg); color: var(--fail); padding: .75rem 1rem;
           border-radius: 6px; margin: .5rem 0; }

  details > summary { list-style: none; }
  details > summary::-webkit-details-marker { display: none; }
  details[open] .arrow { transform: rotate(90deg); }
  .arrow { display: inline-block; transition: transform .15s; margin-right: .5rem; font-size: .8rem; }
</style>
</head>
<body>
<div class="container">
<h1>VVV-Abgleich Report</h1>
<p class="meta">""")
        h.append(f'{now} &middot; {len(results)} Tests &middot; <code>{escape(self.base_dir)}</code></p>')

        # Summary cards
        h.append('<div class="summary">')
        h.append(f'<div class="summary-card ok"><div class="num">{total_ok}</div><div class="lbl">Bestätigt</div></div>')
        h.append(f'<div class="summary-card fail"><div class="num">{total_fail}</div><div class="lbl">Fehler</div></div>')
        h.append(f'<div class="summary-card"><div class="num">{total_skip}</div><div class="lbl">Übersprungen</div></div>')
        h.append(f'<div class="summary-card rate"><div class="num">{rate:.0f}%</div><div class="lbl">Erfolgsrate</div></div>')
        h.append('</div>')

        # Per-test sections
        for idx, result in enumerate(results):
            _, ok, fail, skip = per_test[idx]
            has_fail = fail > 0
            badge_cls = "badge-fail" if has_fail else "badge-ok"
            badge_text = f"{fail} Fehler" if has_fail else f"{ok} OK"
            is_open = "open" if has_fail else ""

            h.append(f'<details class="test-section" {is_open}>')
            h.append(f'<summary class="test-header"><h2><span class="arrow">&#9654;</span>{escape(result["label"])}</h2>')
            h.append(f'<span class="badge {badge_cls}">{badge_text}</span></summary>')
            h.append('<div class="test-body">')
            h.append(f'<div class="test-dir">{escape(result["dir"])}</div>')

            if result["errors"]:
                for err in result["errors"]:
                    h.append(f'<div class="error">{escape(err)}</div>')
                h.append('</div></details>')
                continue

            in_table = False
            for check in result["checks"]:
                if "section" in check:
                    if in_table:
                        h.append('</tbody></table>')
                        in_table = False
                    h.append(f'<div class="section-title">{escape(check["section"])}</div>')
                    h.append('<table><thead><tr><th>Feld</th><th>Wert</th><th class="st">Status</th></tr></thead><tbody>')
                    in_table = True
                    continue

                status = check.get("status", "")
                label = check.get("label", "")
                value = check.get("value", "")
                if status == "ok":
                    icon, cls = "&#10003;", "st-ok"
                elif status == "fail":
                    icon, cls = "&#10007;", "st-fail"
                else:
                    icon, cls = "&#8211;", "st-skip"

                h.append(f'<tr><td>{escape(label)}</td><td class="val">{escape(str(value))}</td>')
                h.append(f'<td class="st {cls}">{icon}</td></tr>')

            if in_table:
                h.append('</tbody></table>')

            h.append(f'<div class="test-result">&#10003; {ok} OK &nbsp; &#10007; {fail} Fehler &nbsp; &#8211; {skip} Übersprungen</div>')
            h.append('</div></details>')

        h.append('</div></body></html>')
        return "\n".join(h)

    def _generate_md_report(self, results: list[dict]) -> str:
        """Erzeugt einen Markdown-Report."""
        lines = []
        lines.append("# VVV-Abgleich Report")
        lines.append(f"\n**Datum**: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        lines.append(f"**Verzeichnis**: `{self.base_dir}`")
        lines.append(f"**Anzahl Tests**: {len(results)}")

        total_ok = 0
        total_fail = 0
        total_skip = 0

        for result in results:
            lines.append(f"\n---\n")
            lines.append(f"## {result['label']}")
            lines.append(f"\n`{result['dir']}`\n")

            if result["errors"]:
                for err in result["errors"]:
                    lines.append(f"**FEHLER**: {err}")
                continue

            ok = 0
            fail = 0
            skip = 0

            for check in result["checks"]:
                if "section" in check:
                    lines.append(f"\n### {check['section']}\n")
                    lines.append("| Feld | Wert | Status |")
                    lines.append("|------|------|--------|")
                    continue

                status = check.get("status", "")
                label = check.get("label", "")
                value = check.get("value", "")

                if status == "ok":
                    icon = "✅"
                    ok += 1
                elif status == "fail":
                    icon = "❌"
                    fail += 1
                else:
                    icon = "⏭️"
                    skip += 1

                # Escape pipe characters in value
                value_escaped = str(value).replace("|", "\\|")
                lines.append(f"| {label} | `{value_escaped}` | {icon} |")

            total_ok += ok
            total_fail += fail
            total_skip += skip

            lines.append(f"\n**Ergebnis**: ✅ {ok} OK | ❌ {fail} Fehler | ⏭️ {skip} Übersprungen")

        # Zusammenfassung
        lines.append(f"\n---\n")
        lines.append("## Gesamtergebnis\n")
        lines.append(f"| Metrik | Wert |")
        lines.append(f"|--------|------|")
        lines.append(f"| Tests | {len(results)} |")
        lines.append(f"| ✅ Bestätigt | {total_ok} |")
        lines.append(f"| ❌ Fehler | {total_fail} |")
        lines.append(f"| ⏭️ Übersprungen | {total_skip} |")

        total_checked = total_ok + total_fail
        if total_checked > 0:
            rate = (total_ok / total_checked) * 100
            lines.append(f"| Erfolgsrate | {rate:.1f}% |")

        return "\n".join(lines)


DEFAULT_DOWNLOADS_DIR = os.path.join("web", "apps", "fe-web-e2e", "cypress", "downloads")


def main():
    parser = argparse.ArgumentParser(description="VVV-Abgleich: Vergleicht VVV-PDFs mit JSON-Testdaten")
    parser.add_argument("directory", nargs="?", default=None,
                        help="Verzeichnis mit should_onboard_* Ordnern (Standard: web/apps/fe-web-e2e/cypress/downloads)")
    parser.add_argument("--output", "-o", help="Pfad für den Report (Standard: <directory>/vvv-abgleich-report.<format>)")
    parser.add_argument("--format", "-f", choices=["md", "html"], default="html",
                        help="Report-Format: html (Standard) oder md")
    args = parser.parse_args()

    # Default-Pfad: CWD/web/apps/fe-web-e2e/cypress/downloads
    directory = args.directory or os.path.join(os.getcwd(), DEFAULT_DOWNLOADS_DIR)

    if not os.path.isdir(directory):
        print(f"Fehler: {directory} ist kein Verzeichnis!")
        if not args.directory:
            print(f"Tipp: Standard-Pfad '{DEFAULT_DOWNLOADS_DIR}' nicht gefunden. Starte das Script aus dem Projekt-Root oder gib ein Verzeichnis an.")
        sys.exit(1)

    comparer = VVVComparer(directory)
    results = comparer.run_batch()

    if not results:
        sys.exit(1)

    report = comparer.generate_report(results, fmt=args.format)

    ext = args.format
    output_path = args.output or os.path.join(directory, f"vvv-abgleich-report.{ext}")
    with open(output_path, "w") as f:
        f.write(report)

    # Bei HTML nur Zusammenfassung auf stdout, bei MD den vollen Report
    if args.format == "html":
        total_ok, total_fail, total_skip, per_test = comparer._count_checks(results)
        total_checked = total_ok + total_fail
        rate = (total_ok / total_checked * 100) if total_checked > 0 else 0
        print(f"VVV-Abgleich: {len(results)} Tests | {total_ok} OK | {total_fail} Fehler | {rate:.0f}%")
        for label, ok, fail, skip in per_test:
            icon = "❌" if fail > 0 else "✅"
            print(f"  {icon} {label}: {ok} OK, {fail} Fehler")
    else:
        print(report)

    print(f"\n📄 Report gespeichert: {output_path}")


if __name__ == "__main__":
    main()

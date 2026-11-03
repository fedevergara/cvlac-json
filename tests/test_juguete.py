"""End-to-end tests on a toy CvLAC page (tests/fixtures/cvlac_juguete.html), through extract() and the command.

The Release workflow runs this file against the built wheel before publishing (with CVLAC_JSON_INSTALLED and
CVLAC_JSON_EXPECTED_VERSION set); CI runs it with the rest of the suite. No network: Scienti and ROR are off.

The toy owner, Juan Pablo Ejemplo Prueba (COD_RH 0000000002), worked at the Universidad del Valle in 2005-2010 and
at the Universidad de Antioquia from 2016, so each record's year decides the affiliation.
"""

import json
import os
import pathlib
import shutil
import subprocess
import sys

import pytest

import cvlac_json
from cvlac_json import extract, to_jsonld
from cvlac_json.parser import product_lists

COD = "0000000002"
TOY = pathlib.Path(__file__).parent / "fixtures" / "cvlac_juguete.html"
UDEA, VALLE = "UNIVERSIDAD DE ANTIOQUIA", "UNIVERSIDAD DEL VALLE"


@pytest.fixture
def toy():
    return extract(COD, html=TOY.read_text(encoding="latin-1"), scienti="off", ror=False, log=lambda m: None)


def owner(people):
    (o,) = [p for p in people if p.get("id") == COD]
    return o


def affs(person):
    return [a["name"] for a in person.get("affiliations") or []]


def run_cli(*args):
    """The command as installed (`cvlac-json` on PATH), else `python -m cvlac_json`."""
    exe = shutil.which("cvlac-json")
    cmd = [exe] if exe else [sys.executable, "-m", "cvlac_json"]
    return subprocess.run(
        [*cmd, "2", "--html", str(TOY), "--scienti", "off", "--ror", "off", "--no-progress", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )


def test_installed_package():
    expected = os.environ.get("CVLAC_JSON_EXPECTED_VERSION")
    if expected:
        assert cvlac_json.__version__ == expected
    if os.environ.get("CVLAC_JSON_INSTALLED"):  # the wheel, not the source tree
        src = pathlib.Path(__file__).resolve().parents[1] / "src"
        assert src not in pathlib.Path(cvlac_json.__file__).resolve().parents


def test_cli_writes_the_same_json_as_extract(tmp_path, toy):
    out = tmp_path / "toy.json"
    run_cli("-o", str(out))
    cli = json.loads(out.read_text(encoding="utf-8"))
    for d in (cli, toy):
        d.pop("retrieved")
    assert cli == json.loads(json.dumps(toy))


def test_cli_stdout_and_jsonld(tmp_path):
    data = json.loads(run_cli("-o", "-").stdout)
    assert data["cod_rh"] == COD and data["profile"]["Nombre"] == "Juan Pablo Ejemplo Prueba"
    out = tmp_path / "toy.jsonld"
    run_cli("--format", "jsonld", "-o", str(out))
    ld = json.loads(out.read_text(encoding="utf-8"))
    assert ld["@id"].endswith(f"cod_rh={COD}") and "@context" in ld
    assert ld["patents"][0]["@type"] == "Patent" and ld["events"][0]["@id"].endswith("#/events/0")


def test_cli_version():
    exe = shutil.which("cvlac-json")
    cmd = [exe] if exe else [sys.executable, "-m", "cvlac_json"]
    out = subprocess.run([*cmd, "--version"], capture_output=True, text=True, check=True)
    assert cvlac_json.__version__ in out.stdout + out.stderr


def test_owner_once_in_every_record(toy):
    recs = [*toy["works"], *toy["projects"], *(it for _, v in product_lists(toy) for it in v)]
    assert len(recs) == 7
    for r in recs:
        assert sum(a.get("id") == COD for a in r["authors"]) == 1, r.get("title")
    for ev in toy["events"]:
        assert sum(p["id"] == COD for p in ev["participants"]) == 1, ev["name"]
    hashes = [owner(r["authors"])["product_hash"] for r in recs]
    assert len(set(hashes)) == 7 and all(len(h) == 40 for h in hashes)
    assert owner(toy["works"][0]["authors"])["product_hash"] == cvlac_json.product_hash(
        "Un artículo de juguete con DOI", COD, "work", 2019
    )


def test_works(toy):
    full, short, absent = toy["works"]
    assert full["doi"] == "https://doi.org/10.9999/toy.2019.001" and full["year_published"] == 2019
    assert owner(full["authors"])["full_name"] == "JUAN PABLO EJEMPLO PRUEBA" and affs(owner(full["authors"])) == [UDEA]
    assert owner(short["authors"])["full_name"] == "JUAN PABLO EJEMPLO"  # shortened form of the owner's name
    assert affs(owner(short["authors"])) == [VALLE]  # 2008
    assert [a["full_name"] for a in absent["authors"]] == ["MARTA LUCIA OTRA PERSONA", "Juan Pablo Ejemplo Prueba"]
    assert affs(owner(absent["authors"])) == [UDEA]  # not listed: added at the end


def test_project_spans_both_jobs(toy):
    (p,) = toy["projects"]
    assert (p["start"]["year"], p["end"]["year"]) == (2009, 2017)
    assert sorted(affs(owner(p["authors"]))) == [UDEA, VALLE]


def test_events(toy):
    congress, seminar = toy["events"]
    o = owner(congress["participants"])
    assert (o["name"], o["role"], affs(o)) == ("JUAN PABLO EJEMPLO PRUEBA", "Ponente", [UDEA])
    other = next(p for p in congress["participants"] if p["id"] is None)
    assert other["external_ids"] == [] and other.get("affiliations", []) == []
    o = owner(seminar["participants"])  # the page lists only someone else: the owner is added
    assert (o["name"], o["role"], affs(o)) == ("Juan Pablo Ejemplo Prueba", None, [VALLE])


def test_patent_thesis_and_jury(toy):
    (pat,) = toy["patents"]
    assert {"source": "patent", "id": "NC2021/0000002"} in pat["identifiers"] and pat["holder"] == UDEA
    assert affs(owner(pat["authors"])) == [UDEA]
    (thesis,) = toy["other_products"]["Trabajos dirigidos/tutorías"]
    co = owner(thesis["authors"])  # co-advisor: the owner's experience in 2019, not the thesis institution
    assert co["type"] == "co-advisor" and affs(co) == [UDEA]
    (jury,) = toy["other_products"]["Jurado en comités de evaluación"]
    assert owner(jury["authors"])["type"] == "jury" and affs(owner(jury["authors"])) == []  # no year on the page


def test_counts(toy):
    c = toy["counts"]
    assert (c["works"], c["projects"], c["events"], c["patents"]) == (3, 1, 2, 1)
    assert (c["owner_by_name_variant"], c["owner_added"]) == (1, 2)
    assert (c["works_with_affiliation"], c["projects_with_affiliation"], c["events_with_affiliation"]) == (3, 1, 2)
    assert toy["affiliations_from_experience"]["theses_owner_from_experience"] == 1
    assert to_jsonld(toy)["@type"] == ["schema:ProfilePage", "CvlacProfile"]

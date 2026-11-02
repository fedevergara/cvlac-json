from cvlac_json import extract, ror
from cvlac_json.parser import build

UDEA = {
    "id": "https://ror.org/03bp5hc83",
    "names": [{"value": "Universidad de Antioquia", "types": ["ror_display", "label"]}, {"value": "UdeA", "types": ["acronym"]}],
    "types": ["education"],
    "external_ids": [{"type": "grid", "preferred": "grid.412881.6", "all": ["grid.412881.6"]}],
    "locations": [{"geonames_details": {"name": "Medellín", "country_name": "Colombia", "country_code": "CO"}}],
}
UNAL = {
    "id": "https://ror.org/059yx9a68",
    "names": [{"value": "Universidad Nacional de Colombia", "types": ["ror_display"]}],
    "types": ["education"],
    "external_ids": [],
    "locations": [{"geonames_details": {"name": "Bogotá", "country_name": "Colombia", "country_code": "CO"}}],
}
OTHER = {
    "id": "https://ror.org/000000000",
    "names": [{"value": "Universidad de Jaén", "types": ["ror_display"]}],
    "types": ["education"],
    "external_ids": [],
    "locations": [],
}


def test_period_years():
    assert ror.period_years("Noviembre de 1995 Marzo de 2001") == (1995, 2001)
    assert ror.period_years("Febrero de 1995 de", now=2030) == (1995, 2030)
    assert ror.period_years("Marzo de 2006 de Actual", now=2030) == (2006, 2030)
    assert ror.period_years("") == (None, None)


def test_accept_exact_name_not_rors_chosen_flag():
    items = [{"chosen": True, "score": 1.0, "organization": OTHER}, {"chosen": False, "score": 1.0, "organization": UDEA}]
    org, how = ror._accept("UNIVERSIDAD DE ANTIOQUIA", items)
    assert org is UDEA and how == "name"


def test_accept_prefix_needs_high_score():
    items = [{"chosen": True, "score": 1.0, "organization": UNAL}]
    org, how = ror._accept("UNIVERSIDAD NACIONAL DE COLOMBIA SEDE MEDELLÍN", items)
    assert org is UNAL and how == "prefix"
    low = [{"chosen": True, "score": 0.5, "organization": UNAL}]
    assert ror._accept("UNIVERSIDAD NACIONAL DE COLOMBIA SEDE MEDELLÍN", low) == (None, None)


def test_no_match_for_units():
    assert ror._accept("FACULTAD DE INGENIERIA", [{"chosen": True, "score": 0.8, "organization": OTHER}]) == (None, None)


def test_enrich_with_mocked_ror(page, monkeypatch):
    answers = {
        "universidad de antioquia": [{"chosen": False, "score": 1.0, "organization": UDEA}],
        "universidad nacional de colombia sede medellin": [{"chosen": True, "score": 1.0, "organization": UNAL}],
    }

    def fake_lookup(name, cache):
        k = ror.norm(name)
        if k not in cache:
            org, how = ror._accept(name, answers.get(k, []))
            cache[k] = (
                None
                if org is None
                else {
                    "id": org["id"].rsplit("/", 1)[-1],
                    "name": ror._display(org),
                    "match": how,
                    "types": [{"source": "ror", "type": t} for t in org["types"]],
                    "external_ids": [{"provenance": "ror", "source": "ror", "id": org["id"]}],
                    "addresses": [],
                }
            )
        return cache[k]

    monkeypatch.setattr(ror, "lookup", fake_lookup)
    data = extract("1", html=page, scienti="off", ror=True, log=lambda m: None)
    assert [e["ror"]["id"] for e in data["experience"]] == ["03bp5hc83", "059yx9a68"]
    aff = data["works"][0]["authors"][0]["affiliations"][0]
    assert aff["id"] == "03bp5hc83" and aff["name"] == "Universidad de Antioquia"
    thesis = data["other_products"]["Trabajos dirigidos/tutorías"][0]
    assert thesis["institution"]["id"] == "03bp5hc83"
    student = next(a for a in thesis["authors"] if a["type"] == "student")
    assert student["affiliations"][0]["id"] == "03bp5hc83"
    co = next(a for a in thesis["authors"] if a["type"] == "co-advisor")
    assert co["affiliations"] == []
    (owner,) = data["patents"][0]["authors"]  # patents and other products: as works, by the item's year
    assert owner["affiliations"] and owner["affiliations"][0]["cvlac"]["provenance"] == "cvlac experience"
    assert data["counts"]["products_with_affiliation"] >= 1
    (proj_owner,) = data["projects"][0]["authors"]  # 2019-2021: UdeA (2015-), not UNAL (2008-2012)
    assert [a["id"] for a in proj_owner["affiliations"]] == ["03bp5hc83"]
    assert data["counts"]["projects_with_affiliation"] == 1


def test_project_span():
    assert ror.project_span({"start": {"year": 2019}, "end": {"year": 2021}}) == (2019, 2021)
    assert ror.project_span({"start": {"year": 2019}, "end": None, "projected_end": {"year": 2022}}) == (2019, 2022)
    assert ror.project_span({"start": {"year": 2019}, "end": {"year": 2017}}) == (2019, 2019)
    assert ror.project_span({"start": None}) is None


def test_project_overlap_and_siiu_affiliation(page):
    data = build(page, "0000000001")
    data["experience"] = [e for e in data["experience"] if "NACIONAL" in e["institution"]]  # 2008-2012 only
    data["projects"][0]["start"] = {"year": 2012, "month": 1}  # 2012-2021 overlaps UNAL
    data["projects"][0]["siiu"] = {"id": "2012-1", "siiu_years": [2012, 2014]}
    ror.enrich(data, ror=False)
    (owner,) = data["projects"][0]["authors"]
    unal, udea = owner["affiliations"]
    assert unal["cvlac"]["provenance"] == "cvlac experience" and unal["years"] == list(range(2008, 2013))
    assert udea["id"] == "03bp5hc83" and udea["name"] == "Universidad de Antioquia"
    assert udea["cvlac"]["provenance"] == "siiu project" and udea["years"] == [2012, 2013, 2014]
    assert data["affiliations_from_experience"]["projects_with_siiu_affiliation"] == 1
    ror.siiu_affiliations(data["projects"][:1], "0000000001", {}, ror=False)  # UdeA already there: not repeated
    assert len(owner["affiliations"]) == 2

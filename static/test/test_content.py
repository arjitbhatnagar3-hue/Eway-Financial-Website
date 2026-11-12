"""Tests for public content endpoints and active page routes."""


# --------------------------------------------------------------------------- pages
def test_new_pages_render(anon):
    pages = [
        "/", "/about", "/about/company-profile", "/about/team",
        "/about/awards", "/services", "/services/taxation",
        "/faq", "/contact", "/search",
    ]
    for page in pages:
        r = anon.get(page)
        assert r.status_code == 200, f"{page} -> {r.status_code}"
        assert "<html" in r.text.lower()


# --------------------------------------------------------------------------- team
def test_team_endpoint(anon):
    team = anon.get("/api/team").json()
    assert len(team) == 2
    assert any(m["name"] == "Divya Bhatnagar" and m["is_director"] for m in team)
    one = anon.get(f"/api/team/{team[0]['id']}")
    assert one.status_code == 200
    assert anon.get("/api/team/does-not-exist").status_code == 404


# --------------------------------------------------------------------------- awards
def test_awards_endpoint(anon):
    awards = anon.get("/api/awards").json()
    assert len(awards) >= 3
    assert all("issuer" in a and "year" in a for a in awards)

# --------------------------------------------------------------------------- single service lookup
def test_single_service_endpoint(anon):
    r = anon.get("/api/services/taxation")
    assert r.status_code == 200
    assert r.json()["id"] == "taxation"
    assert anon.get("/api/services/does-not-exist").status_code == 404


# --------------------------------------------------------------------------- search
def test_search_endpoint(anon):
    r = anon.get("/api/search?q=gst")
    assert r.status_code == 200
    data = r.json()
    assert data["results"]
    assert any(item["type"] == "Service" for item in data["results"])

    empty = anon.get("/api/search?q=x")
    assert empty.json()["results"] == []

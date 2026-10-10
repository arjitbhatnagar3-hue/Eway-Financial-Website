"""Tests for the public content endpoints and page routes added for the
redesigned site (About Us sub-pages, Services, Resources, Workshops,
Articles, FAQ, Contact, Search)."""


# --------------------------------------------------------------------------- pages
def test_new_pages_render(anon):
    pages = [
        "/", "/about", "/about/company-profile", "/about/team",
        "/about/awards", "/about/media", "/services", "/services/taxation",
        "/resources", "/workshops", "/articles",
        "/articles/gst-checklist-small-business", "/faq", "/contact", "/search",
    ]
    for page in pages:
        r = anon.get(page)
        assert r.status_code == 200, f"{page} -> {r.status_code}"
        assert "<html" in r.text.lower()


# --------------------------------------------------------------------------- team
def test_team_endpoint(anon):
    team = anon.get("/api/team").json()
    assert len(team) >= 5
    assert any(m["name"] == "Divya Bhatnagar" and m["is_director"] for m in team)
    one = anon.get(f"/api/team/{team[0]['id']}")
    assert one.status_code == 200
    assert anon.get("/api/team/does-not-exist").status_code == 404


# --------------------------------------------------------------------------- awards & media
def test_awards_and_media_endpoints(anon):
    awards = anon.get("/api/awards").json()
    assert len(awards) >= 3
    assert all("issuer" in a and "year" in a for a in awards)

    media = anon.get("/api/media").json()
    assert len(media) >= 3
    assert all("outlet" in m for m in media)


# --------------------------------------------------------------------------- articles
def test_articles_list_and_detail(anon):
    articles = anon.get("/api/articles").json()
    assert len(articles) >= 4
    # newest first
    dates = [a["date"] for a in articles]
    assert dates == sorted(dates, reverse=True)

    slug = articles[0]["slug"]
    detail = anon.get(f"/api/articles/{slug}")
    assert detail.status_code == 200
    assert isinstance(detail.json()["body"], list) and detail.json()["body"]

    assert anon.get("/api/articles/no-such-article").status_code == 404


# --------------------------------------------------------------------------- workshops
def test_workshops_endpoint(anon):
    workshops = anon.get("/api/workshops").json()
    assert len(workshops) >= 3
    assert all(w["topics"] for w in workshops)
    one = anon.get(f"/api/workshops/{workshops[0]['id']}")
    assert one.status_code == 200
    assert anon.get("/api/workshops/nope").status_code == 404


# --------------------------------------------------------------------------- resources (PDFs)
def test_resources_endpoint_and_files_exist(anon):
    resources = anon.get("/api/resources").json()
    assert len(resources) >= 4
    for r in resources:
        file_resp = anon.get(f"/static/{r['file']}")
        assert file_resp.status_code == 200
        assert file_resp.headers["content-type"] == "application/pdf"


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

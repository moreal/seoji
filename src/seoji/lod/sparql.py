import httpx

SPARQL_ENDPOINT = "https://lod.nl.go.kr/sparql"


def sparql_construct(
    uris: list[str], *, endpoint: str = SPARQL_ENDPOINT, timeout: float = 70
) -> bytes:
    """Fetch every triple of the given resources as RDF/XML. Keep batches small (<=200)."""
    values = " ".join(f"<{u}>" for u in uris)
    query = f"CONSTRUCT {{ ?s ?p ?o }} WHERE {{ VALUES ?s {{ {values} }} ?s ?p ?o }}"
    resp = httpx.get(
        endpoint,
        params={"query": query},
        headers={"Accept": "application/rdf+xml"},
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.content


def sparql_count_books(*, endpoint: str = SPARQL_ENDPOINT, timeout: float = 70) -> int:
    query = "SELECT (COUNT(?s) AS ?n) WHERE { ?s a <http://purl.org/ontology/bibo/Book> }"
    resp = httpx.get(
        endpoint,
        params={"query": query},
        headers={"Accept": "application/sparql-results+json"},
        timeout=timeout,
    )
    resp.raise_for_status()
    return int(resp.json()["results"]["bindings"][0]["n"]["value"])

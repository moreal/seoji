#!/usr/bin/env bash
# Fetch the LOD test fixtures from the NLK SPARQL endpoint (no key needed).
set -euo pipefail
cd "$(dirname "$0")/.."
ENDPOINT=https://lod.nl.go.kr/sparql
OUT=tests/fixtures/lod

construct_uris() {
  local values=""
  for id in "$@"; do values+="<http://lod.nl.go.kr/resource/${id}> "; done
  echo "CONSTRUCT { ?s ?p ?o } WHERE { VALUES ?s { ${values}} ?s ?p ?o }"
}

curl -fsS -m 90 -G "$ENDPOINT" --data-urlencode "query=$(construct_uris \
  KJU201703899 KJU201108521 KJU201211257 KJU201208224 KJU200801614 \
  KJU200607571 KJU200803205 CMO202503241 CMO000000001)" -o "$OUT/sample_kr.rdf"

curl -fsS -m 90 -G "$ENDPOINT" --data-urlencode "query=PREFIX bibo: <http://purl.org/ontology/bibo/>
CONSTRUCT { ?s ?p ?o } WHERE { { SELECT DISTINCT ?s WHERE { ?s a bibo:Book ; bibo:isbn ?i } LIMIT 5 } ?s ?p ?o }" \
  -o "$OUT/sample_foreign.rdf"

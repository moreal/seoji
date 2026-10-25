# PostgreSQL 17 + pg_bigm for CloudNativePG (homelab runs seoji on CNPG; docker/postgres is the
# compose image for local development). Same pg_bigm build, CNPG operand image as the base.
ARG BASE=ghcr.io/cloudnative-pg/postgresql:17-standard-trixie

FROM ${BASE} AS build
ARG PG_BIGM_VERSION=1.2-20240606
USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl ca-certificates postgresql-server-dev-17 libicu-dev \
    && curl -fsSL "https://github.com/pgbigm/pg_bigm/archive/refs/tags/v${PG_BIGM_VERSION}.tar.gz" | tar xz -C /tmp \
    && make -C "/tmp/pg_bigm-${PG_BIGM_VERSION}" USE_PGXS=1 \
    && make -C "/tmp/pg_bigm-${PG_BIGM_VERSION}" USE_PGXS=1 install DESTDIR=/out

FROM ${BASE}
USER root
COPY --from=build /out/ /
# CNPG runs the operand as the image's postgres user (UID 26).
USER 26

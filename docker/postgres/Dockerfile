FROM postgres:17 AS build
ARG PG_BIGM_VERSION=1.2-20240606
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl ca-certificates postgresql-server-dev-17 libicu-dev \
    && curl -fsSL "https://github.com/pgbigm/pg_bigm/archive/refs/tags/v${PG_BIGM_VERSION}.tar.gz" | tar xz -C /tmp \
    && make -C "/tmp/pg_bigm-${PG_BIGM_VERSION}" USE_PGXS=1 \
    && make -C "/tmp/pg_bigm-${PG_BIGM_VERSION}" USE_PGXS=1 install DESTDIR=/out

FROM postgres:17
COPY --from=build /out/ /

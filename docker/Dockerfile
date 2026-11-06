# Fixed digests identify base images; registries need not retain them forever.
FROM mambaorg/micromamba:1.5.10-bookworm-slim@sha256:e3797091302382ea841498bc93a7b0a50f7c1448333d5e946d2d1608d0c5f43d AS dependencies

ARG PYTHON_VERSION=3.12.13
USER root
ENV DEBIAN_FRONTEND=noninteractive
ENV MAMBA_ROOT_PREFIX=/opt/conda
ENV CONDA_PREFIX=/opt/rdkit
ENV PATH=/opt/rdkit/bin:$PATH

# APT and Conda repodata are live sources. Their availability and transitive
# solutions can drift even with pinned bases and direct versions. Preserve the
# resolved dependency inventory; review failures in a new release, not by
# relaxing checksums or silently substituting unaudited source code.
RUN set -eux; \
    apt-get -o Acquire::Retries=3 update; \
    apt-get -o Acquire::Retries=3 install -y --no-install-recommends \
      build-essential cmake ninja-build pkg-config curl ca-certificates; \
    rm -rf /var/lib/apt/lists/*
RUN set -eux; \
    micromamba create -y -p /opt/rdkit; \
    for attempt in 1 2 3; do \
      if micromamba install -y -p /opt/rdkit --override-channels \
          -c https://conda.anaconda.org/conda-forge --strict-channel-priority \
          "python=$PYTHON_VERSION" "libboost-devel=1.90.0" "libboost-python-devel=1.90.0" \
          eigen cairo freetype expat numpy pandas pillow matplotlib-base pycairo \
          reportlab sqlalchemy setuptools setuptools_scm; then break; fi; \
      test "$attempt" != 3; \
      micromamba clean --index-cache -y; \
      sleep 5; \
    done; \
    mkdir -p /opt/rdkit/share/doc/rdkit /opt/rdkit/share/licenses/rdkit \
      /opt/rdkit/share/testdata; \
    micromamba list -p /opt/rdkit > /opt/rdkit/share/doc/rdkit/conda-packages.txt; \
    micromamba env export -p /opt/rdkit --explicit > /opt/rdkit/share/doc/rdkit/conda-explicit.txt

COPY docker/conda-licenses.py /opt/rdkit/share/testdata/conda-licenses.py
RUN set -eux; \
    python /opt/rdkit/share/testdata/conda-licenses.py collect; \
    micromamba clean -a -y

FROM dependencies AS builder
ARG TARGETARCH
ARG BUILD_JOBS=2
COPY docker/sources.json docker/prepare-sources.py /tmp/rdkit-packaging/

# Official RDKit and all fetched CMake inputs are pinned by URL and SHA256.
# A matching checksum proves identity, not perpetual upstream availability.
# Pre-extraction avoids CMake's mutable network fallback. The two skipped
# upstream preparation operations are replayed verbatim, not algorithm patches.
RUN python /tmp/rdkit-packaging/prepare-sources.py prepare \
      /tmp/rdkit-packaging/sources.json /build \
      /opt/rdkit/share/licenses/rdkit/source

ENV LD_LIBRARY_PATH=/opt/rdkit/lib
ENV PKG_CONFIG_PATH=/opt/rdkit/lib/pkgconfig
# No functional/numerical smoke in a build layer. Both native architectures
# run the same declared smoke and real wrapper tests after image construction.
RUN --network=none set -eux; \
    case "$TARGETARCH" in amd64) popcnt=ON ;; arm64) popcnt=OFF ;; *) exit 1 ;; esac; \
    cmake -S /build/rdkit -B /build/objects -G Ninja \
      -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/opt/rdkit \
      -DCMAKE_PREFIX_PATH=/opt/rdkit -DBoost_NO_SYSTEM_PATHS=ON \
      -DBOOST_ROOT=/opt/rdkit -DPython_EXECUTABLE=/opt/rdkit/bin/python \
      -DPython3_EXECUTABLE=/opt/rdkit/bin/python \
      -DPYTHON_INSTDIR=/opt/rdkit/lib/python3.12/site-packages \
      -DRDK_BUILD_PYTHON_WRAPPERS=ON -DRDK_BUILD_BOOST_PYTHON_WRAPPERS=ON \
      -DRDK_BUILD_NANOBIND_WRAPPERS=OFF -DRDK_BUILD_AVALON_SUPPORT=ON \
      -DRDK_BUILD_CAIRO_SUPPORT=ON -DRDK_BUILD_CONTRIB=ON \
      -DRDK_BUILD_CPP_TESTS=OFF -DRDK_BUILD_FREESASA_SUPPORT=ON \
      -DRDK_BUILD_INCHI_SUPPORT=ON -DRDK_BUILD_PGSQL=OFF \
      -DRDK_BUILD_XYZ2MOL_SUPPORT=ON -DRDK_BUILD_YAEHMOP_SUPPORT=ON \
      -DRDK_INSTALL_INTREE=OFF -DRDK_INSTALL_STATIC_LIBS=OFF \
      -DRDK_INSTALL_PYTHON_TESTS=OFF -DRDK_BUILD_RPATH_SUPPORT=ON \
      -DRDK_OPTIMIZE_POPCNT="$popcnt" \
      -DFETCHCONTENT_SOURCE_DIR_BETTER_ENUMS=/build/better-enums; \
    cmake --build /build/objects --parallel "$BUILD_JOBS"; \
    cmake --install /build/objects; \
    cp /build/rdkit/license.txt /opt/rdkit/share/licenses/rdkit/license.txt; \
    cp /build/rdkit/README.md /build/rdkit/ReleaseNotes.md /opt/rdkit/share/doc/rdkit/; \
    cp /build/objects/CMakeCache.txt /opt/rdkit/share/doc/rdkit/; \
    cp /tmp/rdkit-packaging/sources.json /opt/rdkit/share/doc/rdkit/; \
    cp /tmp/rdkit-packaging/prepare-sources.py /opt/rdkit/share/testdata/; \
    printf '%s\n' 'upstream_version=2026.09.2' 'upstream_tag=Release_2026_09_2' \
      'upstream_commit=f86b7dc9b31e2531200bbd1f54589bcbd968bb05' \
      'runtime_source=official-source-cmake-boost-python' \
      'upstream_algorithm_patch=none' "target_arch=$TARGETARCH" \
      > /opt/rdkit/share/doc/rdkit/source.txt; \
    rm -rf /opt/rdkit/conda-meta /opt/rdkit/include /opt/rdkit/lib/cmake \
      /opt/rdkit/lib/pkgconfig /opt/rdkit/share/info /opt/rdkit/share/man; \
    find /opt/rdkit/lib/python3.12/site-packages -type d \
      \( -name test -o -name tests \) -prune -exec rm -rf '{}' +; \
    find /opt/rdkit -type f \( -name '*.a' -o -name '*.pyc' \) -delete; \
    find /opt/rdkit -type d -name '__pycache__' -prune -exec rm -rf '{}' +; \
    rm -rf /build

FROM debian:12-slim@sha256:88200866dfff7ea7f5cbcb6ec7c8a701889efe6fe859fe64d6990e4b07ea4171
ENV DEBIAN_FRONTEND=noninteractive
ENV CONDA_PREFIX=/opt/rdkit
ENV RDBASE=/opt/rdkit/share/RDKit
ENV LD_LIBRARY_PATH=/opt/rdkit/lib
ENV PATH=/opt/rdkit/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ENV PYTHONNOUSERSITE=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV MPLBACKEND=Agg
ENV MPLCONFIGDIR=/tmp/matplotlib
ENV XDG_CACHE_HOME=/tmp/xdg-cache
# This final-stage APT resolution is also live, not frozen by the base digest.
RUN set -eux; \
    apt-get -o Acquire::Retries=3 update; \
    apt-get -o Acquire::Retries=3 install -y --no-install-recommends \
      ca-certificates coreutils findutils grep libc-bin; \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/rdkit /opt/rdkit
COPY docker/bin/rdkit-runtime-info /opt/rdkit/bin/rdkit-runtime-info
COPY docker/rdkit-smoke.py /opt/rdkit/share/testdata/rdkit-smoke.py
COPY docker/licenses/ /opt/rdkit/share/licenses/rdkit/embedded/
RUN --network=none set -eux; \
    (cd /opt/rdkit/share/licenses/rdkit/embedded && sha256sum -c SHA256SUMS); \
    chmod 0755 /opt/rdkit/bin/rdkit-runtime-info /opt/rdkit/share/testdata/rdkit-smoke.py; \
    python /opt/rdkit/share/testdata/conda-licenses.py verify; \
    python /opt/rdkit/share/testdata/prepare-sources.py verify /opt/rdkit/share/licenses/rdkit/source; \
    python -c 'import sys, rdkit; from rdkit.Chem import inchi, rdCoordGen, rdFreeSASA, rdSynthonSpaceSearch; from rdkit.Avalon import pyAvalonTools; assert sys.version_info[:3] == (3,12,13); assert rdkit.__version__ == "2026.09.2"; print(rdkit.__version__)'; \
    : > /tmp/rdkit-ldd.txt; \
    ldd /opt/rdkit/bin/python >> /tmp/rdkit-ldd.txt 2>&1; \
    find /opt/rdkit/lib -maxdepth 1 -type f -name 'libRDKit*.so*' \
      -exec sh -c 'for library do ldd "$library" >> /tmp/rdkit-ldd.txt 2>&1 || true; done' sh '{}' +; \
    find /opt/rdkit/lib/python3.12/site-packages/rdkit -type f -name '*.so' \
      -exec sh -c 'for library do ldd "$library" >> /tmp/rdkit-ldd.txt 2>&1 || true; done' sh '{}' +; \
    if grep -F 'not found' /tmp/rdkit-ldd.txt; then exit 1; fi; \
    rm -f /tmp/rdkit-ldd.txt

WORKDIR /root
ENV TAFFISH_ENV=TAFFISH
ENV TAFFISH_NAME=rdkit

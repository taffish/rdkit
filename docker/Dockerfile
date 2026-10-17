# 来源边界：基础镜像 digest 固定身份，不保证注册表永久保留。
FROM mambaorg/micromamba:1.5.10-bookworm-slim@sha256:e3797091302382ea841498bc93a7b0a50f7c1448333d5e946d2d1608d0c5f43d AS installed

ARG TARGETARCH
ARG RDKIT_VERSION=2026.09.1
ARG PYTHON_VERSION=3.12.13
ARG RDKIT_AMD64_BUILD=py312h5eb2359_0
ARG RDKIT_AMD64_SHA256=abf4c837c1e6cef61ab469872a644187a6d284f5a6a5c0167736ad1cec86bff1
ARG RDKIT_ARM64_BUILD=py312hf04553f_0
ARG RDKIT_ARM64_SHA256=65e92a5bc72abd7499663e5d67087a32e49044c4518afcbb0c50bbe5316c3dd4
ARG LIBRDKIT_AMD64_BUILD=h61648e3_0
ARG LIBRDKIT_AMD64_SHA256=fb78b6398a4d6ec28f98b2a382185e3e9540384a0a2ff15db6b0f1a742eb8283
ARG LIBRDKIT_ARM64_BUILD=h4ab84a9_0
ARG LIBRDKIT_ARM64_SHA256=2f30bac0ee79098b9bd588fdcaccff758b7439675a84563e67886666ebe210f9
ARG RDKIT_LICENSE_SHA256=daeb8d194502cbcf34c05c39541a0d02be65bc9bada5b891c1974cd24e9fca30
ARG RDKIT_README_SHA256=e3f46ec360f5aa3b8000ea36ea84bfc94511d60bcdb508fb3c19cc47a16dd1cd
ARG RDKIT_RELEASE_NOTES_SHA256=7d5c160c8f21e25e46dc3455893a996cb9d9e18e95dbfefc3965fac7b06a7c0c

USER root

ENV DEBIAN_FRONTEND=noninteractive
ENV MAMBA_ROOT_PREFIX=/opt/conda

# Debian 在线仓库的候选版本及保留期会变化；失效时先核对仓库事实，
# 以新的不可变 release 修复，不能将重试当作可复现或永久可下载保证。
RUN set -eux; \
    for attempt in 1 2 3 4 5; do \
      if apt-get -o Acquire::Retries=3 update \
       && apt-get -o Acquire::Retries=3 install -y --no-install-recommends \
            ca-certificates \
            coreutils \
            curl \
            findutils \
            grep; then \
        break; \
      fi; \
      if [ "${attempt}" = "5" ]; then exit 1; fi; \
      apt-get clean; \
      rm -rf /var/lib/apt/lists/*; \
      sleep 5; \
    done; \
    rm -rf /var/lib/apt/lists/*; \
    chown mambauser:mambauser /opt

USER mambauser

ENV CONDA_PREFIX=/opt/rdkit
ENV PATH=/opt/rdkit/bin:${PATH}

# RDKit/librdkit 按架构固定 build + SHA256，Python 固定版本；传递依赖仍由
# 当前 main repodata 求解，完整解保存在 conda-explicit.txt。归档下架/repodata
# 漂移应重新核对、验证并推进 release，不能放宽 checksum 或换成未审计的包。
# 下方官方文本同样以固定 tag + SHA256 验证；URL 可用性不属于身份保证。
RUN set -eux; \
    case "${TARGETARCH}" in \
      amd64) \
        rdkit_build="${RDKIT_AMD64_BUILD}"; \
        rdkit_sha256="${RDKIT_AMD64_SHA256}"; \
        librdkit_build="${LIBRDKIT_AMD64_BUILD}"; \
        librdkit_sha256="${LIBRDKIT_AMD64_SHA256}"; \
        conda_subdir="linux-64" \
        ;; \
      arm64) \
        rdkit_build="${RDKIT_ARM64_BUILD}"; \
        rdkit_sha256="${RDKIT_ARM64_SHA256}"; \
        librdkit_build="${LIBRDKIT_ARM64_BUILD}"; \
        librdkit_sha256="${LIBRDKIT_ARM64_SHA256}"; \
        conda_subdir="linux-aarch64" \
        ;; \
      *) \
        echo "unsupported TARGETARCH: ${TARGETARCH}" >&2; \
        exit 1 \
        ;; \
    esac; \
    micromamba create -y -p /opt/rdkit; \
    for attempt in 1 2 3; do \
      if micromamba install -y -p /opt/rdkit \
          -c https://conda.anaconda.org/conda-forge/label/main \
          --strict-channel-priority \
          "python=${PYTHON_VERSION}" \
          "rdkit=${RDKIT_VERSION}=${rdkit_build}" \
          "librdkit=${RDKIT_VERSION}=${librdkit_build}"; then \
        break; \
      fi; \
      if [ "${attempt}" = "3" ]; then exit 1; fi; \
      micromamba clean -a -y || true; \
      sleep 10; \
    done; \
    package_archive="$(find /opt/conda/pkgs -maxdepth 1 -type f -name "rdkit-${RDKIT_VERSION}-${rdkit_build}.conda" -print -quit)"; \
    test -n "${package_archive}"; \
    echo "${rdkit_sha256}  ${package_archive}" | sha256sum -c -; \
    library_archive="$(find /opt/conda/pkgs -maxdepth 1 -type f -name "librdkit-${RDKIT_VERSION}-${librdkit_build}.conda" -print -quit)"; \
    test -n "${library_archive}"; \
    echo "${librdkit_sha256}  ${library_archive}" | sha256sum -c -; \
    mkdir -p \
      /opt/rdkit/share/doc/rdkit \
      /opt/rdkit/share/licenses/rdkit \
      /opt/rdkit/share/testdata; \
    micromamba list -p /opt/rdkit > /opt/rdkit/share/doc/rdkit/conda-packages.txt; \
    micromamba env export -p /opt/rdkit --explicit > /opt/rdkit/share/doc/rdkit/conda-explicit.txt; \
    curl --retry 5 --retry-delay 2 --retry-all-errors -fsSL \
      "https://raw.githubusercontent.com/rdkit/rdkit/Release_2026_09_1/license.txt" \
      -o /opt/rdkit/share/licenses/rdkit/license.txt; \
    echo "${RDKIT_LICENSE_SHA256}  /opt/rdkit/share/licenses/rdkit/license.txt" | sha256sum -c -; \
    curl --retry 5 --retry-delay 2 --retry-all-errors -fsSL \
      "https://raw.githubusercontent.com/rdkit/rdkit/Release_2026_09_1/README.md" \
      -o /opt/rdkit/share/doc/rdkit/README.md; \
    echo "${RDKIT_README_SHA256}  /opt/rdkit/share/doc/rdkit/README.md" | sha256sum -c -; \
    curl --retry 5 --retry-delay 2 --retry-all-errors -fsSL \
      "https://raw.githubusercontent.com/rdkit/rdkit/Release_2026_09_1/ReleaseNotes.md" \
      -o /opt/rdkit/share/doc/rdkit/ReleaseNotes.md; \
    echo "${RDKIT_RELEASE_NOTES_SHA256}  /opt/rdkit/share/doc/rdkit/ReleaseNotes.md" | sha256sum -c -; \
    { \
      printf "upstream_repo=https://github.com/rdkit/rdkit\n"; \
      printf "upstream_tag=Release_2026_09_1\n"; \
      printf "upstream_commit=fece8caa860bdf6c9c82bdb9253f22a0cf87150c\n"; \
      printf "upstream_version=%s\n" "${RDKIT_VERSION}"; \
      printf "runtime_source=conda-forge/label/main::rdkit=%s=%s\n" "${RDKIT_VERSION}" "${rdkit_build}"; \
      printf "runtime_package_subdir=%s\n" "${conda_subdir}"; \
      printf "runtime_package_sha256=%s\n" "${rdkit_sha256}"; \
      printf "runtime_library_build=%s\n" "${librdkit_build}"; \
      printf "runtime_library_sha256=%s\n" "${librdkit_sha256}"; \
      printf "python_version=%s\n" "${PYTHON_VERSION}"; \
      printf "platform_note=Native linux/amd64 and linux/arm64 conda-forge builds are selected independently.\n"; \
      printf "scope_note=Python bindings, RDKit shared runtime libraries, runtime data, upstream Contrib files, and declared Python dependencies are included.\n"; \
      printf "boundary_note=PostgreSQL cartridge, development SDKs, alternate-language wrappers, Jupyter services, and optional Contrib-only dependencies are not included.\n"; \
    } > /opt/rdkit/share/doc/rdkit/source.txt

FROM installed AS builder

COPY docker/conda-licenses.py /tmp/conda-licenses.py

RUN set -eux; \
    python /tmp/conda-licenses.py collect; \
    rm -rf \
      /opt/rdkit/conda-meta \
      /opt/rdkit/include \
      /opt/rdkit/lib/cmake \
      /opt/rdkit/lib/pkgconfig \
      /opt/rdkit/share/info \
      /opt/rdkit/share/man; \
    find /opt/rdkit/lib/python3.12/site-packages \
      -type d \( -name test -o -name tests \) \
      -prune -exec rm -rf '{}' +; \
    find /opt/rdkit -type f \( -name '*.a' -o -name '*.pyc' \) -delete; \
    find /opt/rdkit -type d -name '__pycache__' -prune -exec rm -rf '{}' +; \
    micromamba clean -a -y; \
    rm -rf /home/mambauser/.cache

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

# 此 final stage 的 APT 仍是在线来源：固定 base digest 不会固定后续仓库解。
RUN set -eux; \
    for attempt in 1 2 3 4 5; do \
      if apt-get -o Acquire::Retries=3 update \
       && apt-get -o Acquire::Retries=3 install -y --no-install-recommends \
            ca-certificates \
            coreutils \
            findutils \
            grep \
            libc-bin; then \
        break; \
      fi; \
      if [ "${attempt}" = "5" ]; then exit 1; fi; \
      apt-get clean; \
      rm -rf /var/lib/apt/lists/*; \
      sleep 5; \
    done; \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/rdkit /opt/rdkit
COPY docker/bin/rdkit-runtime-info /opt/rdkit/bin/rdkit-runtime-info
COPY docker/rdkit-smoke.py /opt/rdkit/share/testdata/rdkit-smoke.py
COPY docker/conda-licenses.py /opt/rdkit/share/testdata/conda-licenses.py
COPY docker/licenses/ /opt/rdkit/share/licenses/rdkit/embedded/

RUN set -eux; \
    (cd /opt/rdkit/share/licenses/rdkit/embedded && sha256sum -c SHA256SUMS); \
    chmod 0755 /opt/rdkit/bin/rdkit-runtime-info /opt/rdkit/share/testdata/rdkit-smoke.py; \
    python /opt/rdkit/share/testdata/conda-licenses.py verify; \
    python --version 2>&1 | grep -F "Python 3.12.13" >/dev/null; \
    rdkit-runtime-info --version 2>&1 | grep -Fx "rdkit-runtime-info 2026.09.1" >/dev/null; \
    rdkit-runtime-info --json | grep -F '"rdkit": "2026.09.1"' >/dev/null; \
    python -m rdkit.Chem.ChemUtils.SDFToCSV --help 2>&1 | grep -F "Convert SDF file to CSV" >/dev/null; \
    python -c 'import rdkit; from rdkit import Avalon, Chem, DataManip, Dbase, DistanceGeometry, ForceField, Geometry, ML, Numerics, SimDivFilters, VLib; from rdkit.Chem import AllChem, Draw, PandasTools, inchi, rdCoordGen, rdFreeSASA, rdMolDescriptors; assert rdkit.__version__ == "2026.09.1"; mol = Chem.MolFromSmiles("CCO"); mol.SetName("ethanol"); assert mol.GetName() == "ethanol"; print(rdkit.__version__)' | grep -Fx "2026.09.1" >/dev/null; \
    : > /tmp/rdkit-ldd.txt; \
    ldd "$(command -v python)" >> /tmp/rdkit-ldd.txt 2>&1; \
    find /opt/rdkit/lib -maxdepth 1 -type f -name 'libRDKit*.so*' \
      -exec sh -c 'for library do ldd "$library" >> /tmp/rdkit-ldd.txt 2>&1 || true; done' sh '{}' +; \
    find /opt/rdkit/lib/python3.12/site-packages/rdkit -type f -name '*.so' \
      -exec sh -c 'for extension do ldd "$extension" >> /tmp/rdkit-ldd.txt 2>&1 || true; done' sh '{}' +; \
    if grep -F "not found" /tmp/rdkit-ldd.txt; then exit 1; fi; \
    rm -rf /tmp/rdkit-ldd.txt /tmp/matplotlib /tmp/xdg-cache /root/.cache

WORKDIR /root

ENV TAFFISH_ENV=TAFFISH
ENV TAFFISH_NAME=rdkit

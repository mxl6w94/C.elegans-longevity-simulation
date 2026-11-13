#
# C. elegans lifespan predictor: web app image.
#
# Serves the Flask app (web/) with Gunicorn, reading the precomputed pipeline
# results in core/results/ and the measured lifespans in core/data/. The modeling pipeline itself (COBRApy) is not in
# this image; it runs offline and its CSVs are copied in at build time.
#
#   docker build -t wormlife-web .
#   docker run --rm -p 8000:8000 --read-only --tmpfs /tmp wormlife-web
#   open http://localhost:8000
#
# On EC2, publish the port on localhost only (-p 127.0.0.1:8000:8000) and put
# Nginx in front of it, as described in the security plan.

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Unprivileged user with no login shell runs the app
RUN groupadd --system wormlife \
 && useradd --system --gid wormlife --no-create-home --shell /usr/sbin/nologin wormlife

# Dependencies first, so code changes don't reinstall them
COPY web/requirements.txt web/requirements.txt
RUN pip install -r web/requirements.txt gunicorn==27.0.0

# App code and the data files it reads. Files stay owned by root,
# so the app user can read them but not change them.
COPY web/ web/
COPY core/results/ core/results/
COPY core/data/ core/data/

USER wormlife

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/curves', timeout=4).status == 200 else 1)"

# Production server: no Flask debug mode, no Werkzeug dev server
CMD ["gunicorn", "--chdir", "web", "--bind", "0.0.0.0:8000", "--workers", "2", "--worker-tmp-dir", "/tmp", "--access-logfile", "-", "app:app"]

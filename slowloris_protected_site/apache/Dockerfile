FROM debian:bookworm-slim

# ── Install Apache & mod_evasive ────────────────────────────────────────────────
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
        apache2 \
        libapache2-mod-evasive && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# ── Switch to scalable event MPM + enable required modules ─────────────────────
RUN a2dismod mpm_prefork && \
    a2enmod  mpm_event reqtimeout evasive

# ── Copy vhost & hardening configs ─────────────────────────────────────────────
COPY 000-default.conf          /etc/apache2/sites-available/000-default.conf
COPY slowloris-hardening.conf  /etc/apache2/conf-available/slowloris-hardening.conf

RUN a2ensite 000-default.conf && \
    a2enconf slowloris-hardening.conf

# ── Web content ────────────────────────────────────────────────────────────────
COPY index.html /var/www/html/index.html

EXPOSE 80
CMD ["apache2ctl", "-D", "FOREGROUND"]

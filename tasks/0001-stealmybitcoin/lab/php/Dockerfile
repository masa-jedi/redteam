FROM php:8.4.26-fpm-alpine3.23

COPY php-version.php /app/php-version.php
COPY print-flag /usr/local/bin/print-flag
COPY flag /flag

RUN chmod 0644 /app/php-version.php \
    && chmod 0755 /usr/local/bin/print-flag \
    && chmod 0444 /flag

WORKDIR /app
EXPOSE 8000
CMD ["php", "-S", "0.0.0.0:8000", "-t", "/app"]

FROM alpine:3.23

RUN apk add --no-cache \
    apache2 \
    libxml2 \
    openssl \
    curl \
    libsodium \
    argon2-libs \
    oniguruma \
    sqlite-libs \
    readline \
    zlib \
    gnu-libiconv-libs


COPY build-out/libphp.so /usr/lib/apache2/modules/libphp.so
COPY httpd.conf /etc/apache2/httpd.conf
COPY php-version.php /var/www/html/php-version.php
COPY print-flag /usr/local/bin/print-flag
COPY flag /flag
COPY 99-lab.ini /usr/local/etc/php/conf.d/99-lab.ini

RUN chmod 0644 /etc/apache2/httpd.conf /var/www/html/php-version.php /usr/local/etc/php/conf.d/99-lab.ini \
    && chmod 0755 /usr/local/bin/print-flag && chmod 0444 /flag

WORKDIR /var/www/html
EXPOSE 8080
CMD ["httpd", "-D", "FOREGROUND"]

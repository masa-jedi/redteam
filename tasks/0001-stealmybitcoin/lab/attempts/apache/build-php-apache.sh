#!/bin/sh
# Build PHP 8.4.26 as an Apache module on Alpine, matching the official FPM
# image's configure flags plus --with-apxs2. Produces build-out/libphp.so.
#
# Usage (inside an alpine:3.23 container with /out mounted):
#   sh build-php-apache.sh <php-tar-xz-sha256>
set -eux

PHP_VERSION=8.4.26
PHP_SHA256="${1:?pass the php.net tarball sha256}"

exec >/out/build.log 2>&1

apk add --no-cache --virtual .build-deps \
    autoconf dpkg dpkg-dev file g++ gcc libc-dev make pkgconf re2c \
    apache2 apache2-dev argon2-dev coreutils curl-dev gnu-libiconv-dev libsodium-dev \
    libxml2-dev linux-headers oniguruma-dev openssl-dev readline-dev sqlite-dev \
    zlib-dev curl

mkdir -p /usr/src /out
cd /usr/src
curl -fsSL -o php.tar.xz "https://www.php.net/distributions/php-${PHP_VERSION}.tar.xz"
echo "${PHP_SHA256}  php.tar.xz" | sha256sum -c -
tar -xf php.tar.xz
cd "php-${PHP_VERSION}"

export CFLAGS="-fstack-protector-strong -fpic -fpie -O2 -D_LARGEFILE_SOURCE -D_FILE_OFFSET_BITS=64"
export CPPFLAGS="$CFLAGS"
export LDFLAGS="-Wl,-O1 -pie"
export PHP_BUILD_PROVIDER='https://github.com/docker-library/php'
export PHP_UNAME='Linux - Docker'

./configure \
    --build=x86_64-linux-musl \
    --sysconfdir=/usr/local/etc \
    --with-config-file-path=/usr/local/etc/php \
    --with-config-file-scan-dir=/usr/local/etc/php/conf.d \
    --enable-option-checking=fatal \
    --with-mhash \
    --with-pic \
    --enable-mbstring \
    --enable-mysqlnd \
    --with-password-argon2 \
    --with-sodium=shared \
    --with-pdo-sqlite=/usr \
    --with-sqlite3=/usr \
    --with-curl \
    --with-iconv=/usr \
    --with-openssl \
    --with-readline \
    --with-zlib \
    --disable-phpdbg \
    --with-pear \
    --disable-cgi \
    --enable-fpm \
    --with-fpm-user=www-data \
    --with-fpm-group=www-data \
    --with-apxs2=/usr/bin/apxs

make -j"$(nproc)"

test -f libs/libphp.so
nm libs/libphp.so | grep -E ' (zval_ptr_dtor|zif_system)$' | tee /out/symbols-apache.txt
cp libs/libphp.so /out/libphp.so
cp sapi/cli/php /out/php-cli
ls -l /out

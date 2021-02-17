#!/bin/sh

. $(dirname "$0")/base.sh

DjangoSettings="sites.$SITE.settings.django"

app_labels() {
    echo "`$pyt -c \"from $DjangoSettings import APP_LIST; print(\\\" \\\".join(x.rsplit('.')[-1] for x in APP_LIST))\"`"
}

app_paths() {
    echo "`$pyt -c \"from $DjangoSettings import APP_LIST; print(\\\" \\\".join(x.replace('.', '/') for x in APP_LIST))\"`"
}

db_name() {
    x=`$pyt -c "from $DjangoSettings import DATABASES; print(DATABASES['default']['NAME'])"`
    echo $x
}

setup_db() {
    db=`db_name`
    echo "Mysql root"
    sudo mysql -uroot -p -e "CREATE USER IF NOT EXISTS '$MYSQL_USER'@'localhost' IDENTIFIED BY '$MYSQL_PASSWORD'; GRANT ALL PRIVILEGES ON $db.* TO '$MYSQL_USER'@'localhost'; FLUSH PRIVILEGES;"
}

init_db() {
    db=`db_name`
    echo "Mysql $MYSQL_USER"
    mysql -u$MYSQL_USER -p$MYSQL_PASSWORD -e "CREATE DATABASE IF NOT EXISTS $db DEFAULT CHARACTER SET = 'utf8mb4' DEFAULT COLLATE 'utf8mb4_unicode_ci';"
}

init_dirs() {
    for x in migrations static media
    do
        mkdir -p ${1}_$x
    done
}

init_links() {
    for x in static media
    do
        ln -sf ${1}_$x $x
    done
}

collectstatic() {
    $pyt manage.py collectstatic --no-input
}

makemigrations() {
    $pyt manage.py makemigrations `app_labels`
}

migrate() {
    $pyt manage.py migrate
}

init_migrations() {
    for x in `app_paths`
    do
        mkdir -p $1_migrations/$x
        ln -sf $1_migrations/$x $x/migrations
    done
}

init_sites() {
    $pyt manage.py shell -c "from base.settings import DjangoUtil; DjangoUtil.init_sites()"
}

createsuperuser() {
    $pyt manage.py createsuperuser
}

clean() {
    db=`db_name`
    for x in `app_paths`
    do
        rm -rf $x/migrations
    done
    echo "Mysql $MYSQL_USER"
    mysql -u$MYSQL_USER -p$MYSQL_PASSWORD -e "drop database $db";
}

dev() {
    init_db
    makemigrations
    migrate
}

#crawler-machine.
grant_db_access() {
    db=`db_name`
    echo "MYSQL Root Password"
    sudo mysql -uroot -p$MYSQL_ROOT_PASSWORD -e "CREATE USER IF NOT EXISTS '$MYSQL_USER'@'$MYSQL_HOST' IDENTIFIED BY '$MYSQL_PASSWORD'; GRANT ALL PRIVILEGES ON $db.* TO '$MYSQL_USER'@'$MYSQL_HOST'; FLUSH PRIVILEGES;"
}

$1

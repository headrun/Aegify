#!/bin/sh

. $(dirname "$0")/base.sh
. $(dirname "$0")/django.sh

webserver() {
    if [ -z $ENV_HOME ] || [ -z $ENV_PROJECT ] || [ -z "$ENV_SITES" ] || [ -z $ENV_NUM_PROCESSES ]
    then
        echo "define ENV_HOME, ENV_PROJECT, ENV_NUM_PROCESSES, ENV_SITES in ~/.bashrc"
        exit 1
    fi

    release_dir=$g_project_dir

    cd $ENV_HOME
    init_dirs $ENV_PROJECT

    cd $release_dir/
    proj_abs=$ENV_HOME/$ENV_PROJECT
    init_links $proj_abs
    collectstatic

    init_db
    init_migrations $proj_abs
    makemigrations

    home_esc="`echo $ENV_HOME | sed -e "s/\//\\\\\\\\\//g"`"
    for each_site in $ENV_SITES
    do
        exp="s/##home##/$home_esc/g; s/##project##/$ENV_PROJECT/g; s/##site_url##/$each_site/g; s/##num_proc##/$ENV_NUM_PROCESSES/g"
        if [  $ENV_HTTPS ]
        then
            suffix="https"
        else
            suffix="http"
        fi
        src_conf="sites/$SITE/nginx_$suffix.conf"
        if [ ! -f "$src_conf" ]
        then
            src_conf="deploy/nginx_$suffix.conf"
        fi
        sed -e "$exp" $src_conf > deploy/${each_site}.nginx.conf
    done
    sed -e "$exp" deploy/uwsgi.ini > deploy/${ENV_PROJECT}_uwsgi.ini

    set +e
    uwsgi --stop $ENV_HOME/${ENV_PROJECT}_uwsgi.pid
    sudo /etc/init.d/nginx stop
    set -e
    sleep 1

    if [ -f "$ENV_HOME/$ENV_PROJECT/sites/$SITE/config/node.js" ]
    then
        pm2 stop $ENV_HOME/$ENV_PROJECT/deploy/pm2.config.js
    fi

    migrate
    init_sites

    cd $ENV_HOME
    ln -sfn $release_dir $ENV_PROJECT
    sudo rm -f /etc/nginx/sites-enabled/$SITE.conf
    for each_site in $ENV_SITES
    do
        sudo ln -sf $ENV_HOME/$ENV_PROJECT/deploy/${each_site}.nginx.conf /etc/nginx/sites-enabled/$each_site.conf
    done

    uwsgi --ini $ENV_HOME/$ENV_PROJECT/deploy/${ENV_PROJECT}_uwsgi.ini

    if [ -f "$ENV_HOME/$ENV_PROJECT/sites/$SITE/config/node.js" ]
    then
        pm2 start $ENV_HOME/$ENV_PROJECT/deploy/pm2.config.js
    fi

    sudo /etc/init.d/nginx start
}

crawler() {
    if [ -z $ENV_HOME ] || [ -z $ENV_PROJECT ]
    then
        echo "define ENV_HOME, ENV_PROJECT in ~/.bashrc"
        exit 1
    fi

    release_dir=$g_project_dir

    cd $ENV_HOME
    ln -sfn $release_dir $ENV_PROJECT
}

all() {
    webserver
    crawler
}


main() {
    if [ -z $ENV_SERVER_TYPE ]
    then
        webserver $1
    else
        $ENV_SERVER_TYPE $1
    fi
}

main $1

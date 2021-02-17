#!/bin/sh

. $(dirname "$0")/base.sh

basic_pkgs="vim python3-pip"
mysql_pkgs="mysql-server libmysqlclient-dev mysql-client python3-mysqldb python3-setuptools python3-dev build-essential"
django_pkgs="mysqlclient==1.4.6 django==3.0.1 django-mysql==3.2.0 django-rest_framework==0.1.0 django-oauth-toolkit==1.2.0 jsondiff==1.2.0 django-celery-beat==2.0.0 crochet==1.12.0 PyYAML==5.3.1 drf-renderer-xlsx==0.3.7"
scrapy_pkgs="scrapy==1.8.0 scrapyd==1.2.1 scrapy-user-agents==0.1.1 scrapy-crawlera==1.7.0 python-dateutil==2.8.1 xmltodict==0.12.0 json2table==1.1.5 textract==1.6.3 googletrans==3.0.0 translate==3.5.0"
api_common_pkgs="schematics==2.1.0 XlsxWriter==1.2.9 python-scrapyd-api==2.1.2"
npm_pkgs="airport-timezone express puppeteer puppeteer-extra-plugin-stealth puppeteer-extra axios moment deepcopy moment-timezone prompt dateformat fs request prompt-sync mailparser lodash winston-mongodb mongoose"
selenium_pkgs="selenium==3.141.0 pyvirtualdisplay==1.3.2"
python_pkgs="pillow==7.2.0 svglib==1.0.1"
flask_pkgs="alembic==1.4.2 click==7.1.2 Flask==1.1.2 Flask-Migrate==2.5.3 Flask-Script==2.0.6 Flask-SQLAlchemy==2.4.4 Flask-WTF==0.14.3 itsdangerous==1.1.0 Jinja2==2.11.2 Mako==1.1.3 MarkupSafe==1.1.1 numpy==1.19.1 pandas==1.0.5 python-dateutil==2.8.1 python-editor==1.0.4 pytz==2020.1 six==1.15.0 SQLAlchemy==1.3.18 Werkzeug==1.0.1 WTForms==2.3.3"

goaccess() {
	#for more reference https://goaccess.io/download
	if [ ! -z $ENV_GOACCESS_SETUP ]
	then
		sudo apt-get install libncursesw5-dev libgeoip-dev libmaxminddb-dev libtokyocabinet-dev libssl-dev;
		wget https://tar.goaccess.io/goaccess-1.3.tar.gz;
		tar -xzvf goaccess-1.3.tar.gz;
		cd goaccess-1.3/;
		./configure --enable-utf8 --enable-geoip=legacy;
		sudo make;
		sudo make install;
		cd ..
		sudo rm -rf goaccess-1.3/
		sudo mv goaccess-1.3.tar.gz ~/
    else
        echo "export <ENV_GOACCESS_SETUP> to install goaccess"
	fi
}

apt_install() {
    sudo apt-get install $1
}

pip_install() {
    sudo -H pip3 install $1
}

npm_install() {
    npm install $1
}

lockrun() {
    binpath="/usr/local/bin/lockrun"
    if [ ! -f $binpath ]
    then
        file="lockrun.c"
        URL="http://www.unixwiz.net/tools/$file"
        wget "${URL}"
        cc ${file} -o tmp
        sudo mv tmp ${binpath}
        rm $file
    fi
}

base_server() {
    apt_install "$basic_pkgs $mysql_pkgs"
    pip_install "$django_pkgs $api_common_pkgs $python_pkgs $flask_pkgs"
    pip_install "-U mysqlclient==1.4.6"
    lockrun
}

webserver() {
    apt_install "nginx"
    pip_install "uwsgi==2.0.18"

    . $(dirname "$0")/django.sh
    setup_db

    goaccess
}

pm_install(){
	sudo npm i -g pm2
}

npm_pkg_install(){
	npm_install "$npm_pkgs"
}

geckodriver() {
    env_gdv=$1
    binpath=/usr/local/bin/geckodriver
    if [ ! -f $binpath ]
    then
        if [ ! -z $env_gdv ]
        then
            fl=geckodriver-$env_gdv-linux64.tar.gz
            echo $fl
            curl -L -o $fl "https://github.com/mozilla/geckodriver/releases/download/$env_gdv/$fl"
            tar -xvzf $fl
            sudo mv geckodriver $binpath
            rm $fl
        else
            echo "export ENV_GDV=<version> look at for version https://github.com/headrun/Tracking/wiki/selenium-geckodriver-install"
        fi
    fi
}

selenium(){
    if [ ! -z $ENV_SELENIUM ]
    then
        pip_install "$selenium_pkgs"
        apt_install "curl xvfb"

        #geckodriver version as v0.27.0
        geckodriver v0.27.0

    fi

}

puppeteer() {
    if [ ! -z $ENV_PUPPETEER ]
    then
        set +e
        nv=`nodejs -v 2>/dev/null`
        set -e

        mnv=${nv%%\.*}
        if [ "$mnv" != $ENV_MNV ]
        then
            pip_install "$selenium_pkgs"
            apt_install "curl"
            curl -sL https://deb.nodesource.com/setup_14.x | sudo -E bash -
            apt_install "nodejs"
            sudo npm i

            npm_install "$npm_pkgs"
            pm_install
        fi

        #geckodriver version as v0.26.0
        geckodriver v0.26.0
    fi
}

crawler() {
    pip_install "$scrapy_pkgs"

    puppeteer
    selenium
}

all() {
    webserver
    crawler
}

dev() {
    pip_install "django-debug-toolbar==2.1"
    crawler

    goaccess
}

main() {
    if [ -z $ENV_SERVER_TYPE ]
    then
        echo "ENV_SERVER_TYPE is not set. all/webserver/crawler/dev"
    else
        base_server
        $ENV_SERVER_TYPE
    fi
}

main $1

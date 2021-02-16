# Aegify_Parse

# Table of contents

 1. [Table of contents](#table-of-contents)
 1. [OS](#os)
 1. [Production](#production)
      1. [Setup](#setup)
      1. [Install](#install)
      1. [Create Admin](#create-admin)
      1. [Cronjob](#cronjobs)
      1. [Https](#https)


## OS
Ubuntu bionic - 18.04

## Production

### Setup
-> Create user, say *appuser*
 ```
 ssh root@<ip>
 adduser <user>
 usermod -aG sudo <user>
 exit
 ```
-> Initialize and Install pre-requisites
 ```
 ssh <user>@<ip>
 mkdir releases
 exit

 scp -r <release>.tgz <user>@<ip>:~/releases/
 ssh <user>@<ip>

 sudo apt-get upgrade
 sudo apt-get update

 # Add the below lines to ~/.bashrc.
   export ENV_HOME=~
   export ENV_PROJECT=<project>

   export ENV_SERVER_TYPE=<all/webserver/crawler/dev>

   #For ENV_SERVER_TYPE all/webserver
   export ENV_SITES=<site>.headrun.com
   export ENV_NUM_PROCESSES=<int>

   #For ENV_SERVER_TYPE all/crawler
   export ENV_CONCURRENT_REQUESTS=<int>
   #For Selenium
   export ENV_SELENIUM=<selenium>
   #To export selenium driver path
   export ENV_GECKODRIVER_EXECUTABLE_PATH=<driver_executable_path>
   #For Puppeteer
   export ENV_PUPPETEER=<puppeteer>
   export ENV_MNV=<node version> #v14

   export SITE=<sites/name>

   #For HTTPS and PROD
   export ENV_HTTPS=True

   export MYSQL_DATABASE=<db_name>#optional
   export MYSQL_USER=<user>
   export MYSQL_PASSWORD=<password>
   export MYSQL_HOST=<hostname>#optional
   export MYSQL_PORT=<port>#optional

   #To extend the oauth token expiration
   export ENV_OAUTH_TOKEN_EXPIRE_SECONDS=<seconds>

 source ~/.bashrc

 tar -xzf releases/<release>.tgz
 cd <release>
 sh deploy/setup.sh
 sh deploy/upgrade.sh

 if ENV_SERVER_TYPE=<all/webserver/dev>
    sh deploy/django.sh createsuperuser

 if ENV_SERVER_TYPE=<crawler>
    ###Grant acess of DB to ENV_SERVER_TYPE=<crawler> by following these steps:
        1. export MYSQL_ROOT_PASSWORD=<mysql_root_password>
        2. source ~/.bash_profile.<site>
        3. sh deploy/django.sh grant_db_access
        4. Do following changes in mysql configuration file:
            -sudo vim /etc/mysql/mysql.conf.d/mysqld.conf and comment bind-address. 
            -sudo service mysql restart.

 exit
 ```
#if we faced any nginx-issue, please add the below config.
### Nginx Logs Format

 ```
 Add below settings into nginx.conf for api_mchines.
 vim /etc/nginx/nginx.conf

 log_format main '$remote_addr - $remote_user [$time_local] '
                    '"$request" $status $body_bytes_sent '
                    '"$http_referer" "$http_user_agent" '
                    '$request_time $upstream_response_time '
                    '"$http_host" $ssl_protocol ';
 ```

### Install
Install the project/application.

 ```
 scp -r <release>.tgz <user>@<ip>:~/releases/
 ssh <user>@<ip>

 #enable the respective bash_profile like source ~/.bash_profile.<SITE>
 sh <project>/deploy/install.sh releases/<release>.tgz

 If installation fails because of third party packages, then
 sh <release>/deploy/setup.sh
 continue installation as above
 ```

### Cronjobs
Schedule the below command in crontab or django celery etc., Use Lockrun or something similar to make sure only one process is running.

#### Crawl Cron
 ```
 export SITE=<site>; export SCRAPY_PROJECT=$SITE.<SCRAPY_APP>; export CMD_HOME=/home/<user>/<project>; cd $CMD_HOME; python3 crawl/scrapy/process.py 2>&1 >> $CMD_HOME/process.log
 ```

 #### DataBase bkup Cron
 ```
 export CMD_HOME=/home/<user>/<project>; cd $CMD_HOME; source /home/<user>/.bash_profile.<site_name>; python3 base/database_backup.py -s <your-bkup-server-ip> -u <bkup-server-user> -p <bkup-password>
 ```

### Https
Installing key and certificate files for Https.
 ```
 create a directory <site>.headrun.com with ssl.crt and ssl.key
 scp -r <site>.headrun.com <user>@<ip>:~/
 ssh <user>@<ip>
 sudo mv <site>.headrun.com /etc/ssl/private/
 cd /etc/ssl/private
 chown -R root:root <site>.headrun.com
 cd <site>.headrun.com
 chmod 640 ssl.key
 chmod 644 ssl.crt
 exit


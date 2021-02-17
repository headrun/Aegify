import ftplib
import os
import traceback
import logging
import sys
import ast
import subprocess
import socket
sys.path.insert(1, os.getcwd())
from datetime import datetime, timedelta
from optparse import OptionParser

from base.utils import standalone_main, init_logger, close_logger
from daily_mail_alerts import ItemStatus

def get_timestamp():
    timestamp = datetime.now().strftime('%d-%m-%Y_%H_%M_%S')
    return timestamp

class DailyBackup(object):
    def parse(self):
        parser = OptionParser()
        parser.add_option("-s", "--server", dest="server", default=False, help="server ip or domain name")
        parser.add_option("-u", "--user", dest="user", default=False, help="server user")
        parser.add_option("-p", "--password", dest="password", default=False, help="server password")
        parser.add_option("-b", "--days", dest="days", default=15, type=int, help="To Remove the Old Backp Files from FTP")
        parser.add_option("-m", "--media-files-backup", dest="media_files", default=False, help="Backup Media Files")
        parser.add_option("-d", "--db-backup", dest="db_backup", default=False, help="DataBase BackUp")
        parser.add_option("", "--site", dest="site_db_backup", action="store_true", default=False, help="To backup the database based on site options")
        parser.add_option("-l","--app-db-lable", dest="app_db_backup", default="", help="to backup db based on app_name")
        (self.options, args) = parser.parse_args()
        self.log = init_logger(
            os.path.join(__file__.rstrip('.py') + '.log'),
            level=logging.INFO,
        )

    def close(self):
        close_logger(self.log)

    def process(self):
        self.site=site  = os.environ.get('SITE', '')
        project         = os.environ.get('ENV_PROJECT', '')
        backup_server   = self.options.server
        server_user     = self.options.user
        server_password = self.options.password
        days            = self.options.days

        if self.options.db_backup:
            database_name   = os.environ.get('MYSQL_DATABASE', '')
            db_user         = os.environ.get('MYSQL_USER', '')
            db_password     = os.environ.get('MYSQL_PASSWORD', '')
            try:
                os.system('mysqldump -u %s -p%s %s > %s.sql' %(db_user, db_password, database_name, site))
            except Exception as e:
                self.log.error("Failed while taking dump db_user=%s, db_password=%s, database_name=%s, site=%s"%(db_user, db_password, database_name, site))
                traceback.print_exc()
                return

            file_name = "%s_databackup_%s.tar.gz" % (site, get_timestamp())
            try:
                os.system('tar -czvf %s %s.sql' %(file_name, site))
                os.system('rm -rf %s.sql'%site)
            except Exception as e:
                self.log.error("Not able to create zip file %s"%file_name)
                traceback.print_exc()
                return
            self.file_upload(file_name=file_name,
                             dest_dir=project,
                             server=backup_server,
                             u_name=server_user,
                             password=server_password,
                             days=days,
                             old_files=1,
                             bkup_type="db_bkup"
                            )

        if self.options.site_db_backup:
            app_list     = self.options.app_db_backup.split(',') if self.options.app_db_backup else ast.literal_eval(os.environ.get('APP_LIST', "[]"))
            if not app_list:
                self.log.error("Unable to find the APP_LIST for site {}".format(site))
                return

            file_name   = "%s_databackup_%s.tar.gz" % (site, get_timestamp())
            db_dir      = "{}_db_backup".format(site)
            email_text  = {}
            if not os.path.isdir(db_dir):
                os.makedirs(db_dir)

            for _app in app_list:
                _app_lable = _app.split('.')[-1]
                process_command = "python3 manage.py dumpdata {} > {}_app_db.json".format(
                    _app_lable,
                    os.path.join(db_dir, _app_lable)
                )
                try:
                    os.system(process_command)
                except Exception as db_err:
                    email_text[_app_lable] = str(db_err)
            try:
                tar_cmd = "tar -cvzf {} {}".format(file_name, db_dir)
                _process = subprocess.Popen(
                        tar_cmd.split(),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                sucess, error = _process.communicate()
                if not error:
                    os.system('rm -rf {}'.format(db_dir)) # remove the db_backup dir from local-storage
            except Exception as tar_err:
                self.log.error("Not able to create tar file %s"%file_name)
                traceback.print_exc()
                return
            #upload file into ftp-server
            self.file_upload(file_name=file_name,
                            dest_dir=project,
                            server=backup_server,
                            u_name=server_user,
                            password=server_password,
                            days=days,
                            old_files=1,
                            bkup_type="db_bkup",
                            extra_args=email_text)

        if self.options.media_files:
            media_dir_path   = os.environ.get('MEDIA_PATH','')
            if not media_dir_path:
                media_dir_path  = os.path.join(os.path.abspath(os.getcwd()), "media")

            if os.path.isdir(media_dir_path) and "media" in media_dir_path:
                file_name = "%s_media_backup_%s.tar.gz" % (site, get_timestamp())
                try:
                    os.system('tar -czvf %s %s' %(file_name, media_dir_path))
                except Exception as media_err:
                    self.log.error("Not able to create zip file %s"%file_name)
                    traceback.print_exc()
                    return

                self.file_upload(file_name=file_name,
                                 dest_dir=project,
                                 server=backup_server,
                                 u_name=server_user,
                                 password=server_password,
                                 days=days,
                                 old_files=1,
                                 bkup_type="media_bkup"
                            )

    def login_to_ftp_server(self, server, u_name, password):
        try:
            ftp = ftplib.FTP(server)    # Connect to the host with default port
            ftp.login(u_name, password)   # UserName, Password
            self.log.info('succesfully connected')
            return ftp
        except Exception as e:
            self.log.error("connection failed for server=%s"%server)
            subject = "connection failed for server %s"%server
            ItemStatus.send_mail(self, subject=subject, text=str(e) + str(traceback.format_exc()))
            print(traceback.print_exc())
            return 

    def remove_old_files(self, ftp, days, filename="_databackup_"):
        old_date    = (datetime.now() - timedelta(days=days)).strftime('%d-%m-%Y')
        files_list  = []
        try:
            old_file = self.site + filename + old_date
            files_list = [ ftp.delete(f_name) for f_name in ftp.nlst() if old_file in f_name ]
            return {
                "Removed Old File":files_list
            }
        except:
            self.log.info("Not able to delete files %s" %files_list)
            return {
                "Not able to delete files" : files_list
            }

    def file_upload(self, file_name, dest_dir, server, u_name, password, days, old_files, bkup_type=None, extra_args={}):
        host_name = socket.gethostname()
        ftp = self.login_to_ftp_server(server, u_name, password)
        try:
            try:
                try:
                    ftp.cwd(dest_dir)
                except:
                    ftp.mkd(dest_dir)
                    ftp.cwd(dest_dir)
                f = open(file_name, 'rb')
                ftp.storbinary('STOR %s' % file_name, f)  # Transfer the file to destination
                f.close()
                self.log.info("upload success %s" % file_name)
                stat = os.stat(file_name)
                default_text_status = {
                        "upload_file": file_name,
                        "status":"success",
                        "bkup_type": bkup_type,
                        "host_name": host_name,
                        "file-size": str(round(stat.st_size/(1024 * 1024 * 1024), 3)) + "GB"
                    }
                os.system("rm -rf %s" % file_name)
                if old_files:
                    if bkup_type == "media_bkup":
                        old_removed_status = self.remove_old_files(ftp=ftp,
                                                days=days,
                                                filename="_media_backup_")
                    else:
                        old_removed_status = self.remove_old_files(ftp, days)
                    default_text_status.update(old_removed_status)

                if extra_args:
                    default_text_status.update(extra_args)

                if bkup_type == "db_bkup":
                    subject = "dbname: " + os.environ.get('MYSQL_DATABASE','') + '--backup upload success'
                elif bkup_type == "media_bkup":
                    subject = "LTL Document Images: backup upload success"

                if bkup_type:
                    ItemStatus.send_mail(self, subject=subject, text=str(default_text_status))
            finally:
                ftp.quit()
        except Exception as e:
            if bkup_type == "db_bkup":
                subject = "dbname: "+ os.environ.get('MYSQL_DATABASE','') + '--backup upload Failed'
            elif bkup_type == "media_bkup":
                subject = "LTL Document Images: backup upload Failed"

            ItemStatus.send_mail(self, subject=subject, text=str({
                    "status":"failed",
                    "failed_upload_file": file_name,
                    "bkup_type": bkup_type,
                    "host_name": host_name,
                    "err_msg":str(e) + str(traceback.format_exc())
                }))
            self.log.error(e)
            traceback.print_exc()
            return


if __name__ == '__main__':
    standalone_main(DailyBackup) 

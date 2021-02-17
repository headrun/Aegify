import datetime
import subprocess
import os, sys, logging, traceback, re
from optparse import OptionParser
from collections import OrderedDict
import socket
import datetime as DT
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.text import MIMEText

sys.path.insert(1, os.getcwd())
from django.db.models import Count
from django.utils import timezone
from django.db.models import Q
import pytz
from base.settings import DjangoUtil;DjangoUtil.setup()
from base.utils import standalone_main, init_logger, close_logger, import_module_var
from django.db import connections
from django.db.utils import OperationalError

class ItemStatus:
    def parse(self):
        parser = OptionParser()
        parser.add_option("-n", "--new-item", dest="new_item", help="Newly Added Items", default=False)
        parser.add_option("-u", "--updated-item", dest="updated_item", help="Updated Items", default=False)
        parser.add_option("-t", "--time", dest="time", help="time in hours", default=3)
        parser.add_option("-d", "--disk-space", dest="disk_space", help="send the alert mail for disk", default=False)
        parser.add_option("-p", "--partition", dest="disk_partition", help="disk partition for verify space", default="/")
        parser.add_option("-s", "--threshold", dest="min_threshold", help="minimum threshold", default=50, type=int)
        parser.add_option("-x", "--max-threshold", dest="max_threshold", help="To get as High-Alert", default=75, type=int)
        parser.add_option("-m", "--app-models", dest="app_models", default='', help="app models path. default is ${SCRAPY_PROJECT}.models.")
        parser.add_option("-k", "--db-server-status", dest="db_server_status", help="send the alert mail for mysql", default=False)
        parser.add_option("-a", "--media-newly-files", dest="media_newly_files", help="count the number of docs present per day", default=False)
        parser.add_option("", "--media-path", dest="media_path", help="path of media storage", default="media")
        parser.add_option("-c", "--crawl-name", dest="crawl_name", help="name of the crawlrun", default="Default")
        parser.add_option("--process_time", dest="process_time", help="process max limit time", default='')
        parser.add_option("--process_name", dest="process_name", help="process name: aux|cmd for example testrun.lock", default='')

        parser.add_option("--subject", "--alert-mail-sub-name", dest="alert_mail_sub_name",
                        help="Mail Subject Name", default='')

        parser.add_option("--logname", "--crawlrun-log-name", dest="crawlrun_log_name",
                        help="crawlrun related logname to get stats",
                        default='item_logs')

        (self.options, args) = parser.parse_args()
        models = self.options.app_models if self.options.app_models else '%s.models' % os.environ['SCRAPY_PROJECT']
        self.app_models = import_module_var(models, None)
        if not self.app_models:
            raise Exception('Unable to import module: %s' % models)

        self.log = init_logger(
            os.path.join(__file__.rstrip('.py') + '.log'),
            level=logging.INFO,
        )

    def process(self):
        if self.options.media_newly_files:
            site_name = os.environ.get('SITE', None)
            media_cmd = "find {} -type f -printf '%TY-%Tm-%Td\n' | sort | uniq -c | tail -n 2 > media_file.txt".format(
                self.options.media_path)
            try:
                os.system(media_cmd)
                with open("media_file.txt","r") as f:
                    data = f.read()
                media_stats = data.split('\n')

                subject = '{} @ Newly added Documents w.r.t All Sources on {}'.format(
                    site_name,
                    datetime.datetime.strftime(datetime.datetime.now(), "%b %d, %Y"))

                text = '''<br /><br /><b>Media Files Stats @ {}.</b><br /><br />
                <table border="1" style="border-collapse:collapse;" cellpadding="6px" cellspacing="8px">
                <tr>'''.format(datetime.datetime.strftime(datetime.datetime.now(), "%b %d, %Y"))
                headers = ['no.of_documents_added_per_day', 'date']
                for header in headers:
                    text += '<th>{}</th>'.format(header)
                text+='</tr>'
                for stats in media_stats:
                    if stats:
                        text+='<tr>'
                        for val in stats.split():
                            text+='<td>{}</td>'.format(val)
                        text+='</tr>'
                self.send_mail(subject, text)
                os.system('rm -rf media_files.txt')
            except Exception as error:
                self.log.info(" Unable to send the stats for media-documents {}".format(str(error)))

        if self.options.new_item:
            self.log.info('Newly Added Item Mail')
            self.log.info('App Models:%s' % self.app_models)

            item_model      = getattr(self.app_models,'Item', None)
            source_model    = getattr(self.app_models,'Source', None)
            site_name       = os.environ.get('SITE', None)
            site_app_name   = os.environ.get('SCRAPY_PROJECT', None)

            if not item_model:
                raise Exception('%s does not have %s model' % (self.app_models, item_model))

            source_objects  = source_model.objects.all()
            item_crawled    = OrderedDict()
            time_threshold  = timezone.now() - datetime.timedelta(hours=int(self.options.time))

            for source_object in source_objects:
                source_name = source_object.name
                item_crawled[source_name]   = OrderedDict()
                items       = item_model.objects.filter(
                    Q(source=source_object,
                      created_at__gte=time_threshold)
                    ).select_related('source')
                item_crawled[source_name]['TotalCount']     = items.count()
                item_crawled[source_name]['Available']      = 0
                item_crawled[source_name]['Un-Available']   = 0

                for item in items:
                    data = list(item.data_list.values())
                    if data:
                        item_crawled[source_name]['Available']  += 1
                        continue
                    item_crawled[source_name]['Un-Available']   += 1

            self.log.info('Item crawled w.r.s:%s' % item_crawled)
            text = '<br /><br /><b>Tracking_ids  crawl status with respect to each source on %s.</b><br /><br /><table border="1" \
                    style="border-collapse:collapse;" cellpadding="6px" cellspacing="8px"><tr>'%datetime.datetime.strftime(datetime.datetime.now(), "%b %d, %Y")
            headers = [
                'Source',
                'TotalCount',
                'Available',
                'Not Available'
            ]
            for header in headers:
                text += '<th>%s</th>' % header
            text += '</tr>'

            is_sent_mail = False
            for key, val in item_crawled.items():
                if not val['TotalCount']:
                    continue
                is_sent_mail=True
                text    += '<tr>'
                text    += '<td>%s</td>' % (key)
                for i, j in val.items():
                    text+='<td>%s</td>' % (j)
                text    += '</tr>'

            subject_outline = self.get_subject_outline()
            if site_name or site_app_name:
                subject = "{}:{} {} Newly added Keys with respect to each source on {}".format(
                    site_name,
                    site_app_name,
                    subject_outline,
                    datetime.datetime.strftime(
                        datetime.datetime.now(), "%b %d, %Y"))
            else:
                host_name = socket.gethostname()
                subject = '{} {} Newly added Keys with respect to each source on {}'.format(
                    host_name,
                    subject_outline,
                    datetime.datetime.strftime(
                        datetime.datetime.now(), "%b %d, %Y"))

            if is_sent_mail:
                self.send_mail(subject, text)

        if self.options.updated_item:
            self.log.info('Updated Item Mail')
            self.log.info('App Models:%s' % self.app_models)
            crawlrun_model      = getattr(self.app_models,'CrawlRun',None)
            source_model        = getattr(self.app_models,'Source',None)
            site_name           = os.environ.get('SITE', None)
            site_app_name       = os.environ.get('SCRAPY_PROJECT', None)
            if not crawlrun_model:
                raise Exception('%s does not have %s model' % (self.app_models, crawlrun_model))

            items_updated       = OrderedDict()
            crawl_run_name      = self.options.crawl_name.split(',')
            time_threshold      = timezone.now() - datetime.timedelta(hours=int(self.options.time))
            crawlrun_objects    = crawlrun_model.objects.filter(
                updated_at__gte=time_threshold,
                name__in=crawl_run_name)

            STATUS_LIST_DICT = {
                '0':'Pending',
                '1':'Success',
                '2':'Failure',
                '3':'FalsePositive'
            }
            for crawlrun_object in crawlrun_objects:
                total_items = 0
                source_name = source_model.objects.get(id=crawlrun_object.source_id).name
                items_updated[source_name] = OrderedDict()
                crawlrun_log_object     = getattr(crawlrun_object, self.options.crawlrun_log_name)
                crawl_status_list       = crawlrun_log_object.values('status').order_by('status').annotate(count=Count('status'))
                item_status_dict        = {}
                item_updated_dict       = items_updated[source_name]
                pending_failure_count   = 0
                for crawl_status in crawl_status_list:
                    each_crawl_item_count = crawl_status.get('count', 0)
                    total_items     += each_crawl_item_count
                    item_status     = STATUS_LIST_DICT.get(crawl_status.get('status')).strip()
                    if item_status in ['Failure','Pending']:
                        pending_failure_count   += each_crawl_item_count
                    item_status_dict[item_status]   = each_crawl_item_count

                item_updated_dict['status']         = item_status_dict
                item_updated_dict['total_items']    = total_items
                try:
                    outdated_percentage = int((pending_failure_count/total_items)*100)
                except:
                    outdated_percentage = 0
                item_updated_dict['outdated_percentage']=outdated_percentage

            self.log.info('Item Updated w.r.s:%s' % items_updated)
            text = '<br /><br /><b>Items updated in last %s hrs crawl_runs %s.</b><br /><br /><table border="1" \
                    style="border-collapse:collapse;" cellpadding="6px" cellspacing="8px"><tr>'%(self.options.time,datetime.datetime.strftime(datetime.datetime.now(), "%b %d, %Y"))
            headers = [
                'Source',
                'TotalCount',
                'Status',
                'OutDatedKeys(%)'
            ]
            for header in headers:
                text += '<th>%s</th>' % header
            text += '</tr>'

            is_sent_mail = False
            for key, val in items_updated.items():
                outdated_percentage = val.pop('outdated_percentage',0)
                if outdated_percentage >= 10:
                    color='Red'
                elif outdated_percentage >= 5:
                    color='Orange'
                else:
                    color=''
                text    += '<tr bgcolor="%s">'%color
                text    += '<td>%s</td>' % (key)
                text    += '<td>%s</td>' % (val.pop('total_items', 0))
                text    += '<td>%s</td>' % (val.pop('status', {}))
                text    += '<td>%s</td>' % (outdated_percentage)
                text    += '</tr>'
                is_sent_mail = True

            subject_outline = self.get_subject_outline()
            if site_name or site_app_name:
                subject = '{}:{} {} Items Updated within {} hours on {}'.format(
                    site_name,
                    site_app_name,
                    subject_outline,
                    self.options.time,
                    datetime.datetime.strftime(
                        datetime.datetime.now(), "%b %d, %Y"))
            else:
                host_name = socket.gethostname()
                subject = '{} {} Items Updated within {} hours on {}'.format(
                    host_name,
                    subject_outline,
                    self.options.time,
                    datetime.datetime.strftime(
                        datetime.datetime.now(), "%b %d, %Y"))

            if is_sent_mail:
                self.send_mail(subject, text)

        if self.options.disk_space:
            disk_free = subprocess.Popen(["df","-h"], stdout=subprocess.PIPE)
            host_name = socket.gethostname()
            alert_subject = None
            text = '''<html>
                        <body>
                            /<br/> : Hi Team, <br /> <br />
                            Please check the disk space in {} <br />
                            <b> THRESHOLD: {}
                        </body>
                    </html>'''
            for line in disk_free.stdout:
                disk_partition = line.decode().split()
                try:
                    if disk_partition[5]==self.options.disk_partition:
                        disk_threshold = int(disk_partition[4][:-1])
                        if (disk_threshold > self.options.min_threshold) and (disk_threshold < self.options.max_threshold):
                            alert_subject = "LOW: disk space warning @ {}"
                        elif disk_threshold >= self.options.min_threshold:
                                alert_subject = "HIGH: Machine Health is not good @ {}, Don't have enough space"
                        if alert_subject:
                            self.send_mail(alert_subject.format(host_name), text.format(host_name, disk_threshold))
                except Exception as mail_err:
                    self.send_mail("Failed to send the mail", str(mail_err))
            if not alert_subject:
                self.log.info("Machine Health is Good")

        if self.options.db_server_status:
            try:
                c = connections['default'].cursor()
            except OperationalError:
                subject = 'mysql server gone away'
                conn_dict = connections['default'].settings_dict
                conn_dict['PASSWORD'] = '*********'
                self.log.error('Mysql Server Error %s'%(str(conn_dict)))
                self.send_mail(subject, str(conn_dict))
            else:
                self.log.info("MySql Server is Good")


        if self.options.process_name and self.options.process_time:
            t2 = DT.datetime(1900,1,1)
            cmd = "ps -eo etime,cmd | grep '%s'"%(self.options.process_name)
            f = os.popen(cmd)
            for line in f.read().split('\n'):
                crawl_time = None
                formates = ['%H:%M:%S', '%d-%H:%M:%S', '%M:%S']
                for p in formates:
                    try:
                        rp = '\d\d-\d\d:\d\d:\d\d|\d-\d\d:\d\d:\d\d|\d:\d\d:\d\d:\d\d|\d\d:\d\d:\d\d|\d\d:\d\d'
                        ti = ''.join(re.findall(rp, line))
                        crawl_time = (DT.datetime.strptime(ti, p) - t2).total_seconds() / 60
                        break
                    except ValueError:
                        pass

                if crawl_time:
                    self.log.info(" Crawled Time is {}".format(crawl_time))
                    if crawl_time > int(self.options.process_time):
                        subject = 'SLA:ALERT @ {} process tacking more time | expected time {} minutes'.format(
                            self.options.process_name.replace('.lock', ''),
                            self.options.process_time
                        )
                        self.log.info(subject + '\n\n' + line)
                        self.send_mail(subject=subject, text=line)
                        break

    def close(self):
        close_logger(self.log)

    def get_subject_outline(self):
        return "@ " + self.options.alert_mail_sub_name if self.options.alert_mail_sub_name else "@"

    def send_mail(self, subject, text):
        msgRoot = MIMEMultipart('mixed')
        msgRoot['Subject'] = subject
        msgRoot.preamble = 'This is a multi-part message in MIME format.'
        msgAlternative = MIMEMultipart('alternative')
        msgRoot.attach(msgAlternative)

        msgText = MIMEText(text, 'html', _charset='UTF-8')
        msgAlternative.attach(msgText)

        smtp = smtplib.SMTP("smtp.gmail.com", 587)
        try:
            from_ = os.environ.get('noreply_email','')
            to_ = os.environ.get('mail_to','')
            cc_ = os.environ.get('mail_cc','')
            if not (from_ or to_ or cc_):
                self.log.info("Please provide the valid cc and to mail-address")
                return
            self.log.info('Sending mail to %s from %s and cc %s'%(to_,from_,cc_))
            msgRoot['From']=from_
            msgRoot['To']=to_
            msgRoot['Cc']=cc_
            smtp.ehlo()
            smtp.starttls()
            username = from_
            password = os.environ.get('noreply_password','')
            smtp.login(username,password)
            smtp.sendmail(msgRoot['From'],msgRoot['To'].split(',')+msgRoot['Cc'].split(','),msgRoot.as_string())
            smtp.quit()
            self.log.info("Mail Sent Successfully from %s to %s"%(from_,to_))
        except Exception as e:
            self.log.info("unabel to send mail from_ %s to %s cc %s"%(from_,to_,cc_))
            print(e)


if __name__ == '__main__':
    standalone_main(ItemStatus)

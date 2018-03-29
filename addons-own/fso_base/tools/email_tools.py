# -*- coding: utf-'8' "-*-"
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.addons.fso_base.tools.server_tools import is_production_server

from datetime import datetime as dt
from dateutil import tz
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
logger = logging.getLogger(__name__)


def send_internal_email(odoo_env_obj=None, fromaddr='', toaddr='', subject='', body=''):

    if not is_production_server():
        subject = "[IGNORE-THIS-DEV-MSG]: %s" % subject

    # Try to get instance information from self whereas self is expected to be the odoo instance
    if odoo_env_obj is not None:
        try:
            dbname = "%s" % odoo_env_obj.cr.dbname
            user = "%s" % odoo_env_obj.user.name
            now = dt.now(tz=tz.gettz('Europe/Vienna'))
            nowstr = now.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

            fromaddr = "fson-%s@datadialog.net" % dbname if not fromaddr else fromaddr
            toaddr = "admin@datadialog.net" if not toaddr else toaddr
            subject = "FSON[%s](%s) %s: %s" % (dbname, nowstr, user, subject)
            body = subject if not body else body
        except Exception as e:
            logger.warning("send_internal_email() could not get instance info!\n%s" % repr(e))

    try:
        # Prepare e-mail
        msg = MIMEMultipart()
        msg['From'] = fromaddr
        msg['To'] = toaddr
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Send e-mail
        server = smtplib.SMTP('192.168.37.1', 25)
        # server.starttls()
        # server.login(fromaddr, "YOUR PASSWORD")
        text = msg.as_string()
        server.sendmail(fromaddr, toaddr, text)
        server.quit()

    except Exception as e:
        try:
            logger.error("Could not send status e-mail!\n---\n%s\n---\n%s" % (text, repr(e)))
        except:
            logger.error("Could not send status e-mail! %s" % subject)

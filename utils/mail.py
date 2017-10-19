#-*-coding:utf-8-*-

import smtplib
from email.mime.text import MIMEText
import sys, socket

def send_mail(sub, content, to_list):
    mail_host = 'smtp.163.com'
    mail_user = 'm15000406743@163.com'
    mail_pass = 'zx1314520'
    msg = MIMEText(content, _subtype='plain', _charset='utf-8')
    me = "bug" + "<"+mail_user+">"
    msg['Subject'] = socket.gethostbyname(socket.gethostname())+": " +sub
    msg['From'] = me
    msg['To'] = ';'.join(to_list)
    try:
        server = smtplib.SMTP()
        server.connect(mail_host)
        server.login(mail_user, mail_pass)
        server.sendmail(me, to_list, msg.as_string())
        server.close()
        return True
    except Exception as e:
        print(str(e))
        return False

if __name__ == '__main__':
    print(send_mail(u'WO', u'LOVE', ['1195615991@qq.com']))

import argparse
import json
import requests
from getpass import getpass
from urllib3.exceptions import InsecureRequestWarning
import time

import smtplib
import os.path as op
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email import encoders


requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
    
def getAuditlog(cvpServer, session_id, session_token):
    update_resp = requests.get(
        'https://%s/cvp-ipam-api/auditlog?session_id=%s&token=%s'% (cvpServer, session_id, session_token),verify=False)
    return update_resp.json()["data"]

def send_mail(send_from, send_to, subject, message, files,
          server, port, username, password, use_tls):

    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach(MIMEText(message))

    for path in files:
        part = MIMEBase('application', "octet-stream")
        with open(path, 'rb') as file:
            part.set_payload(file.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition',
                        'attachment; filename="{}"'.format(op.basename(path)))
        msg.attach(part)

    smtp = smtplib.SMTP(server, port)
    if use_tls:
        smtp.starttls()
    smtp.login(username, password)
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.quit()

def main():
    d1 = time.strftime("%Y_%m_%d_%H_%M_%S", time.gmtime())
    d2 = time.strftime("%Y %m %d  %H:%M:%S", time.gmtime())
    parser = argparse.ArgumentParser()
    parser.add_argument('--username', required=True)
    parser.add_argument('--cvpServer', required=True)

    args = parser.parse_args()
    username = args.username
    password = getpass()
    cvpServer=args.cvpServer


    print ('Start Login')
    login_data = {'username': username, 'password': password}
    login_resp = requests.post('https://%s/cvp-ipam-api/login' % cvpServer,
                               data=json.dumps(login_data), verify=False)
    print ('Login Info')
    login_json = login_resp.json()
    print ('\n')

    session_id = login_json['session_id']
    session_token = login_json['token']
    
    auditLog = getAuditlog(cvpServer, session_id, session_token)
    
    filename= "IPAM_Audit_logs_" + d1 + ".txt"
    with open(filename,'w', encoding='utf-8') as file:
        json.dump(auditLog,file, ensure_ascii=False, indent=4)
    
    send_from = "sender@domain.com"
    send_to = ["receiver@domain.com"]
    subject = "IPAM Audit Log " + d2
    files = [filename]
    message = ""
    server = "smtp.domain.com"
    username = "username"
    password = "password"
    port =587
    use_tls = True
    send_mail(send_from, send_to, subject, message, files, server, port, username, password, use_tls )
    
    print ('\n')
    print ('Start Logout')
    logout_data = {'session_id': session_id, 'token': session_token}
    logout_resp = requests.post('https://%s/cvp-ipam-api/logout' % cvpServer,
                                data=json.dumps(logout_data), verify=False)
    print ('Logout Info')
    logout_json = logout_resp.json()
    print (logout_json)

if __name__ == '__main__':
    main()


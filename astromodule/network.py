import mimetypes
import smtplib
from email import encoders
from email.message import EmailMessage, MIMEPart
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from pathlib import Path
from typing import List


def send_email(
  sender: str, 
  recipients: List[str],
  username: str, 
  password: str, 
  message: str, 
  subject: str = '', 
  files: List[str] = [],
  use_tls: bool = True,
):
  msg = MIMEMultipart()
  msg['From'] = sender
  msg['To'] = COMMASPACE.join(recipients)
  msg['Date'] = formatdate(localtime=True)
  msg['Subject'] = subject
  msg.attach(MIMEText(message))
  
  for path in files:
    part = MIMEBase('application', 'octet-stream')
    with open(path, 'rb') as file:
      part.set_payload(file.read())
    encoders.encode_base64(part)
    part.add_header(
      'Content-Disposition',
      f'attachment; filename={Path(path).name}'
    )
    msg.attach(part)

  smtp = smtplib.SMTP('smtp.office365.com', 587)
  if use_tls:
    smtp.starttls()
  smtp.login(username, password)
  smtp.sendmail(sender, recipients, msg.as_string())
  smtp.quit()



def send_email2(
  sender: str, 
  recipients: List[str],
  username: str, 
  password: str, 
  message: str, 
  subject: str = '', 
  files: List[str] = [],
  use_tls: bool = True,
):
  msg = EmailMessage()
  msg['From'] = sender
  msg['To'] = COMMASPACE.join(recipients)
  msg['Date'] = formatdate(localtime=True)
  msg['Subject'] = subject
  msg.set_content(message)
  
  for path in files:
    with open(path, 'rb') as fp:
      file_data = fp.read()
      maintype, _, subtype = (mimetypes.guess_type(path)[0] or 'application/octet-stream').partition("/")
      msg.add_attachment(file_data, maintype=maintype, subtype=subtype, filename=path)

  smtp = smtplib.SMTP('smtp.office365.com', 587)
  if use_tls:
    smtp.starttls()
  smtp.login(username, password)
  smtp.sendmail(sender, recipients, msg.as_string())
  smtp.quit()



  
if __name__ == '__main__':
  send_email2(
    'natanael_magalhaes@msn.com', 
    ['palmiliaxonga@gmail.com'], 
    'natanael_magalhaes@msn.com', 
    'fat=fat*n;', 
    'Relatório Final', 
    'Relatório Final',
    files=['/home/natan/repos/splus-radial-search/output_heasarc/heasarc_top200.pdf']
  )
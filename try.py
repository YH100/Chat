import smtplib
def sendrestartpassmail(mailadd):
    content = "exemple"
    mail = smtplib.SMTP('smtp.gmail.com',587)
    mail.ehlo()
    mail.starttls()
    mail.login("yhserverproject2018@gmail.com","yhserver2018")
    mail.sendmail('yhserverproject2018@gmail.com',mailadd,content)
    mail.close()

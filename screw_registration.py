from socket import *
from time import sleep

post_str ='''POST /v099/app HTTP/1.1\r\nHost: auth.lessnetworks.com\r\nConnection: keep-alive\r\nUser-Agent: Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.5 (KHTML, like Gecko) Chrome/4.1.249.1045 Safari/532.5\r\nReferer: http://auth.lessnetworks.com/v099/app?service=page/Resend\r\nContent-Length: 108\r\nCache-Control: max-age=0\r\nOrigin: http://auth.lessnetworks.com\r\nContent-Type: application/x-www-form-urlencoded\r\nAccept: application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5\r\nAccept-Encoding: gzip,deflate,sdch\r\nAccept-Language: en-US,en;q=0.8\r\nAccept-Charset: ISO-8859-1,utf-8;q=0.7,*;q=0.3\r\nCookie: com.lessnet.co.ui.pages.Login.username=johnsjohns; JSESSIONID=9B8F3BF85A82F518E02522ED3EC06DD4; __utmz=231581954.1271282793.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); THELARRYCOOKIE=375495; __utma=231581954.1664321371.1271282793.1271282793.1271282793.1; __utmc=231581954; __utmb=231581954.20.10.1271282793\r\n\r\nservice=direct%2F1%2FResend%2FforgotForm&sp=S0&Form0=inputEmail&inputEmail=john%40johnsjohn.co&Submit=Submit'''

print post_str

s = socket()
s.connect(("auth.lessnetworks.com",80))

while True:
	s.send(post_str)
	print s.recv(4096)
	sleep(590)

# -*- coding: utf-8 -*-

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
from time import sleep, time
import csv
import hashlib
from datetime import datetime 
from smtplib import SMTP
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from ConfigParser import SafeConfigParser



user = "dchestnov@mail.ru"
password = "Merlin75"
basket_url = "https://lk.wildberries.ru/basket"
url = "https://security.wildberries.ru/login?returnUrl=https://lk.wildberries.ru/basket"
uE = '//*[@id="Item_Login"]'
pE = '//*[@id="Item_Password"]'
bE = '/html/body/div[1]/div/div[2]/div/div/form/div[2]/button'
fN = 'items.csv'

CFG = SafeConfigParser()
config = 'user.conf'


def login():
	driver = webdriver.Firefox()
	wait = WebDriverWait(driver, 10)
	driver.maximize_window()
	driver.get(url)
	driver.find_element_by_xpath(uE).send_keys(user)
	driver.find_element_by_xpath(pE).send_keys(password)
	driver.find_element_by_xpath(bE).click()
	sleep(3)
	return driver


def send_mail(msg_txt="\nItem price was changed!!!\n"):
	CFG.read(config)
	eUser = CFG.get('email', 'user')
	ePassword = CFG.get('email', 'password')
	sender = CFG.get('email', 'sender')
	subject = CFG.get('email', 'subject')
	recipient = CFG.get('email', 'recipients')
	msg = MIMEMultipart()
	msg['From'] = sender
	msg['To'] = recipient
	msg['Subject'] = subject
	msg.attach(MIMEText(msg_txt.encode('utf-8'),'plain'))
	try:
		server = SMTP('smtp.gmail.com:587')
		server.starttls()
		server.login(eUser, ePassword)
		server.sendmail(sender, recipient, msg.as_string())
		print '[+] Email successfully sent'
	except:
		print "[-] Error sending email"
	finally:
		server.quit()


def main():
	rez = []
	drv = login()
	html = drv.page_source
	soup = BeautifulSoup(html, "html.parser")
	order_list = soup.find('tbody', {'class': 'basket-list-body'})
	items = order_list.find_all('tr', {'class': 'outerRow'})
	#print order_list.prettify()
	item_id = 0
	for item in items:
		d = dict()
		d['title'] = item.find('a', {'class': 'j-product-popup image-link'}).get('title').strip()
		d['salesPrice'] = item.find('td',{'class': 'basketTableSum'}).text.strip()
		d['discount'] = item.find('span', {'class': 'sale'}).text.strip()
		d['initialPrice'] = item.find('del', {'class': 'price-wo-sale'}).text.strip()
		d['id'] = get_id(d['title'])
		rez.append(d)
	return rez


def get_id(item):
	m = hashlib.md5()
	m.update(item.encode('cp1251'))
	return str(int(m.hexdigest(),16))[0:8]


def write_file(item):
	#time = datetime.strftime(datetime.now(), "%d/%m %H:%M")
	with open(fN,'ab') as f:
		writer = csv.writer(f, delimiter=';')
		writer.writerow([item['id'], time(), item['initialPrice'], item['discount'], item['salesPrice']])


def read_file():
	with open(fN, 'r') as f:
		reader = csv.reader(f, delimiter=';')
		d = dict()
		for row in reader:
			item_id = str(row[0])
			if item_id in d:
				d[item_id].append(float(row[4]))
			else:
				d[item_id] = [float(row[4])]
	return d


def get_min_price(item_id):
	d = read_file()
	l = d[item_id]
	return min(l)


if __name__ == '__main__':
	basket = main()
	for item in basket:
		write_file(item)
	iid = '32719242'
	print get_min_price(iid)





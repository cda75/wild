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
from os.path import exists
import pandas as pd



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
	CFG.read(config)
	user = CFG.get('wild', 'user')
	password = CFG.get('wild', 'password')
	#driver.maximize_window()
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
	for item in items:
		d = dict()
		d['title'] = item.find('a', {'class': 'j-product-popup image-link'}).get('title').strip()
		d['salesPrice'] = float(item.find('td',{'class': 'basketTableSum'}).text.strip().replace(' ',''))
		if item.find('span', {'class': 'sale'}):
			d['discount'] = float(item.find('span', {'class': 'sale'}).text.strip().replace('%','').replace('-',''))
		else:
			d['discount'] = 0
		if item.find('del', {'class': 'price-wo-sale'}):
			d['initialPrice'] = float(item.find('del', {'class': 'price-wo-sale'}).text.strip().replace(' ',''))
		else:
			d['initialPrice'] = d['salesPrice']
		d['id'] = get_id(d['title'])
		rez.append(d)
	drv.close()
	return rez


def get_id(item):
	m = hashlib.md5()
	m.update(item.encode('cp1251'))
	return str(int(m.hexdigest(),16))[0:8]


def write_file(item):
	#time = datetime.strftime(datetime.now(), "%d/%m %H:%M")	
	if not exists(fN):
		with open(fN,'wb') as f:
			writer = csv.writer(f)
			headers = ['id', 'time', 'initialPrice', 'discount', 'salesPrice']
			writer.writerow(headers)
	with open(fN,'ab') as f:
		writer = csv.writer(f)
		writer.writerow([item['id'], time(), item['initialPrice'], item['discount'], item['salesPrice']])


def get_min_price(item_id):
	df = pd.read_csv(fN)
	df_new = df.loc[df['id'] == long(item_id)]
	return float(df_new['salesPrice'].min())


def get_max_discount(item_id):
	df = pd.read_csv(fN)
	df_new = df.loc[df['id'] == long(item_id)]
	return float(df_new['discount'].max())




if __name__ == '__main__':
	basket = main()
	if not exists(fN):
		for item in basket:
			write_file(item)
	for item in basket:
		item_min_price = get_min_price(item['id'])
		if item['salesPrice'] < item_min_price:
			write_file(item)
			msg_txt = '%s has new minimum price: %s' %(item['title'], item['salesPrice'] )
			send_mail(msg_txt)
			print msg_txt


	
	








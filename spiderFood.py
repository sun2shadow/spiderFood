import re

from selenium import  webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyquery import PyQuery as pq
from config import *
import pymongo

client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]

driver = webdriver.Chrome()
wait = WebDriverWait(driver, 20)

#启动浏览器，输入搜索关键字
def search():
    try:

        driver.get('https://www.taobao.com')

        input = wait.until(
            EC.presence_of_element_located((By.ID, 'mq'))
        )

        submit = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#J_PopSearch > div.sb-search > div > form > input[type="submit"]:nth-child(2)'))
        )

        input.send_keys('美食')
        submit.submit()

        total = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.total')))
        get_products()
        return total.text
    except TimeoutException:
        return search()

#跳转到下一页
def next_page(page_number):
    try:
        number_input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#mainsrp-pager > div > div > div > div.form > input"))
        )
        drump_submit = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit"))
        )
        number_input.clear()
        number_input.send_keys(page_number)
        drump_submit.click()
        show_page = wait.until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, "#mainsrp-pager > div > div > div > ul > li.item.active > span"), str(page_number))
        )
        get_products()
    except TimeoutException:
        next_page(page_number)

#获取产品类容
def get_products():
    wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#mainsrp-itemlist .items .item"))
    )
    html = driver.page_source
    doc = pq(html)
    items = doc('#mainsrp-itemlist .items .item').items()
    for item in items:
        product = {
            'image':item.find('.pic .img').attr['src'],
            'price':item.find('.price').text(),
            'deal':item.find('.deal-cnt').text()[:-3],
            'title':item.find('.title').text(),
            'shop':item.find('.shop').text(),
            'location':item.find('.location').text()
        }
        print(product)
        save_to_mongo(product)

#保存到mongo中
def save_to_mongo(product):
    try:
        if db[MONGO_TABLE].insert(product):
            print("保存商品成功",product)
    except Exception:
        print('保存商品失败', product)

def main():
    total = search()
    total = int(re.compile('(\d+)').search(total).group(1))
    for i in range(2, total + 1):
        next_page(i)
    driver.close()
    
if __name__ == '__main__':
    main()

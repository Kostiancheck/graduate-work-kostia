import json
import re
import bs4
import requests
import csv
from datetime import datetime

import config
import time


# TODO перевести всё на укр добавив в ЮРЛ /uk/
class OlxParser:
    f = open(config.FILENAME, 'w')
    writer = csv.DictWriter(f, lineterminator='\n', fieldnames=config.FILDNAMES)

    def get_html(self, url):
        r = requests.get(url)
        return r.text if re.search(config.URL, r.url) else None

    def get_htmlv2(self, url):
        r = requests.get(url)
        return r.text if re.search('https://www.olx.ua/', r.url) else None

    def get_data(self, html):
        soup = bs4.BeautifulSoup(html, 'lxml')
        trs = soup.find('table', id='offers_table').findAll('tr', class_='wrap')

        for tr in trs:
            try:
                price = tr.find('p', class_='price').find('strong').text
            except AttributeError:
                price = 'Не указано'

            delivery = tr.find('div', class_='delivery-badge')
            top_post = tr.find('td', class_="offer promoted ")

            href = tr.find('a').get('href')

            data = {
                'href': href,
                'name': self.clean_name(tr.find('strong').text),
                'date': self.clean_date(tr.find('td', valign="bottom").findAll('span')[1].text.strip()),
                'place': tr.find('td', valign="bottom").findAll('span')[0].text.strip(),
                'cathegory': tr.find('small', class_='breadcrumb x-normal').text.strip(),
                'price': self.clean_price(price),
                'olxdelivery': True if delivery else False,
                'is_promoted': True if top_post else False
            }

            additional_data = self.get_more_product_data(href)

            self.write_data(dict(data, **additional_data))

    def get_more_product_data(self, product_url) -> dict:
        html = self.get_htmlv2(f'{product_url}')
        soup = bs4.BeautifulSoup(html, 'lxml')

        author_from = soup.body.find('div', text=re.compile('на OLX с'))
        # TODO format to the standart date and calculate now - this date to see how long the auth on OLX
        author_from_data = re.search("на OLX с (.*)</div>", str(author_from)).group(1)

        # doest work because it's dynamic data
        # auth_rating = soup.body.find('div', attrs={"data-testid": "listing-seller-rating-sentiment"}) \
        #     .findAll('span')[0].text.strip().replace(':', '')

        views = 0
        # views = soup.find(text=re.compile('Просмотров:'))
        # print(str(views))
        # # print(f'views: {views}')
        # views = re.search('Просмотров: (\\d*)', str(views)).group(1)
        # print(f'views: {views}')

        # TODO check how it works when there is no photo
        photos = soup.find('div', class_='swiper-wrapper').findChildren("div", recursive=False)
        photos_number = len(photos)

        data = {
            'author_from_data': author_from_data if author_from_data else None,
            'views': views if views else None,
            'photos_number': photos_number if photos_number else None
        }
        # print(f'Product info {data}')
        return data

    def clean_price(self, price):
        if price == 'Не указано' or price == 'Обмен':
            return price
        else:
            result = re.search('(.*) грн.', price).group(1)
            return result.replace(' ', '')

    def clean_date(self, publications_date):
        res = re.search('(.*) \\d{2}:\\d{2}', publications_date)

        if res and res.group(1) == 'Сегодня':
            date = f'{datetime.today().day} {config.PARAMS[datetime.today().month]}'
            return date
        elif res and res.group(1) == 'Вчера':
            date = f'{datetime.today().day - 1} {config.PARAMS[datetime.today().month]}'
            return date
        else:
            return publications_date

    def clean_name(self, name):
        return name.replace(',', ' ').replace(';', ' ')

    def write_data(self, data):
        print(f'Final data: {data}')
        self.writer.writerow(data)

    def write_head(self):
        self.write_data({
            'href': 'URL',
            'name': 'НАЗВАНИЕ',
            'cathegory': 'КАТЕГОРИЯ',
            'price': 'ЦЕНА',
            'place': 'ГОРОД',
            'date': 'ДАТА',
            'olxdelivery': 'ДОСТАВКА',
            'is_promoted': 'Рекламний пост?',
            'author_from_data': 'Автор на ОЛХ з',
            'views': 'Переглядів',
            'photos_number': 'Кількість фото'
        })

    def main(self):
        self.write_head()
        url = config.URL
        page = 1
        start_time = datetime.now()
        print(f"Start time: {start_time}")

        while True:

            try:
                html = self.get_html(f'{url}?page={page}')
                if html:
                    self.get_data(html)
                    page += 1
                else:
                    break

            except AttributeError:
                time.sleep(1)
                html = self.get_html(url)
                if html:
                    self.get_data(html)
                    page += 1
                else:
                    break
            finally:
                end_time = datetime.now()
                print(f"End time: {end_time}")
                print(f"Work time: {end_time - start_time}")
                self.f.close()




if __name__ == '__main__':
    parser = OlxParser()
    parser.main()

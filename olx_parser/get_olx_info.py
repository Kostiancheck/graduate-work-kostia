import re
import bs4
import requests
import csv
from datetime import datetime, timedelta
from selenium import webdriver

import config
import time


# TODO перевести всё на укр добавив в УРЛ /uk/
class OlxParser:
    f = open(config.FILENAME, 'a')  # file opened in append mode
    writer = csv.DictWriter(f, lineterminator='\n', fieldnames=config.FILDNAMES)
    driver = webdriver.Firefox(executable_path='../drivers/geckodriver')
    time_to_sleep_for_page_downloading = 1  # seconds

    def get_html(self, url):
        r = requests.get(url)
        return r.text

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
            delivery_2 = tr.find('span', class_='delivery-badge')
            delivery = delivery if delivery else delivery_2

            href = tr.find('a').get('href')
            try:
                top_post = re.search(r'^.*;(promoted)$', href).group(1)
            except AttributeError:
                top_post = None

            data = {
                'href': href,
                'name': self.clean_name(tr.find('strong').text),
                'date': self.clean_date(tr.find('td', valign="bottom").findAll('span')[1].text.strip()),
                'place': tr.find('td', valign="bottom").findAll('span')[0].text.strip(),
                'category': tr.find('small', class_='breadcrumb x-normal').text.strip(),
                'price': self.clean_price(price),
                'olxdelivery': True if delivery else False,
                'is_promoted': True if top_post else False
            }

            try:
                additional_data = self.get_more_product_data(href)
            except Exception as e:
                print(f"problem here: {href}\nerror: {e}")
                continue  # don't write this data to the dataset
            self.write_data(dict({'created_time': datetime.now()}, **data, **additional_data))

    def get_more_product_data(self, product_url) -> dict:
        html = self.get_htmlv2(f'{product_url}')
        soup = bs4.BeautifulSoup(html, 'lxml')

        self.driver.get(product_url)
        time.sleep(self.time_to_sleep_for_page_downloading)
        html_2 = self.driver.page_source
        soup_2 = bs4.BeautifulSoup(html_2, 'lxml')

        author_from = soup_2.body.find('div', text=re.compile('на OLX с'))
        # TODO format to the standart date and calculate now - this date to see how long the auth on OLX
        author_from_data = re.search("на OLX с (.*)</div>", str(author_from)).group(1)

        try:
            auth_rating = soup_2.body.find('div', attrs={"data-testid": "listing-seller-rating-sentiment"}) \
                .findAll('span')[0].text.strip().replace(':', '')
        except AttributeError:
            auth_rating = "нет ни одного отзыва"

        views = soup_2.find(text=re.compile('Просмотров:'))

        try:
            views = re.search('Просмотров: (\\d*)', str(views)).group(1)
        except AttributeError:
            views = "нет просмотров"

        # TODO check how it works when there is no photo
        try:
            photos = soup.find('div', class_='swiper-wrapper').findChildren("div", recursive=False)
            photos_number = len(photos)
        except AttributeError:
            photos_number = 0

        try:
            description = soup_2.body.find('div', attrs={"data-cy": "ad_description"}) \
                .findChildren('div', recursive=False)[0].text.strip()
        except AttributeError:
            description = 'N/A'

        data = {
            'author_from_data': author_from_data if author_from_data else None,
            'views': views if views else None,
            'auth_rating': auth_rating,
            'photos_number': photos_number if photos_number else None,
            'description': description
        }

        return data

    def clean_price(self, price):
        if price == 'Не указано' or price == 'Обмен':
            return price
        else:
            result = re.search('(.*) грн.', price).group(1)
            return result.replace(' ', '')

    def clean_date(self, publications_date):
        res = re.search('(.*) (\\d{2}):(\\d{2})', publications_date)
        if res and res.group(1) == 'Сегодня':
            date = datetime.today()
            hour = int(res.group(2))
            minute = int(res.group(3))
            return date.replace(hour=hour, minute=minute)

        elif res and res.group(1) == 'Вчера':
            date = datetime.today() - timedelta(days=1)
            hour = int(res.group(2))
            minute = int(res.group(3))
            return date.replace(hour=hour, minute=minute)
        else:
            return publications_date

    def clean_name(self, name):
        return name.replace(',', ' ').replace(';', ' ')

    def write_data(self, data):
        print(f'Final data: {data}')
        self.writer.writerow(data)

    def write_head(self):
        self.write_data({
            'created_time': 'Created_time',
            'href': 'URL',
            'name': 'Name',
            'category': 'Category',
            'price': 'Price',
            'place': 'Address',
            'date': 'Date',
            'olxdelivery': 'OlxDelivery',
            'is_promoted': 'Is_promoted',
            'author_from_data': 'Author_from_data',
            'views': 'Views',
            'auth_rating': 'Auth_rating',
            'photos_number': 'Photos_number',
            'description': 'Description'
        })

    def main(self):
        self.write_head()
        urls = config.URLs
        start_time = datetime.now()
        print(f"Start time: {start_time}")

        for url in urls:
            page = 1
            error = "No error"
            tries = 1
            while True:

                try:
                    html = self.get_html(f'{url}?page={page}')
                    if html:
                        self.get_data(html)
                        page += 1
                    else:
                        if tries < 10:
                            print(f"Try {tries} \n URL: {url}?page={page} HTML: {html}")
                            tries += 1
                            continue
                        else:
                            break

                except AttributeError as e:
                    error = e
                    time.sleep(self.time_to_sleep_for_page_downloading)
                    html = self.get_html(url)
                    if html:
                        self.get_data(html)
                        page += 1
                    else:
                        if tries < 10:
                            print(f"Try {tries} \n URL: {url}?page={page} HTML: {html}")
                            tries += 1
                            continue
                        else:
                            break
                finally:
                    end_time = datetime.now()
                    print(f"End time: {end_time} \n Tries: {tries} Error: {error}")
                    # print(f"Work time: {end_time - start_time}")

        self.f.close()
        end_time = datetime.now()
        print(f"Final end time: {end_time}")
        print(f"Work time: {end_time - start_time}")


if __name__ == '__main__':
    parser = OlxParser()
    parser.main()

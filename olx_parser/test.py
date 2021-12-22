from datetime import datetime, timedelta, date
import re

test_dates = [
    'Сегодня 17:01',
    'Сегодня 16:58',
    'Сегодня 16:57',
    'Вчера 16:55',
    'Вчера 16:55',
    'Вчера 16:55',
    'Вчера 16:53'
]


def clean_date(publications_date):
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


#
# for test_date in test_dates:
#     print(clean_date(test_date))
MONTHS = {
    'январь': 1,
    'февраль': 2,
    'март': 3,
    'апрель': 4,
    'май': 5,
    'июнь': 6,
    'июль': 7,
    'август': 8,
    'сентябрь': 9,
    'октябрь': 10,
    'ноябрь': 11,
    'декабрь': 12,
}


def clean_author_from_data(auth_date):
    split = auth_date.split()
    month = MONTHS[split[0]]
    year = split[1]
    return date(year=int(year), month=int(month), day=1)


dates = ["июнь 2016 г.",
         "октябрь 2019 г.",
         "июнь 2011 г.",
         "июль 2010 г.",
         "октябрь 2016 г.",
         "сентябрь 2021 г.",
         "сентябрь 2021 г.",
         "январь 2020 г.",
         "июль 2015 г.",
         "июль 2015 г.",
         "декабрь 2018 г.",
         "январь 2012 г.",
         ]
for d in dates:
    print(clean_author_from_data(d))
print(len('Apple iPhone XS Space Gray 64GB'))
from datetime import datetime

import requests
from bs4 import BeautifulSoup

import schedule


url = 'https://toytoystore.kz/product_list'
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36 RuxitSynthetic/1.0 v3975717906 t6703941201591042144 athfa3c3975 altpub cvcv=2 smf=0"
}


def get_data():
    req = requests.get(url=url, headers=headers)
    req.encoding = 'UTF8'
    src = req.text
    soup = BeautifulSoup(src, 'lxml')

    # Сбор всех ссылок на каталоги
    categories_li = soup.find('ul', class_='cs-product-groups-gallery').find_all('li', class_='cs-product-groups-gallery__item cs-online-edit')
    dict_categ = []
    for li in categories_li:
        a_url = f"https://toytoystore.kz{li.find('a', class_='cs-image-holder__image-link').get('href')}"
        dict_categ.append(a_url)

    # print(dict_categ)
    # print(len(dict_categ))

    # сбор карточек в каталогах
    dict_cards = [["Название", "Код товара", "Цена"]]
    sum_count = []
    k = 0
    for url1 in dict_categ:
        k += 1
        try:
            page = 1
            while True:
                # print(f'Страница {page}')
                req1 = requests.get(url=f'{url1}/page_{page}?product_items_per_page=48', headers=headers)
                req1.encoding = 'UTF8'
                src1 = req1.text
                soup1 = BeautifulSoup(src1, 'lxml')

                max_page = int(soup1.find('div', class_='b-pager').find('div').get('data-pagination-pages-count'))
                # print(max_page)

                all_cards = soup1.find('ul', class_='cs-product-gallery')\
                    .find_all('li', class_='cs-product-gallery__item cs-online-edit')

                count = 0
                for card in all_cards:
                    if len(card.find_all('span', class_='cs-goods-data__state cs-goods-data__state_val_clarify')) == 0:
                        count += 1
                        name_product = card.find('a', class_='cs-goods-title').text
                        price = card.find('span', class_='cs-goods-price__value cs-goods-price__value_type_current').text[:-3]

                        if len(card.find_all('span', class_='cs-goods-sku cs-product-gallery__sku')) == 1:
                            article_num = card.find('span', class_='cs-goods-sku cs-product-gallery__sku').text.strip()
                        else:
                            article_num = 'Код отсутствует'

                        # print(f'{name_product} - {price} - {article_num}')
                        dict_cards.append(
                            [
                                name_product,
                                article_num,
                                price
                            ]
                        )

                if page < max_page:
                    page += 1
                    sum_count.append(count)
                else:
                    break

        except Exception as ex:
            print(ex)
            print(url1)

        print(k)

    print(sum(sum_count))
    google_table(dict_cards=dict_cards)


def google_table(dict_cards):
    import os.path

    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from google.oauth2 import service_account

    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, 'credentials.json')

    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    # mail bot 'parsers@parsers-372008.iam.gserviceaccount.com'
    SAMPLE_SPREADSHEET_ID = '107SdHe8_dV6npe_dKE-7xA2QJgxz6ZOywOy-GZyrZX0'
    SAMPLE_RANGE_NAME = 'toytoystore.kz'

    try:
        service = build('sheets', 'v4', credentials=credentials).spreadsheets().values()

        # Чистим(удаляет) весь лист
        array_clear = {}
        clear_table = service.clear(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                    range=SAMPLE_RANGE_NAME,
                                    body=array_clear).execute()

        # добавляет информации
        array = {'values': dict_cards}
        response = service.append(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                  range=SAMPLE_RANGE_NAME,
                                  valueInputOption='USER_ENTERED',
                                  insertDataOption='OVERWRITE',
                                  body=array).execute()

    except HttpError as err:
        print(err)


def main():
    # start_time = datetime.now()

    schedule.every(55).minutes.do(get_data)

    while True:
        schedule.run_pending()

    # finish_time = datetime.now()
    # spent_time = finish_time - start_time
    # print(spent_time)


if __name__ == '__main__':
    main()

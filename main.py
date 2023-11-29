import requests
from fake_useragent import UserAgent
from datetime import datetime, timedelta
import csv
import os
import re
from bs4 import BeautifulSoup

api_url = "https://api.superjob.ru/2.0/"
api_headers = {
    "X-Api-App-Id": "your_client_secret",
}

headers = {
    'user_agent': UserAgent().random
}


def authenticate(login, password, client_id, client_secret):
    auth_data = {
        "login": login,
        "password": password,
        "client_id": client_id,
        "client_secret": client_secret,
    }

    response = requests.post(api_url + "oauth2/password/", data=auth_data, headers=api_headers)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print(f"Ошибка аутентификации: {response.text}")
        return None


def get_vacancy_info(access_token, vacancy_id):
    api_url = f"https://api.superjob.ru/2.0/vacancies/{vacancy_id}/"
    api_headers["Authorization"] = f"Bearer {access_token}"
    response = requests.get(api_url, headers=api_headers, timeout=60)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Ошибка получения информации о вакансии: {response.text}")
        return None


def get_vacancies(access_token, page, date_to, date_from):
    api_url = f"https://api.superjob.ru/2.0/vacancies/"
    current_datetime = datetime.now()

    date_pub_to = current_datetime - timedelta(days=date_to)
    date_pub_to_unix = int(date_pub_to.timestamp())
    if date_from == 0:
        date_pub_from_unix = 0
    else:
        date_pub_from = current_datetime - timedelta(days=date_from)
        date_pub_from_unix = int(date_pub_from.timestamp())
    params = {
        "page": page,
        "count": 500,
        "date_published_to": date_pub_to_unix,
        "date_published_from": date_pub_from_unix,
        "catalogues": 478,
    }
    api_headers["Authorization"] = f"Bearer {access_token}"
    response = requests.get(api_url, params=params, headers=api_headers, timeout=30)
    if response.status_code == 200:
        return response.json().get("objects", [])
    else:
        print(f"Ошибка получения списка вакансий: {response.text}")
        return None


login = "your_login"
password = "your_password"
client_id = "your_client_id"
client_secret = "your_client_secret"

access_token = authenticate(login, password, client_id, client_secret)

k = 1
is_vacancies_list_ended = False

visited_urls = set()

date_pub_to = 1
date_pub_from = 1

total_vacancies_quantity = 0

if access_token:
    print(f"Аутентификация прошла успешно. Access token: {access_token}")
    for i in range(1, 51):
        vacancies = []
        urls = []
        info_dict = {}
        url = f"https://russia.superjob.ru/vakansii/turizm-gostinicy-obschestvennoe-pitanie/?order_by%5Bupdated_at%5D=asc&page={i}"
        req = requests.get(url=url, headers=headers)
        src = req.content

        soup = BeautifulSoup(src, 'lxml')

        links = soup.select('div[class*="_2orsF _34A3E"]')

        a_tags = soup.find_all('a', href=True)
        pattern = re.compile(r'/vakansii/.+-\d+\.html')

        filtered_links = [a_tag['href'] for a_tag in a_tags if pattern.match(a_tag['href'])]

        for link in filtered_links:
            if link not in visited_urls:
                visited_urls.add(link)
                urls.append("https://russia.superjob.ru" + link)

                vacancy_id_match = re.search(r'(\d+).html$', f"https://russia.superjob.ru{link}")
                vacancy_id = vacancy_id_match.group(1)

                vacancy_info = get_vacancy_info(access_token, vacancy_id)

                if vacancy_info:
                    vacancy_url = f"https://russia.superjob.ru/{link}"
                    vacancy_date = datetime.utcfromtimestamp(vacancy_info['date_published'])
                    vacancy_name = vacancy_info['profession']
                    town = vacancy_info['town']['title']
                    firm_name = vacancy_info['firm_name']
                    vacancy_address = vacancy_info['address']
                    contact_phone = vacancy_info['phone']
                    contact_face = vacancy_info['contact']
                    if vacancy_address is None:
                        vacancy_address = "Не указан"
                    elif vacancy_address is None:
                        contact_phone = "Не указан"
                    elif contact_face is None:
                        contact_phone = "Не указано"

                    try:
                        vacancy_description = vacancy_info['description']
                    except (TypeError, KeyError):
                        try:
                            vacancy_description = f"{vacancy_info['candidat'][:100]}..."
                        except (TypeError, KeyError):
                            vacancy_description = "Не указано"

                    if not os.path.isfile('superjob.csv'):
                        with open('superjob.csv', 'w', newline='', encoding='utf-8') as csvfile:
                            header = ['Дата публикации', 'Вакансия', 'Описание', 'Город', 'Компания', 'Контактное лицо',
                                      'Телефон', 'Адрес', 'Ссылка']
                            writer = csv.writer(csvfile)
                            writer.writerow(header)

                    with open('superjob.csv', 'a', newline='', encoding='utf-8') as csvfile:
                        data = [vacancy_date, vacancy_name, vacancy_description, town, firm_name, contact_face,
                                contact_phone, vacancy_address, vacancy_url]
                        writer = csv.writer(csvfile)
                        writer.writerow(data)

                    total_vacancies_quantity += 1
                    print(f"Вакансий собрано: {total_vacancies_quantity}")
    for i in range(1, 51):
        vacancies = []
        urls = []
        info_dict = {}
        url = f"https://russia.superjob.ru/vakansii/turizm-gostinicy-obschestvennoe-pitanie/?order_by%5Bupdated_at%5D=desc&page={i}"
        req = requests.get(url=url, headers=headers)
        src = req.content

        soup = BeautifulSoup(src, 'lxml')

        links = soup.select('div[class*="_2orsF _34A3E"]')

        a_tags = soup.find_all('a', href=True)
        pattern = re.compile(r'/vakansii/.+-\d+\.html')

        filtered_links = [a_tag['href'] for a_tag in a_tags if pattern.match(a_tag['href'])]

        for link in filtered_links:
            if link not in visited_urls:
                visited_urls.add(link)
                urls.append("https://russia.superjob.ru" + link)

                vacancy_id_match = re.search(r'(\d+).html$', f"https://russia.superjob.ru{link}")
                vacancy_id = vacancy_id_match.group(1)

                vacancy_info = get_vacancy_info(access_token, vacancy_id)

                if vacancy_info:
                    vacancy_url = f"https://russia.superjob.ru/{link}"
                    vacancy_date = datetime.utcfromtimestamp(vacancy_info['date_published'])
                    vacancy_name = vacancy_info['profession']
                    town = vacancy_info['town']['title']
                    firm_name = vacancy_info['firm_name']
                    vacancy_address = vacancy_info['address']
                    contact_phone = vacancy_info['phone']
                    contact_face = vacancy_info['contact']
                    if vacancy_address is None:
                        vacancy_address = "Не указан"
                    elif vacancy_address is None:
                        contact_phone = "Не указан"
                    elif contact_face is None:
                        contact_phone = "Не указано"

                    try:
                        vacancy_description = vacancy_info['description']
                    except (TypeError, KeyError):
                        try:
                            vacancy_description = f"{vacancy_info['candidat'][:100]}..."
                        except (TypeError, KeyError):
                            vacancy_description = "Не указано"

                    if not os.path.isfile('superjob.csv'):
                        with open('superjob.csv', 'w', newline='', encoding='utf-8') as csvfile:
                            header = ['Дата публикации', 'Вакансия', 'Описание', 'Город', 'Компания', 'Контактное лицо', 'Телефон', 'Адрес', 'Ссылка']
                            writer = csv.writer(csvfile)
                            writer.writerow(header)

                    with open('superjob.csv', 'a', newline='', encoding='utf-8') as csvfile:
                        data = [vacancy_date, vacancy_name, vacancy_description, town, firm_name, contact_face, contact_phone, vacancy_address, vacancy_url]
                        writer = csv.writer(csvfile)
                        writer.writerow(data)

                    total_vacancies_quantity += 1
                    print(f"Вакансий собрано: {total_vacancies_quantity}")

    while date_pub_from != 0:
        date_pub_to = k-1
        if is_vacancies_list_ended:
            date_pub_from = 0
        else:
            date_pub_from = k
        for i in range(1, 6):
            vacancies = get_vacancies(access_token, i, date_pub_to, date_pub_from)
            if vacancies:
                for vacancy_info in vacancies:
                    vacancy_link = vacancy_info['link']
                    if vacancy_link not in visited_urls:
                        visited_urls.add(vacancy_link)
                        vacancy_date = datetime.utcfromtimestamp(vacancy_info['date_published'])
                        vacancy_name = vacancy_info['profession']
                        town = vacancy_info['town']['title']
                        firm_name = vacancy_info['firm_name']
                        vacancy_address = vacancy_info['address']
                        contact_phone = vacancy_info['phone']
                        contact_face = vacancy_info['contact']

                        if vacancy_address is None:
                            vacancy_address = "Не указан"
                        elif contact_phone is None:
                            contact_phone = "Не указан"
                        elif contact_face is None:
                            contact_phone = "Не указано"

                        try:
                            vacancy_description = vacancy_info['description']
                        except (TypeError, KeyError):
                            try:
                                vacancy_description = f"{vacancy_info['candidat'][:100]}..."
                            except (TypeError, KeyError):
                                vacancy_description = "Не указано"

                        if not os.path.isfile('superjob.csv'):
                            with open('superjob.csv', 'w', newline='', encoding='utf-8') as csvfile:
                                header = ['Дата публикации', 'Вакансия', 'Описание', 'Город', 'Компания', 'Контактное лицо', 'Телефон', 'Адрес', 'Ссылка']
                                writer = csv.writer(csvfile)
                                writer.writerow(header)

                        with open('superjob.csv', 'a', newline='', encoding='utf-8') as csvfile:
                            data = [vacancy_date, vacancy_name, vacancy_description, town, firm_name, contact_face, contact_phone, vacancy_address, vacancy_link]
                            writer = csv.writer(csvfile)
                            writer.writerow(data)
                        total_vacancies_quantity += 1
                        print(f"Вакансий собрано: {total_vacancies_quantity}")
            else:
                is_vacancies_list_ended = True
        k += 1

else:
    print("Не удалось выполнить аутентификацию.")

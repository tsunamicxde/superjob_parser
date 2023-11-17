import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import re
from datetime import datetime
import csv
import os

api_url = "https://api.superjob.ru/2.0/oauth2/password/"
api_headers = {
    "X-Api-App-Id": "your_api_app_id",
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

    response = requests.get(api_url, params=auth_data, headers=api_headers)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print(f"Ошибка аутентификации: {response.text}")
        return None


def get_vacancy_info(access_token, vacancy_id):
    api_url = f"https://api.superjob.ru/2.0/vacancies/{vacancy_id}/"
    api_headers["Authorization"] = f"Bearer {access_token}"
    response = requests.get(api_url, headers=api_headers, timeout=30)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Ошибка получения информации о вакансии: {response.text}")
        return None


login = "your_login"
password = "your_password"
client_id = "your_client_id"
client_secret = "your_client_secret_code"

access_token = authenticate(login, password, client_id, client_secret)

if access_token:
    print(f"Аутентификация прошла успешно. Access token: {access_token}")

    for i in range(2, 51):
        vacancies = []
        urls = []
        info_dict = {}
        url = f"https://russia.superjob.ru/vakansii/turizm-gostinicy-obschestvennoe-pitanie/?page={i}"
        req = requests.get(url=url, headers=headers)
        src = req.content

        soup = BeautifulSoup(src, 'lxml')

        links = soup.select('div[class*="_2orsF _34A3E"]')

        a_tags = soup.find_all('a', href=True)
        pattern = re.compile(r'/vakansii/.+-\d+\.html')

        filtered_links = [a_tag['href'] for a_tag in a_tags if pattern.match(a_tag['href'])]

        for link in filtered_links:
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
else:
    print("Не удалось выполнить аутентификацию.")

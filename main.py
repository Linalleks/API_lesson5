from __future__ import print_function

import requests
from decouple import config
from terminaltables import AsciiTable

PROG_LANGS = ["Python", "Java", "Javascript", "Go", "C++", "C#", "PHP", "Ruby"]


def predict_salary(salary_from, salary_to):
    if not salary_from:
        expected_salary = salary_to * 0.8
    elif not salary_to:
        expected_salary = salary_from * 1.2
    else:
        expected_salary = (salary_from + salary_to) / 2
    return expected_salary


def predict_rub_salary_hh(vacancy):
    salary = vacancy["salary"]
    if not salary or salary["currency"] != 'RUR':
        expected_salary = None
    else:
        expected_salary = predict_salary(salary["from"], salary["to"])
    return expected_salary


def predict_rub_salary_sj(vacancy):
    if not vacancy["payment_from"] and not vacancy["payment_to"] or vacancy["currency"] != 'rub':
        expected_salary = None
    else:
        expected_salary = predict_salary(vacancy["payment_from"], vacancy["payment_to"])
    return expected_salary


def print_statistics_table(title, salary_statistics_in_prog_langs):
    table_data = [
        ['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']
    ]

    for prog_lang, salary_statistics in salary_statistics_in_prog_langs.items():
        table_data.append([prog_lang] + list(salary_statistics.values()))

    table_instance = AsciiTable(table_data, title)
    print(table_instance.table)
    print()


def calc_salary_statistics(all_vacancies, vacancies_found, func_predict_salary):
    vacancies_processed = 0
    average_salary = 0
    for vacancy in all_vacancies:
        salary = func_predict_salary(vacancy)
        if salary:
            vacancies_processed += 1
            average_salary += salary

    if vacancies_processed:
        average_salary = int(average_salary / vacancies_processed)

    return {'vacancies_found': vacancies_found,
            'vacancies_processed': vacancies_processed,
            'average_salary': average_salary}


def get_salary_statistics_hh():
    salary_statistics_in_prog_langs = {}
    for prog_lang in PROG_LANGS:
        page = 0
        all_vacancies = []
        while True:
            params = {
                'professional_role': 96,
                'area': 1,
                'text': prog_lang,
                'per_page': 100,
                'page': page
            }
            response = requests.get('https://api.hh.ru/vacancies', params=params)
            response.raise_for_status()

            vacancies_page = response.json()
            all_vacancies.extend(vacancies_page.get("items"))
            total_pages = vacancies_page.get("pages")
            page += 1
            if total_pages == page:
                break
        salary_statistics_in_prog_langs[prog_lang] = calc_salary_statistics(
            all_vacancies, vacancies_page["found"], predict_rub_salary_hh)

    return salary_statistics_in_prog_langs


def get_salary_statistics_sj(secret_key):
    salary_statistics_in_prog_langs = {}
    headers = {
        'X-Api-App-Id': secret_key
    }
    for prog_lang in PROG_LANGS:
        page = 0
        all_vacancies = []
        while True:
            params = {
                'town': 4,
                'catalogues': 48,
                'keyword': prog_lang,
                'count': 100,
                'page': page
            }
            response = requests.get('https://api.superjob.ru/2.0/vacancies', headers=headers, params=params)
            response.raise_for_status()

            vacancies_page = response.json()
            all_vacancies.extend(vacancies_page.get("objects"))
            if vacancies_page["more"]:
                page += 1
            else:
                break
        salary_statistics_in_prog_langs[prog_lang] = calc_salary_statistics(
            all_vacancies, vacancies_page["total"], predict_rub_salary_sj)

    return salary_statistics_in_prog_langs


def main():
    print_statistics_table('HeadHunter Moscow', get_salary_statistics_hh())
    print_statistics_table('SuperJob Moscow', get_salary_statistics_sj(config('SJ_SECRET_KEY')))


if __name__ == '__main__':
    main()

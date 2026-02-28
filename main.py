from __future__ import print_function

import requests
from decouple import config
from terminaltables import AsciiTable


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
    TABLE_DATA = [
        ['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']
    ]

    for prog_lang, salary_statistics in salary_statistics_in_prog_langs.items():
        TABLE_DATA.append([prog_lang] + list(salary_statistics.values()))

    table_instance = AsciiTable(TABLE_DATA, title)
    print(table_instance.table)
    print()


def get_salary_statistics_hh(prog_langs):
    salary_statistics_in_prog_langs = {}
    for prog_lang in prog_langs:
        page = 0
        all_vacancies = []
        salary_statistics = {}
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
                salary_statistics["vacancies_found"] = vacancies_page["found"]
                salary_statistics["vacancies_processed"] = 0
                salary_statistics["average_salary"] = 0
                break

        for vacancy in all_vacancies:
            salary = predict_rub_salary_hh(vacancy)
            if salary:
                salary_statistics["vacancies_processed"] += 1
                salary_statistics["average_salary"] += salary

        if salary_statistics["vacancies_processed"] > 0:
            salary_statistics["average_salary"] = int(
                salary_statistics["average_salary"] / salary_statistics["vacancies_processed"])

        salary_statistics_in_prog_langs[prog_lang] = salary_statistics

    print_statistics_table('HeadHunter Moscow', salary_statistics_in_prog_langs)


def get_salary_statistics_sj(prog_langs):
    salary_statistics_in_prog_langs = {}
    headers = {
        'X-Api-App-Id': config('SJ_SECRET_KEY')
    }
    for prog_lang in prog_langs:
        page = 0
        all_vacancies = []
        salary_statistics = {}
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
                salary_statistics["vacancies_found"] = vacancies_page["total"]
                salary_statistics["vacancies_processed"] = 0
                salary_statistics["average_salary"] = 0
                break

        for vacancy in all_vacancies:
            salary = predict_rub_salary_sj(vacancy)
            if salary:
                salary_statistics["vacancies_processed"] += 1
                salary_statistics["average_salary"] += salary

        if salary_statistics["vacancies_processed"] > 0:
            salary_statistics["average_salary"] = int(
                salary_statistics["average_salary"] / salary_statistics["vacancies_processed"])

        salary_statistics_in_prog_langs[prog_lang] = salary_statistics

    print_statistics_table('SuperJob Moscow', salary_statistics_in_prog_langs)


def main():
    prog_langs = ["Python", "Java", "Javascript", "Go", "C++", "C#", "PHP", "Ruby"]
    get_salary_statistics_hh(prog_langs)
    get_salary_statistics_sj(prog_langs)


if __name__ == '__main__':
    main()

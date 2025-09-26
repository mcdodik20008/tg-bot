import requests
from bs4 import BeautifulSoup
import fake_useragent
import csv
import os
import re

# --- НАСТРОЙКИ ---
SEARCH_QUERY = "C# Разработчик"
SEARCH_AREA = 1
PAGES_TO_PARSE = 1
# -----------------

# Словарь для преобразования кода региона в название для файла
AREA_MAP = {
    1: 'moscow',
    2: 'saint_petersburg',
    113: 'russia'
}


def slugify(text):
    """
    Преобразует текст в "безопасную" строку для имени файла.
    Пример: "Разработчик Python" -> "razrabotchik_python"
    """
    # Транслитерация кириллицы
    cyrillic_map = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo', 'ж': 'zh',
        'з': 'z', 'и': 'i', 'й': 'j', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o',
        'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'c',
        'ч': 'ch', 'ш': 'sh', 'щ': 'shch', 'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
    }
    text = text.lower()
    for cyr, lat in cyrillic_map.items():
        text = text.replace(cyr, lat)

    # Замена пробелов и прочих символов на _
    text = re.sub(r'[^a-z0-9]+', '_', text)
    return text.strip('_')


def get_text_or_default(tag, default="Не указано"):
    """
    Безопасно извлекает текст из тега и очищает его.
    """
    if not tag:
        return default

    text = tag.get_text(strip=True, separator=' ').replace('\u2009', ' ').replace('\xa0', ' ')
    text = re.sub(r'\s+', ' ', text).strip()

    return text if text else default


def get_resume_links(query, page, area):
    """Получает ссылки на резюме со страницы поиска."""
    url = "https://hh.ru/search/resume"
    params = {
        "text": query,
        "area": area,
        "exp_period": "all_time",
        "logic": "normal",
        "pos": "full_text",
        "search_period": 0,
        "items_on_page": 50,
        "page": page
    }
    user = fake_useragent.UserAgent()
    headers = {'User-Agent': user.random}

    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        links = []
        for a in soup.find_all('a', {'data-qa': 'serp-item__title'}):
            clean_link = "https://hh.ru" + a['href'].split('?')[0]
            links.append(clean_link)
        return links
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе страницы поиска: {e}")
        return []


def parse_resume(url):
    """Парсит страницу одного резюме."""
    user = fake_useragent.UserAgent()
    headers = {'User-Agent': user.random}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        name = get_text_or_default(soup.find('h2', {'data-qa': 'bloko-header-1'}))
        gender = get_text_or_default(soup.find('span', {'data-qa': 'resume-personal-gender'}))
        age = get_text_or_default(soup.find('span', {'data-qa': 'resume-personal-age'}))
        personal_info = f"{gender}, {age}"

        address_p = soup.find('p', string=lambda t: t and ("готов к переезду" in t or "не готов к переезду" in t))
        location_info = "Не указано"
        if not address_p:
            address_span = soup.find('span', {'data-qa': 'resume-personal-address'})
            if address_span:
                location_info = get_text_or_default(address_span.find_parent('p'))
        else:
            location_info = get_text_or_default(address_p)

        desired_position = get_text_or_default(soup.find('span', {'data-qa': 'resume-block-title-position'}))
        salary = get_text_or_default(soup.find('span', {'data-qa': 'resume-block-salary'}))

        employment_tags = soup.find_all('p', string=lambda t: t and ("Занятость:" in t or "График работы:" in t))
        employment_info = ", ".join(
            [get_text_or_default(p) for p in employment_tags]) if employment_tags else "Не указано"

        experience_block = soup.find('div', {'data-qa': 'resume-block-experience'})
        total_experience = get_text_or_default(experience_block.find('span',
                                                                     class_='resume-block__title-text_sub')) if experience_block else "Опыт не указан"

        last_job, last_job_description = "Не указано", "Не указано"
        if experience_block:
            job_item = experience_block.find('div', class_='resume-block-item-gap')
            if job_item:
                company_container = job_item.find('div', class_='bloko-text bloko-text_strong')
                company = get_text_or_default(company_container)

                position = get_text_or_default(job_item.find('div', {'data-qa': 'resume-block-experience-position'}))
                last_job = f"{position} в {company}"
                last_job_description = get_text_or_default(
                    job_item.find('div', {'data-qa': 'resume-block-experience-description'}))

        skills_tags = soup.select('[data-qa="bloko-tag__text"]')
        skills = ", ".join(
            [get_text_or_default(skill) for skill in skills_tags]) if skills_tags else "Навыки не указаны"

        about_me = get_text_or_default(soup.find('div', {'data-qa': 'resume-block-skills-content'}))
        education_items = soup.select('[data-qa="resume-block-education-item"]')
        education = "; ".join(
            [get_text_or_default(item) for item in education_items]) if education_items else "Не указано"
        language_items = soup.select('[data-qa="resume-block-language-item"]')
        languages = ", ".join(
            [get_text_or_default(item) for item in language_items]) if language_items else "Не указано"

        return {
            'ФИО': name, 'Желаемая должность': desired_position, 'Зарплата': salary, 'Личная информация': personal_info,
            'Местоположение': location_info, 'Занятость и график': employment_info, 'Общий опыт': total_experience,
            'Последнее место работы': last_job, 'Обязанности': last_job_description, 'Ключевые навыки': skills,
            'Обо мне': about_me, 'Образование': education, 'Языки': languages, 'Ссылка': url,
        }

    except Exception as e:
        print(f"Не удалось разобрать страницу резюме {url}: {e}")
        return None


def save_to_csv(data, query, area_code):
    """Сохраняет данные в CSV файл с динамическим именем."""
    if not data:
        print("Нет данных для сохранения.")
        return

    output_dir = os.path.join('..', 'datasets')

    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Папка создана: {output_dir}")
    except OSError as e:
        print(f"Ошибка при создании папки {output_dir}: {e}")
        return

    # Формируем имя файла из параметров
    query_slug = slugify(query)
    area_slug = AREA_MAP.get(area_code, str(area_code))
    filename = f"resume_{query_slug}_{area_slug}.csv"
    file_path = os.path.join(output_dir, filename)

    headers = data[0].keys()
    try:
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)
        print(f"Данные успешно сохранены в файл: {file_path}")
    except IOError as e:
        print(f"Ошибка при записи в файл {file_path}: {e}")


if __name__ == '__main__':
    print(f"Начинаю парсинг по запросу: '{SEARCH_QUERY}'")

    all_resumes_data = []

    for page_num in range(PAGES_TO_PARSE):
        print(f"\nПарсинг страницы {page_num + 1}...")
        resume_urls = get_resume_links(SEARCH_QUERY, page_num, SEARCH_AREA)

        if not resume_urls:
            print("Не найдено ссылок на резюме.")
            break

        print(f"Найдено {len(resume_urls)} резюме. Начинаю обработку...")
        for url in resume_urls:
            data = parse_resume(url)
            if data:
                all_resumes_data.append(data)
                print(f"  + Обработано: {data['ФИО']} | {data['Желаемая должность']}")

    print("\n--- Парсинг завершен ---")

    save_to_csv(all_resumes_data, SEARCH_QUERY, SEARCH_AREA)
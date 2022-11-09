import os
import datetime
import os.path
import shutil
import time

import smtplib
from email.message import EmailMessage


from settings import *

current_day = datetime.datetime.now().strftime("%Y%m%d")  # текущий день на начало старта скрипта


def log(s, need_to_write: bool = True):
    """ Вывод сообщения в командную строку и, если нужно, то и запись в файл """
    now = datetime.datetime.now()
    msg = f'{now.strftime("%Y-%m-%d %H:%M:%S")}: {s}'
    print(msg)
    if need_to_write:
        fn = f'{now.strftime("%Y%m%d")}_log.txt'
        log_dir = 'logs'
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)
        fn = os.path.join(log_dir, fn)
        with open(fn, 'a', encoding='utf-8') as f:
            f.write(f'{msg}\n')


def get_files(path, is_scan_subfolder=False):
    """ Получить список файлов в заданной папке. Если вторым параметром передать True, то будет сканировать подпапки """
    found_files = []
    if is_scan_subfolder:
        # сканировать и подпапки
        try:
            for root, dirs, files in os.walk(path):
                for file in files:
                    found_files.append(os.path.join(root, file))
        except Exception as e:
            log(f'Ошибка получения списка файлов: {e}')
    else:
        try:
            with os.scandir(path) as files:
                found_files = [os.path.join(path, file.name) for file in files if file.is_file()]
        except Exception as e:
            log(f'Ошибка получения списка файлов: {e}')

    return found_files


def move_files(found_files, dest_folder):
    if not os.path.isdir(dest_folder):
        log(f'Не найдена папка для перемещения: {dest_folder}')
        return False

    for num, file_name in enumerate(found_files):
        try:
            shutil.move(file_name, dest_folder)
            log(f'Успешно перемещен файл {file_name} в папку {dest_folder}. [{num+1}/{len(found_files)}]')
        except Exception as e:
            log(f'Ошибка перемещения файла "{file_name}": {e}')
            return False

    return True


def send_log_to_email(fn):
    msg = EmailMessage()

    msg['From'] = FROM_EMAIL
    msg['To'] = TO_EMAIL
    msg['Subject'] = 'Уведомление от скрипта "FolderScaner"'

    body = 'Скрипт работает...'

    try:
        msg.set_content(body)
        msg.add_attachment(open(fn, "r", encoding='utf-8').read(), filename=os.path.basename(fn))

        server = smtplib.SMTP_SSL('smtp.mail.ru', 465)
        server.login(FROM_EMAIL, FROM_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        log(f'Ошибка отправки письма: {str(e)}')
        return False


def main():
    is_found = True
    global current_day
    while True:
        if is_found:
            log('Ожидание новых файлов...')
        found_files = get_files(OBSERVATION_FOLDER, SCAN_SUBFOLDERS)
        if found_files:
            log(f'Количество новых файлов: {len(found_files)}')
            if not move_files(found_files, MOVE_FOLDER):
                log('Не удалось перемесить файлы. Делаем паузу в 1 минуту...')
                time.sleep(60)
            else:
                is_found = True
        else:
            is_found = False

        time.sleep(PAUSE_REFRESH_FOLDER)

        now_day = datetime.datetime.now().strftime("%Y%m%d")
        if now_day != current_day:
            log('Сработал переход на новый день и будет отправлено уведомление на почту!')
            fn = os.path.join('logs', f'{current_day}_log.txt')
            send_log_to_email(fn)
            current_day = now_day


if __name__ == '__main__':
    main()

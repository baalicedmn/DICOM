import paramiko
import getpass
import time
import re

# Данные подключения
host = "192.168.32.134"
port = 22
username = input("Введите имя пользователя SSH: ")
password = getpass.getpass("Введите пароль SSH: ")

# Получаем значение mpps_iuid от пользователя
mpps_iuid = input("Введите значение mpps_iuid: ")

# SQL-запрос (только статус)
sql_query = f"psql -d pacsdb -t -A -F',' -c \"SELECT mpps_status FROM mpps WHERE mpps_iuid = '{mpps_iuid}';\""

# Отображение числового статуса
status_map = {"0": "IN PROGRESS", "1": "COMPLETED", "2": "DISCONTINUED"}

try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, port=port, username=username, password=password)

    channel = client.invoke_shell()
    time.sleep(1)

    # Повышение до postgres
    channel.send("sudo -i -u postgres\n")
    time.sleep(1)

    if channel.recv_ready():
        recv = channel.recv(1024).decode("utf-8")
        if f"[sudo] password for {username}" in recv:
            sudo_password = getpass.getpass("Введите пароль для sudo: ")
            channel.send(sudo_password + "\n")
            time.sleep(1)

    # Выполнение SQL-запроса
    channel.send(sql_query + "\n")
    time.sleep(2)

    result = ""
    while channel.recv_ready():
        result += channel.recv(4096).decode("utf-8")
        time.sleep(0.3)

    # Парсинг статуса
    match = re.search(r"^\s*(\d+)", result, re.MULTILINE)
    if match:
        status_code = match.group(1)
        status_text = status_map.get(status_code, f"Неизвестный статус: {status_code}")
        print(f"\n✅ Статус MPPS: {status_text} (код {status_code})")
    else:
        print("\n⚠️ Статус MPPS не найден или пустой результат.")

    channel.close()
    client.close()

except Exception as e:
    print(f"❌ Ошибка: {e}")

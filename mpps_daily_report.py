import paramiko
import getpass
import time

# import re

# Подключение
host = "192.168.32.134"
port = 22
username = input("Введите имя пользователя SSH: ")
password = getpass.getpass("Введите пароль SSH: ")

input_date = input("Введите дату (dd.mm.yyyy) или Enter для сегодняшнего дня: ").strip()
input_patid = input(
    "Введите pat_id (например, auto131810) или Enter для всех пациентов: "
).strip()

if input_date:
    date_filter = f"DATE(m.pps_start) = TO_DATE('{input_date}', 'DD.MM.YYYY')"
else:
    date_filter = "DATE(m.pps_start) = CURRENT_DATE"

if input_patid:
    patid_filter = f" AND p.pat_id = '{input_patid}'"
else:
    patid_filter = ""

# SQL-запрос на сегодня
sql_query = """
psql -d pacsdb -t -A -F',' -c "
    SELECT
        m.mpps_iuid,
        TO_CHAR(m.pps_start, 'DD.MM.YYYY HH24:MI') AS start_time,
        p.pat_name,
        p.pat_id,
        m.mpps_status
    FROM
        mpps m
    JOIN
        patient p ON m.patient_fk = p.pk
    WHERE
        {date_filter}
        {patid_filter}
    ORDER BY
        m.pps_start;"
"""

status_map = {"0": "IN PROGRESS", "1": "COMPLETED", "2": "DISCONTINUED"}

try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, port=port, username=username, password=password)

    channel = client.invoke_shell()
    time.sleep(1)
    channel.send("sudo -i -u postgres\n")
    time.sleep(1)

    if channel.recv_ready():
        recv = channel.recv(1024).decode("utf-8")
        if f"[sudo] password for {username}" in recv:
            sudo_password = getpass.getpass("Введите пароль для sudo: ")
            channel.send(sudo_password + "\n")
            time.sleep(1)

    channel.send(sql_query + "\n")
    time.sleep(2)

    result = ""
    while channel.recv_ready():
        result += channel.recv(4096).decode("utf-8")
        time.sleep(0.3)

        # Обработка результатов
        print("\n📋 Исследования за сегодня (текущая дата)")
        print("=" * 120)
        print(
            f"{'MPPS UID':<38} {'Patient':<25} {'AccNo':<12} {'Mod':<6} {'Date/Time':<20} {'MPPS Status'}"
        )
        print("-" * 120)

        for line in result.splitlines():
            if line.strip() and "," in line:
                parts = line.strip().split(",")
                if len(parts) >= 7:
                    mpps_uid = parts[0].strip()
                    start_time = parts[1].strip()
                    pat_name = parts[2].strip()
                    pat_id = parts[3].strip()
                    acc_no = parts[4].strip()
                    modality = parts[5].strip()
                    status_code = parts[6].strip()
                    status_text = status_map.get(
                        status_code, f"UNKNOWN ({status_code})"
                    )

                    print(
                        f"{mpps_uid[:37]:<38} {pat_name[:24]:<25} {acc_no:<12} {modality:<6} {start_time:<20} {status_text}"
                    )

    channel.close()
    client.close()

except Exception as e:
    print(f"\n❌ Ошибка: {e}")

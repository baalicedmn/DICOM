# Проверка работоспособности MPPS посредством python. 

Для проверки можно использовать как VSCode, так и любую Unix систему.

## Инструкция для VSCode

1. Создать рабочее простарство
2. Создать в рабочем пространстве виртуальное окружение, командой "python -m venv venv"
3. Разрешить исполнение повершел скриптов если необходимо, в повершеле от админа командой "Set-ExecutionPolicy RemoteSigned" и подтвердить А
4. Активировать рабочее пространство командой ".\venv\Scripts\Activate.ps1 "
5. Обновить pip командой "python -m pip install --upgrade pip"
6. Установить нужные для проверки зависимости "pip install pydicom pynetdicom paramiko"
7. Создать пайтон скрипт для создания запроса mpps, для примера название пусть будет "send_mpps_ncreate.py"
8. Вставить код в созданный файл и сохранить:

    <details>
        <summary>Показать код send_mpps_ncreate.py</summary>

            ```python
            from pydicom.dataset import Dataset
            from pydicom.uid import generate_uid
            from pynetdicom import AE
            from pynetdicom.sop_class import ModalityPerformedProcedureStep
            import datetime

            # 📅 Получаем текущую дату и время
            now = datetime.datetime.now()
            start_date = now.strftime("%Y%m%d")
            start_time = now.strftime("%H%M%S")

            # 🔐 Генерация случайного MPPS UID
            mpps_uid = generate_uid(prefix="2.25.")

            # 📦 Формируем Dataset для N-CREATE
            ds = Dataset()
            ds.SOPClassUID = ModalityPerformedProcedureStep
            ds.SOPInstanceUID = mpps_uid
            ds.PerformedProcedureStepID = "MPPS_TEST_" + now.strftime("%H%M%S")
            ds.PerformedProcedureStepStatus = "IN PROGRESS"
            ds.PerformedProcedureStepStartDate = start_date
            ds.PerformedProcedureStepStartTime = start_time
            ds.Modality = "OT"  # Например: MG, CT, MR и т.д.
            ds.PerformedStationAETitle = "MPPSSCU"
            ds.PerformedStationName = "TEST_STATION"
            ds.StudyInstanceUID = generate_uid(prefix="2.25.")

            # 👤 Данные пациента
            ds.PatientName = "TEST"
            ds.PatientID = "TEST123"

            # 🗓️ (0040,0270) ScheduledStepAttributesSequence — обязательный Type 1
            scheduled_step = Dataset()
            scheduled_step.ScheduledStationAETitle = "MPPSSCU"
            scheduled_step.ScheduledProcedureStepStartDate = start_date
            scheduled_step.ScheduledProcedureStepStartTime = start_time
            scheduled_step.ScheduledProcedureStepDescription = "Test MPPS"
            scheduled_step.ScheduledProcedureStepID = "SPSID1234"
            scheduled_step.RequestedProcedureID = "REQID1234"
            scheduled_step.StudyInstanceUID = ds.StudyInstanceUID
            ds.ScheduledStepAttributesSequence = [scheduled_step]

            # 📡 Установка соединения
            ae = AE(ae_title="MPPSSCU")
            ae.add_requested_context(ModalityPerformedProcedureStep)

            assoc = ae.associate("192.168.32.134", 11112, ae_title="DCM107")

            if assoc.is_established:
                print(f"📡 Соединение установлено. Отправка N-CREATE для UID:\n➡️  {mpps_uid}")

                status = assoc.send_n_create(
                    dataset=ds,
                    class_uid=ModalityPerformedProcedureStep,
                    instance_uid=mpps_uid
                )

                status_code, _ = status
                if isinstance(status_code, Dataset):
                    print(f"✅ Ответ сервера: Status = 0x{status_code.Status:04x}")
                elif isinstance(status_code, int):
                    print(f"✅ Ответ сервера: Status = 0x{status_code:04x}")
                else:
                    print(f"⚠️ Неизвестный тип ответа: {status_code}")

                assoc.release()
            else:
                print("❌ Не удалось установить соединение с сервером.")
            ```

	
9. Исполняем скрипт и ищем в логах сервера тестового пациента, успешный запрос в логе выглядит так:

    <details>
    <summary>Показать лог сервера</summary>

        ```log
        2025-07-10 10:20:35,393 INFO  -> (TCPServer-1-3) [org.dcm4cheri.server.ServerImpl] handle - Socket[addr=/192.168.41.23,port=47795,localport=11112]
        2025-07-10 10:20:35,393 INFO  -> (TCPServer-1-3) [org.dcm4cheri.net.FsmImpl] Socket[addr=/192.168.41.23,port=47795,localport=11112]
        2025-07-10 10:20:35,393 INFO  MPPSSCU->DCM107 (TCPServer-1-3) [org.dcm4cheri.net.FsmImpl] received AAssociateRQ
            appCtxName:	1.2.840.10008.3.1.1.1/DICOM Application Context Name
            implClass:	1.2.826.0.1.3680043.9.3811.3.0.3
            implVersion:	PYNETDICOM_303
            calledAET:	DCM107
            callingAET:	MPPSSCU
            maxPDULen:	16382
            asyncOpsWindow:	
            pc-1:	as=1.2.840.10008.3.1.2.3.3/Modality Performed Procedure Step SOP Class
                ts=1.2.840.10008.1.2/Implicit VR Little Endian
                ts=1.2.840.10008.1.2.1/Explicit VR Little Endian
                ts=1.2.840.10008.1.2.1.99/Deflated Explicit VR Little Endian
                ts=1.2.840.10008.1.2.2/Explicit VR Big Endian
        2025-07-10 10:20:35,395 INFO  MPPSSCU->DCM107 (TCPServer-1-3) [org.dcm4cheri.net.FsmImpl] sending AAssociateAC
            appCtxName:	1.2.840.10008.3.1.1.1/DICOM Application Context Name
            implClass:	1.2.40.0.13.1.1.1
            implVersion:	dcm4che-1.4.33
            calledAET:	DCM107
            callingAET:	MPPSSCU
            maxPDULen:	16352
            asyncOpsWindow:	
            pc-1:	0 - acceptance
                ts=1.2.840.10008.1.2.1/Explicit VR Little Endian
        2025-07-10 10:20:35,435 INFO  MPPSSCU->DCM107 (TCPServer-1-3) [org.dcm4cheri.net.FsmImpl] received [pc-1] 1:N_CREATE_RQ with Dataset
            class:	1.2.840.10008.3.1.2.3.3/Modality Performed Procedure Step SOP Class
            inst:	2.25.4385061255521984359992215834134387840122231812574317535471/?
        2025-07-10 10:20:35,439 INFO  MPPSSCU->DCM107 (TCPServer-1-3) [org.dcm4chex.archive.ejb.entity.PatientBean] Created Patient[pk=433870, pid=TEST123, issuer=null, name=TEST^^^^]
        2025-07-10 10:20:35,522 INFO  MPPSSCU->DCM107 (TCPServer-1-3) [org.dcm4chex.archive.ejb.entity.MPPSBean] Created MPPS[pk=44419, iuid=2.25.47708778590409370161849180212254028873199035993373897800443, status=IN PROGRESS, patient->ejb/Patient:433870]
        2025-07-10 10:20:35,562 INFO  MPPSSCU->DCM107 (TCPServer-1-3) [org.dcm4chex.archive.dcm.mwlscp.MWLFindScpService] No such MWL item[spsid=SPSID1234]
        2025-07-10 10:20:35,563 INFO  MPPSSCU->DCM107 (TCPServer-1-3) [org.dcm4cheri.net.FsmImpl] sending [pc-1] 1:N_CREATE_RSP
            class:	1.2.840.10008.3.1.2.3.3/Modality Performed Procedure Step SOP Class
            inst:	2.25.4385061255521984359992215834134387840122231812574317535471/?
            status:	0
        2025-07-10 10:20:35,568 INFO  MPPSSCU->DCM107 (TCPServer-1-3) [org.dcm4cheri.net.FsmImpl] received A-RELEASE-RQ
        2025-07-10 10:20:35,568 INFO  MPPSSCU->DCM107 (TCPServer-1-3) [org.dcm4cheri.net.FsmImpl] sending A-RELEASE-RP
        2025-07-10 10:20:35,619 INFO  MPPSSCU->DCM107 (TCPServer-1-3) [org.dcm4cheri.net.FsmImpl] closing connection - Socket[addr=/192.168.41.23,port=47795,localport=11112]
        2025-07-10 10:20:35,619 INFO  -> (TCPServer-1-3) [org.dcm4cheri.server.ServerImpl] finished - Socket[addr=/192.168.41.23,port=47795,localport=11112]
        ```

Так же VSCode нам соообщит:

📡 Соединение установлено. Отправка N-CREATE для UID:
➡️  2.25.47708778590409370161849180212254028873199035993373897800443
✅ Ответ сервера: Status = 0x0000

Код 0x0000 означает успешне соединение и создание mpps статуса.

10. Далее нам надо создать скрипт исполнения запроса, также создаем файл send_mpps_nset_completed.py и копируем в него код:

    <details>
    <summary>Показать код send_mpps_nset_completed.py</summary>

        ```python
        from pydicom.dataset import Dataset
        from pynetdicom import AE
        from pynetdicom.sop_class import ModalityPerformedProcedureStep
        import sys
        from datetime import datetime

        # 👉 Получение UID из аргументов
        if len(sys.argv) != 2:
            print("Usage: python3 send_mpps_nset_completed.py <MPPS_SOP_Instance_UID>")
            sys.exit(1)

        mpps_uid = sys.argv[1]

        # 📦 Создание Dataset для N-SET с изменением статуса на COMPLETED и временем завершения
        ds = Dataset()
        ds.PerformedProcedureStepStatus = "COMPLETED"

        now = datetime.now()
        ds.PerformedProcedureStepEndDate = now.strftime("%Y%m%d")  # YYYYMMDD
        ds.PerformedProcedureStepEndTime = now.strftime("%H%M%S")  # HHMMSS

        ds.PerformedSeriesSequence = [Dataset()]

        # 📡 Настройка AE и контекста
        ae = AE(ae_title="MPPSSCU")
        ae.add_requested_context(ModalityPerformedProcedureStep)

        assoc = ae.associate("192.168.32.134", 11112, ae_title="DCM107")

        if assoc.is_established:
            print(f"🔗 Связь установлена. Отправляем N-SET для UID: {mpps_uid}")

            # Отправка N-SET
            status = assoc.send_n_set(ds, class_uid=ModalityPerformedProcedureStep, instance_uid=mpps_uid)

            # Обработка ответа
            status_code, _ = status
            if isinstance(status_code, Dataset):
                print(f"✅ Ответ от сервера: Status = 0x{status_code.Status:04x}")
            elif isinstance(status_code, int):
                print(f"✅ Ответ от сервера: Status = 0x{status_code:04x}")
            else:
                print(f"⚠️ Неизвестный тип ответа: {status_code}")

            assoc.release()
        else:
            print("❌ Ошибка: не удалось установить соединение с сервером.")
        ```	
	
11. Исполняем этот скрипт с аргуменом UID который мы получили на шаге выше (пример: send_mpps_nset_completed.py 2.25.47708778590409370161849180212254028873199035993373897800443) смотрим статус исполнения и проверяем завершение статуса mpps в БД пакса:
Успешный ответ выглядит так:
🔗 Связь установлена. Отправляем N-SET для UID: 2.25.47708778590409370161849180212254028873199035993373897800443
✅ Ответ от сервера: Status = 0x0000
Убедимся, что наш запрос корректно завершился, проверим это в БД пакса
(если настройка dcm4che типовая то в бд попадаем так): 	

- переключаемся на пользователя postgres командой "sudo -i -u postgres"
- переключаемся на нужную нам бд "psql pacsdb", узнать к какой бд подключен пользователь на данный момент можно командой \c
- ищем статус нашего mpps подтерждения командой "SELECT * FROM mpps WHERE mpps_iuid = '2.25.47708778590409370161849180212254028873199035993373897800443';" \\mpps_uid берем из лога выше, там он называется iuid
Дополнительно: статус mpps_status
Если это integer, то значения могут означать:
0 — IN PROGRESS
1 — COMPLETED
2 — DISCONTINUED 

Запрос в БД сообщил, что статус моего подтвеждения mpps = 1, что означает успешную проверку.

<details>
<summary>Показать вывод запроса</summary>

```sql
pk   | patient_fk | drcode_fk |                            mpps_iuid                             |      pps_start      | station_aet | modality | accession_no | mpps_status |      created_time       |      updated_time       |                                                                                                                                                                                                                                                                                                                                                           mpps_attrs                                                                                                                                                                                                                                                                                                                                                           
-------+------------+-----------+------------------------------------------------------------------+---------------------+-------------+----------+--------------+-------------+-------------------------+-------------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
44426 |     433890 |           | 2.25.47708778590409370161849180212254028873199035993373897800443 | 2025-07-10 10:43:58 | MPPSSCU     | OT       |              |           1 | 2025-07-10 10:43:59.311 | 2025-07-10 10:47:45.606 | \x02000000554c04001e0000000200100055491600312e322e3834302e31303030382e312e322e312e3939ad4f416ec2400c1c82d4a6a8489c2a8ebc20b2d7bbd9dddba610092468021bcef4d27ba5f6bb95780969828a5a38d717cb33f68c27c513f6ab29385399d3943111b94cb27e964c9062daf1012a5326d3d692b3d6194f9abc58e29c9df6ec48b152469372ce0a7b4f62bc17b1e2bc75445a4b8a57cc6382aa9961fcabc82c968d359c5b21f6d64ba72c4ee79c6b518a24d74a792666638c38e1dc3bf69a9cb1014552942936751de37c3f0b784ee2f2114d199b436c8a6655bd042c924591429132649902caa4d9dc81498b7101f50dbbbdb056eb805d328f23ccab4dbd2e9b72d139c4ce6172763c9c6d2e3aef49dc026d57a716c7beff5fca01ae5326b8fe7988bf89eeb1ae4668de3e3e67fd49b7ff80b81c21d671b56025ba4306931ed995db1fe4d48e8fe8ead47e9d7b4018dee6b9ddf906
(1 row)
```
</details>    

## UPD:
Настройка окружения для Ubuntu

1. Обновляем пакеты "sudo apt update"
2. Устанавливаем пайтон окружение и пип "sudo apt install python3-venv python3-pip"
3. Создаем виртуальное окружение "python3 -m venv venv-mpps"
4. Активируем виртуальное окружение "source venv-mpps/bin/activate"
5. Установливаем нужные для проверки зависимости "pip install pydicom pynetdicom paramiko"
6. Далее все как для VSCode

## UPD:

Вместо ручной проверки состояния статуса mpps (п.7 и далее) можно использовать скрипт mpps_value_check.py
При запуске указываются учетные данные для подключения к серверу ПАКС, посредством ssh
Далее вводится искомый mpps_iuid
После чего подтверждаем паролем привелигерованный режим для пользователя БД

По окончанию отработки скрипт отдаст значение записанное в БД в виде:

0 — IN PROGRESS
1 — COMPLETED
2 — DISCONTINUED

Пример: ✅ Статус MPPS: COMPLETED (код 1)

Код для mpps_value_check.py

<details>
<summary>Показать код mpps_value_check.py</summary>

```python
import paramiko
import getpass
import time
import re

# Данные подключения
host = "YOUR_IP"
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
```
</details> 
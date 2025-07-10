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
    status = assoc.send_n_set(
        ds, class_uid=ModalityPerformedProcedureStep, instance_uid=mpps_uid
    )

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

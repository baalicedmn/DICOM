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
        dataset=ds, class_uid=ModalityPerformedProcedureStep, instance_uid=mpps_uid
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

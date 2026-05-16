# Print Server — Zebra LP2844 на Orange Pi Zero 3

HTTP сервер для печати этикеток. Принимает задания от cutting-api и печатает через EPL2 на Zebra LP2844.

## Архитектура

```
cutting-app (планшет)
      ↓ PUT /pieces/{id}/done
cutting-api (192.168.1.201:8020)
      ↓ POST /print  [fire-and-forget, timeout 10s]
print-server (192.168.1.52:8050)   ← Orange Pi Zero 3
      ↓ EPL2 binary
Zebra LP2844 → /dev/usb/lp0
```

## Железо

| Устройство | Описание |
|---|---|
| Принтер | Zebra LP2844, протокол EPL2, USB → `/dev/usb/lp0` |
| Сервер | Orange Pi Zero 3 2GB, Armbian Bookworm, microSD |
| IP | `192.168.1.52` (WiFi, статический по MAC в роутере) |
| MAC WiFi | `24:5c:93:66:d7:53` |

---

## API

### POST /print
Печать производственной этикетки. Вызывается из cutting-api.

**Request:**
```json
{
  "length": 1200,
  "qty": 1,
  "profile_code": "П-60x60",
  "profile_name": "Стойка угловая",
  "order_title": "Перегородка офис 3 этаж",
  "order_number": "2024-042",
  "section_path": "Секция_А/Левая_часть",
  "color": "RAL 9010"
}
```

| Поле | Тип | Описание |
|---|---|---|
| `length` | int (мм) | Длина детали |
| `qty` | int | Количество (сейчас всегда 1) |
| `profile_code` | string | Код профиля |
| `profile_name` | string | Название профиля |
| `order_title` | string | Название заказа |
| `order_number` | string | Номер заказа (может быть `""`) |
| `section_path` | string | Путь по группам через `/` (может быть `""`) |
| `color` | string | Цвет (может быть `""`) |

**Response:**
```json
{"ok": true}
```

**Тест с PowerShell:**
```powershell
Invoke-WebRequest -Uri "http://192.168.1.52:8050/print" `
  -Method POST -ContentType "application/json" `
  -Body '{"length":1200,"qty":1,"profile_code":"П-60x60","profile_name":"Стойка угловая","order_title":"Перегородка офис","order_number":"2024-042","section_path":"Секция_А","color":"RAL 9010"}'
```

**Тест с curl (Linux/Mac):**
```bash
curl -X POST http://192.168.1.52:8050/print \
  -H 'Content-Type: application/json' \
  -d '{"length":1200,"qty":1,"profile_code":"П-60x60","profile_name":"Стойка угловая","order_title":"Перегородка офис","order_number":"2024-042","section_path":"Секция_А","color":"RAL 9010"}'
```

---

### GET /health
Проверка состояния сервера.

```bash
curl http://192.168.1.52:8050/health
# {"ok": true}
```

---

### GET /
Веб-редактор этикеток. Открывать в браузере:
```
http://192.168.1.52:8050
```

Позволяет создавать произвольные этикетки с текстом, QR-кодом и изображениями. Предпросмотр рендерится на сервере (точное WYSIWYG).

---

### POST /preview
Рендер этикетки в PNG (используется веб-редактором).

### POST /print-custom
Печать произвольного layout из веб-редактора.

---

## Интеграция с cutting-api

В файле `.env` cutting-api добавить:
```
PRINT_SERVER_URL=http://192.168.1.52:8050
```

Перезапустить:
```bash
docker compose up -d cutting-api
```

cutting-api вызывает `POST /print` после `PUT /pieces/{id}/done` если `print_mode == "per_piece"`. Запрос отправляется в отдельном потоке, таймаут 10 секунд, ошибки не блокируют основной флоу.

---

## Этикетка

**Размер:** 40×57мм (текущий рулон), настраивается через `.env`

**Layout:**
```
┌────────────────────────┐
│ #2024-042  Заказ...    │  ← номер + название заказа
│ Стойка угловая         │  ← название профиля
│ П-60x60                │  ← код профиля
│ 1200 mm                │  ← длина (крупно)
│ RAL 9010               │  ← цвет
│ Секция_А/Левая_часть   │  ← путь секции
│      ┌──────────┐      │
│      │    QR    │      │  ← 160×160 dots, по центру
│      └──────────┘      │
└────────────────────────┘
```

**QR содержит все поля:**
```
№2024-042 | Перегородка офис | Стойка угловая П-60x60 | 1200мм | RAL 9010 | Секция_А
```

---

## Конфигурация

`/opt/printserver/.env`:
```
PRINTER_DEV=/dev/usb/lp0
LABEL_WIDTH_MM=40
LABEL_HEIGHT_MM=57
LABEL_GAP_DOTS=26
```

После изменения:
```bash
systemctl restart printserver
```

---

## Деплой и обновление

### Первый деплой (на Orange Pi)
```bash
apt install -y python3-pip python3-venv git fonts-dejavu-core
git clone https://github.com/remixvit/printserver.git /opt/printserver
cd /opt/printserver
python3 -m venv venv
venv/bin/pip install -r requirements.txt
cp printserver.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now printserver
```

### Обновление кода
```bash
cd /opt/printserver && git pull && systemctl restart printserver
```

### Если включён overlayroot
```bash
overlayroot-chroot
cd /opt/printserver && git pull
exit
reboot
```

---

## Структура проекта

```
/opt/printserver/
├── app.py              # Flask сервер, роуты
├── epl.py              # EPL2 builder для /print (A-команды + GW для QR)
├── render.py           # Pillow renderer для /print-custom и /preview
├── config.py           # Конфиг из env vars
├── templates/
│   └── editor.html     # Веб-редактор этикеток
├── requirements.txt
├── .env                # Конфигурация (не в git*)
└── printserver.service # systemd unit
```

> *`.env` закоммичен с дефолтными значениями — безопасно для этого проекта.

---

## Диагностика

```bash
# Статус сервиса
systemctl status printserver

# Логи в реальном времени
journalctl -u printserver -f

# Проверить принтер
ls /dev/usb/lp*
lsusb | grep -i zebra

# Тест принтера (пустая этикетка)
printf "N\r\nP1\r\n" > /dev/usb/lp0

# Тест EPL текста
printf "N\r\nA50,50,0,3,1,1,N,\"TEST\"\r\nP1\r\n" > /dev/usb/lp0
```

---

## Защита SD карты (после финальной настройки)

```bash
apt install overlayroot
echo 'overlayroot="tmpfs"' >> /etc/overlayroot.conf
reboot
```

Для внесения изменений после включения overlayroot:
```bash
overlayroot-chroot   # временный доступ к реальной FS
# ... вносишь изменения ...
exit
reboot
```

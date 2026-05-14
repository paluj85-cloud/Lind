# Lind — Cline CLI Web Terminal

Веб-доступ к [Cline CLI](https://github.com/cline/cline) через [ttyd](https://github.com/tsl0922/ttyd) на `http://lind.adndexis.ru/cline` с HTTP Basic Auth.

## Архитектура

```
Браузер → Nginx (lind.adndexis.ru/cline) → Basic Auth → ttyd (localhost:7681) → Cline CLI
```

## Установка на VPS

```bash
# Клонировать репо
git clone https://github.com/paluj85-cloud/Lind.git /opt/lind

# Запустить установку
sudo bash /opt/lind/scripts/setup.sh
```

## Структура

```
Lind/
├── README.md
├── nginx/
│   └── lind.adndexis.ru.conf    # Nginx server block с WebSocket-прокси
├── systemd/
│   └── lind-ttyd.service        # systemd unit для ttyd + Cline CLI
└── scripts/
    └── setup.sh                 # Скрипт полной установки на VPS
```

## Компоненты

| Компонент | Путь | Порт |
|-----------|------|------|
| ttyd | `/usr/local/bin/ttyd` | 7681 (localhost) |
| Cline CLI | `/usr/bin/cline` (npm global) | — |
| Nginx | `/etc/nginx/sites-available/lind.adndexis.ru` | 80 |
| systemd | `/etc/systemd/system/lind-ttyd.service` | — |

## Управление

```bash
sudo systemctl status lind-ttyd    # Статус
sudo systemctl restart lind-ttyd   # Перезапуск
sudo journalctl -u lind-ttyd -f    # Логи
```

## Лицензия

MIT

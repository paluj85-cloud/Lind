# Prompt Template

Use this structure for EVERY generated prompt.

---

<role>
Linux-администратор / DevOps-инженер, работающий с tmux и systemd на VPS.
</role>

<task>
Сменить префикс tmux с F12 (не работает из-за перехвата браузером) на Ctrl+\ (C-\) и перезагрузить конфигурацию.
</task>

<context>
Текущая проблема: пользователь подключается к терминалу через ttyd (браузер → ttyd → cline_launcher.sh → tmux attach). Нажатие F12 перехватывается браузером для открытия DevTools, поэтому префикс F12 в tmux не работает.

Файлы для изменения:
- `/opt/lind/.tmux.conf` — конфигурация tmux (префикс, биндинги, resurrect)

Текущий конфиг `.tmux.conf` (строки 6-11):
```
set -g prefix F12
unbind C-b
unbind C-a
bind F12 send-prefix
```

Нужно заменить на:
```
set -g prefix C-\
unbind C-b
unbind C-a
bind C-\ send-prefix
```

После изменения файла нужно применить конфиг:
```
systemctl reload lind-tmux
```

Сервис: `lind-tmux.service`, запущен через systemd, tmux-сессия называется `lind`, сокет: `/opt/lind/tmux/default`.

Не трогать:
- Плагин tmux-resurrect
- Остальные настройки (mouse, history-limit, resurrect)
- Все остальные файлы проекта
</context>

<format>
Ожидаемый результат:
1. Файл `/opt/lind/.tmux.conf` изменён — префикс F12 заменён на C-\
2. Выполнен `systemctl reload lind-tmux`
3. Подтверждение, что перезагрузка прошла успешно (exit code 0)
4. Проверка: `tmux -S /opt/lind/tmux/default list-windows -t lind` — сессия жива
</format>

<constraints>
- НЕ менять другие настройки в `.tmux.conf`
- НЕ перезапускать сервис — только reload
- НЕ трогать другие файлы проекта
- НЕ удалять строки `unbind C-b` и `unbind C-a` — они должны остаться
- Проверить, что после reload сессия tmux всё ещё активна
</constraints>
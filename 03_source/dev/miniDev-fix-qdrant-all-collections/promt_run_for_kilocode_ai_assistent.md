# Запрос для запуска автоматического исправления коллекций Qdrant в удаленной DB и локальной

cd "miniDev-fix-qdrant-all-collections\python" && python -X utf8 check_and_fix.py --auto

## Проверим, что все коллекции теперь оптимизированы

cd "miniDev-fix-qdrant-all-collections\python" && python -X utf8 check_status.py

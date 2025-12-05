#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Скрипт для инициализации базы данных"""
import sys
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Добавляем текущую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import db

def main():
    print("=" * 60)
    print("Инициализация базы данных")
    print("=" * 60)
    
    try:
        # Проверяем подключение
        print("\n1. Проверка подключения к БД...")
        with db.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                version = cur.fetchone()[0]
                print(f"   ✓ Подключено: {version[:50]}...")
        
        # Создаём схему
        print("\n2. Создание схемы app...")
        count = db.create_schema("ddl.sql", demo_path=None)
        print(f"   ✓ Схема создана. Выполнено операторов: {count}")
        
        # Создаём админа из .env
        print("\n3. Создание администратора из .env...")
        admin = db.ensure_admin_from_env()
        if admin:
            print(f"   ✓ Администратор создан: {admin['login']}")
        else:
            print("   ⚠ Администратор не создан (проверьте ADMIN_LOGIN и ADMIN_PASSWORD в .env)")
        
        print("\n" + "=" * 60)
        print("✓ База данных успешно инициализирована!")
        print("=" * 60)
        print("\nТеперь можно запускать приложение:")
        print("  python mainApp.py")
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()


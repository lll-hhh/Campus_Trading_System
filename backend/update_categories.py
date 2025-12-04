#!/usr/bin/env python3
"""
Script to update category slugs in the database.
Run this inside the backend Docker container.
"""

import sys
import os
sys.path.append('/app')

from apps.core.database import get_session_scope
from apps.core.models import Category
from sqlalchemy import update, text

def update_category_slugs():
    # Assuming default database is 'sqlite' or adjust as needed
    with get_session_scope('sqlite') as session:
        category_updates = {
            '数码产品': 'electronics',
            '图书教材': 'books',
            '生活用品': 'daily',
            '运动器材': 'sports',
            '服装鞋包': 'fashion',
            '美妆护肤': 'beauty',
            '其他闲置': 'other'
        }

        try:
            for name, slug in category_updates.items():
                # Use raw SQL to avoid auto-update issues
                session.execute(
                    text("UPDATE categories SET slug = :slug WHERE name = :name"),
                    {"slug": slug, "name": name}
                )
                print(f"Updated slug for {name} -> {slug}")

            session.commit()
            print("All category slugs updated successfully!")
        except Exception as e:
            print(f"Error updating categories: {e}")
            session.rollback()

if __name__ == "__main__":
    update_category_slugs()
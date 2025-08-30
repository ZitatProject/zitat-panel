#!/usr/bin/env python3
"""
数据迁移脚本：将JSON文件迁移到SQLite数据库
"""

import os
import json
import sys
from database import db

def migrate_data():
    """执行数据迁移"""
    print("开始数据迁移...")
    
    # 检查JSON文件是否存在
    users_path = "db/users.json"
    sentences_path = "db/sentences.json"
    
    if not os.path.exists(users_path):
        print("警告: users.json 不存在，跳过用户数据迁移")
    else:
        with open(users_path, 'r', encoding='utf-8') as f:
            users_data = json.load(f)
        
        # 迁移用户数据
        for user in users_data:
            success = db.add_user(
                email=user['email'],
                password=user['password'],
                verified=user.get('verified', False)
            )
            if success:
                print(f"✓ 迁移用户: {user['email']}")
            else:
                print(f"⚠ 用户已存在: {user['email']}")
            
            # 迁移用户个人句子（从zitat字段）
            zitat_list = user.get('zitat', [])
            for sentence in zitat_list:
                db.add_sentence(
                    content=sentence['content'],
                    author=sentence['author'],
                    source=sentence['source'],
                    category=sentence['category'],
                    submitted_by=user['email'],
                    status='approved'
                )
                print(f"  ✓ 迁移句子: {sentence['content'][:20]}...")
    
    if not os.path.exists(sentences_path):
        print("警告: sentences.json 不存在，跳过句子数据迁移")
    else:
        with open(sentences_path, 'r', encoding='utf-8') as f:
            sentences_data = json.load(f)
        
        # 迁移全局句子数据
        for sentence in sentences_data:
            # 检查是否已存在（避免重复）
            existing = db.get_sentence_by_id(sentence['id'])
            if not existing:
                db.add_sentence(
                    content=sentence['content'],
                    author=sentence['author'],
                    source=sentence['source'],
                    category=sentence['category'],
                    submitted_by=sentence['submitted_by'],
                    status=sentence.get('status', 'approved')
                )
                print(f"✓ 迁移句子: {sentence['content'][:20]}...")
    
    print("数据迁移完成！")
    print("可以安全删除 users.json 和 sentences.json 文件")

if __name__ == "__main__":
    migrate_data()
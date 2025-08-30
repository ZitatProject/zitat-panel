#!/usr/bin/env python3
import sqlite3
import os

def check_database():
    db_path = 'app.db'
    if not os.path.exists(db_path):
        print("数据库文件不存在")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查句子表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sentences'")
        if not cursor.fetchone():
            print("句子表不存在")
            return
        
        # 查看所有句子ID
        cursor.execute("SELECT id FROM sentences")
        all_ids = [row[0] for row in cursor.fetchall()]
        print(f"数据库中的句子ID: {all_ids}")
        
        # 检查特定ID是否存在
        target_id = "1755075892964"
        cursor.execute("SELECT * FROM sentences WHERE id = ?", (target_id,))
        result = cursor.fetchone()
        
        if result:
            print(f"找到ID为{target_id}的句子:")
            print(f"ID: {result[0]}")
            print(f"内容: {result[1]}")
            print(f"作者: {result[2]}")
            print(f"来源: {result[3]}")
            print(f"分类: {result[4]}")
            print(f"提交者: {result[5]}")
            print(f"提交时间: {result[6]}")
            print(f"状态: {result[7]}")
            print(f"更新时间: {result[8]}")
        else:
            print(f"未找到ID为{target_id}的句子")
        
        # 查看数据库中的总记录数
        cursor.execute("SELECT COUNT(*) FROM sentences")
        count = cursor.fetchone()[0]
        print(f"数据库中共有 {count} 条记录")
        
        conn.close()
        
    except Exception as e:
        print(f"查询数据库时出错: {e}")

if __name__ == "__main__":
    check_database()
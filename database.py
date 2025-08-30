import sqlite3
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

class DatabaseManager:
    def __init__(self, db_path: str = None):
        if db_path is None:
            # 直接使用当前工作目录，避免权限问题
            self.db_path = os.path.join(os.getcwd(), 'app.db')
        else:
            self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库和表结构"""
        db_dir = os.path.dirname(self.db_path)
        
        # 确保目录存在
        try:
            os.makedirs(db_dir, exist_ok=True)
        except PermissionError:
            # 如果权限不足，使用当前目录
            print(f"警告：无法创建目录 {db_dir}，使用当前目录")
            self.db_path = os.path.join(os.getcwd(), "app.db")
        except Exception as e:
            print(f"创建目录时出错: {e}，使用当前目录")
            self.db_path = os.path.join(os.getcwd(), "app.db")
        
        # 确保数据库文件可访问
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 创建用户表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        email TEXT PRIMARY KEY,
                        password TEXT NOT NULL,
                        verified BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 创建句子表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sentences (
                        id TEXT PRIMARY KEY,
                        content TEXT NOT NULL,
                        author TEXT NOT NULL,
                        source TEXT NOT NULL,
                        category TEXT NOT NULL,
                        submitted_by TEXT NOT NULL,
                        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'pending',
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (submitted_by) REFERENCES users (email)
                    )
                ''')
                
                conn.commit()
                print(f"数据库初始化成功: {self.db_path}")
        except Exception as e:
            print(f"数据库初始化失败: {e}")
            raise
    
    def migrate_from_json(self):
        """从JSON文件迁移数据到SQLite"""
        # 迁移用户数据
        users_path = "db/users.json"
        if os.path.exists(users_path):
            with open(users_path, 'r', encoding='utf-8') as f:
                users_data = json.load(f)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                for user in users_data:
                    cursor.execute('''
                        INSERT OR IGNORE INTO users (email, password, verified)
                        VALUES (?, ?, ?)
                    ''', (user['email'], user['password'], user.get('verified', False)))
                conn.commit()
        
        # 迁移句子数据
        sentences_path = "db/sentences.json"
        if os.path.exists(sentences_path):
            with open(sentences_path, 'r', encoding='utf-8') as f:
                sentences_data = json.load(f)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                for sentence in sentences_data:
                    cursor.execute('''
                        INSERT OR IGNORE INTO sentences 
                        (id, content, author, source, category, submitted_by, submitted_at, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        sentence['id'],
                        sentence['content'],
                        sentence['author'],
                        sentence['source'],
                        sentence['category'],
                        sentence['submitted_by'],
                        sentence['submitted_at'],
                        sentence.get('status', 'approved')
                    ))
                conn.commit()
    
    # 用户相关操作
    def add_user(self, email: str, password: str, verified: bool = False) -> bool:
        """添加新用户"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO users (email, password, verified)
                    VALUES (?, ?, ?)
                ''', (email, password, verified))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False
    
    def get_user(self, email: str) -> Optional[Dict[str, Any]]:
        """获取用户信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            row = cursor.fetchone()
            if row:
                return {
                    'email': row[0],
                    'password': row[1],
                    'verified': bool(row[2]),
                    'created_at': row[3]
                }
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """根据邮箱获取用户信息（兼容旧接口）"""
        return self.get_user(email)
    
    def update_user_verification(self, email: str, verified: bool) -> bool:
        """更新用户验证状态"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET verified = ? WHERE email = ?', (verified, email))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """获取所有用户"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users')
            return [
                {
                    'email': row[0],
                    'password': row[1],
                    'verified': bool(row[2]),
                    'created_at': row[3]
                }
                for row in cursor.fetchall()
            ]
    
    # 句子相关操作
    def add_sentence(self, content: str, author: str, source: str, 
                    category: str, submitted_by: str, status: str = 'pending') -> str:
        """添加新句子"""
        sentence_id = str(int(datetime.now().timestamp() * 1000))
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sentences 
                (id, content, author, source, category, submitted_by, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (sentence_id, content, author, source, category, submitted_by, status))
            conn.commit()
            return sentence_id
    
    def get_sentence_by_id(self, sentence_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取句子"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM sentences WHERE id = ?', (sentence_id,))
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'content': row[1],
                    'author': row[2],
                    'source': row[3],
                    'category': row[4],
                    'submitted_by': row[5],
                    'submitted_at': row[6],
                    'status': row[7],
                    'updated_at': row[8]
                }
            return None
    
    def get_all_sentences(self) -> List[Dict[str, Any]]:
        """获取所有句子"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM sentences ORDER BY submitted_at DESC')
            return [
                {
                    'id': row[0],
                    'content': row[1],
                    'author': row[2],
                    'source': row[3],
                    'category': row[4],
                    'submitted_by': row[5],
                    'submitted_at': row[6],
                    'status': row[7],
                    'updated_at': row[8]
                }
                for row in cursor.fetchall()
            ]
    
    def get_user_sentences(self, user_email: str) -> List[Dict[str, Any]]:
        """获取用户的句子"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM sentences 
                WHERE submitted_by = ? 
                ORDER BY submitted_at DESC
            ''', (user_email,))
            return [
                {
                    'id': row[0],
                    'content': row[1],
                    'author': row[2],
                    'source': row[3],
                    'category': row[4],
                    'submitted_by': row[5],
                    'submitted_at': row[6],
                    'status': row[7],
                    'updated_at': row[8]
                }
                for row in cursor.fetchall()
            ]
    
    def update_sentence(self, sentence_id: str, content: str, author: str, 
                       source: str, category: str) -> bool:
        """更新句子"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE sentences 
                SET content = ?, author = ?, source = ?, category = ?, 
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (content, author, source, category, sentence_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_sentence(self, sentence_id: str) -> bool:
        """删除句子"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM sentences WHERE id = ?', (sentence_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def update_sentence_status(self, sentence_id: str, status: str) -> bool:
        """更新句子状态"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE sentences 
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status, sentence_id))
            conn.commit()
            return cursor.rowcount > 0

# 创建全局数据库实例
db = DatabaseManager()
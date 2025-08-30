import eel
import json
import hashlib
import os
import threading
import time
import requests
import random
import string
import smtplib
import base64
import signal
import sys
from urllib.parse import urlparse
from email.mime.text import MIMEText
from email.header import Header
from datetime import datetime, timedelta
import spark_ai
from database import db

# 配置文件路径
config_path = 'config.json'

# 读取配置文件
def read_config():
    if not os.path.exists(config_path):
        with open(config_path, 'w') as f:
            json.dump({'password_hash': ''}, f, indent=4)
        return {'password_hash': ''}
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# 保存配置文件
def save_config(config):
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

# 验证码存储字典和线程锁
verification_codes = {}
verification_lock = threading.Lock()

# 从配置文件中读取SMTP配置
def load_smtp_config():
    config = read_config()
    smtp_config = config.get('smtp_config', {})
    return {
        'smtp_server': smtp_config.get('smtp_server', 'smtp.qiye.163.com'),
        'smtp_port': smtp_config.get('smtp_port', 465),
        'sender': smtp_config.get('sender', 'qzgeek@zitat.cn'),
        'password': smtp_config.get('password', '')
    }

# SMTP连接全局变量
smtp_connection = None

smtp_config = load_smtp_config()

# 初始化SMTP连接函数
def init_smtp_connection():
    global smtp_connection
    try:
        smtp_server = smtp_config['smtp_server']
        smtp_port = smtp_config['smtp_port']
        sender = smtp_config['sender']
        password = smtp_config['password']
        
        smtp_connection = smtplib.SMTP_SSL(smtp_server, smtp_port)
        smtp_connection.set_debuglevel(1)  # 开启调试模式
        print(f"[INFO] 成功连接到SMTP服务器: {smtp_server}:{smtp_port}")

        smtp_connection.login(sender, password)
        print(f"[INFO] 成功登录邮箱: {sender}")
    except smtplib.SMTPAuthenticationError:
        print(f"[ERROR] 邮箱认证失败: 请检查用户名和密码/授权码是否正确")
    except smtplib.SMTPConnectError:
        print(f"[ERROR] 无法连接到SMTP服务器: {smtp_config['smtp_server']}:{smtp_config['smtp_port']}")
    except Exception as e:
        print(f"[ERROR] 初始化SMTP连接失败: {str(e)}")

# 关闭SMTP连接函数
def close_smtp_connection():
    global smtp_connection
    if smtp_connection:
        try:
            smtp_connection.quit()
            print(f"[INFO] SMTP连接已关闭")
        except Exception as e:
            if "please run connect() first" not in str(e):
                print(f"[ERROR] 关闭SMTP连接时发生错误: {str(e)}")
smtp_connection = None
# 初始化EEL
eel.init('web',js_result_timeout=-1)



# 加密密码
# 定义盐值
SALT = "zitat1145"

def encrypt_password(password):
    # 使用盐值进行密码加密
    return hashlib.sha256((password + SALT).encode()).hexdigest()

# 用户数据管理（已迁移到SQLite）
def load_users():
    """从数据库加载用户数据（兼容接口）"""
    return db.get_all_users()

def save_users(users):
    """保存用户数据到数据库（兼容接口）"""
    # 由于SQLite是实时操作，这个方法现在主要用于兼容
    return True

def generate_verification_code():
    """生成6位数字验证码"""
    return ''.join(random.choices(string.digits, k=6))

# 暴露函数给前端
def cleanup_verification_code(email):
    """3分钟后清理验证码"""
    with verification_lock:
        if email in verification_codes:
            del verification_codes[email]
            print(f"[INFO] 验证码已过期，自动清理: {email}")

@eel.expose
def send_verification_code(email):
    """发送验证码到邮箱并存储到字典"""
    verification_code = generate_verification_code()
    expiration_time = datetime.now() + timedelta(minutes=3)
    
    with verification_lock:
        # 存储邮箱、验证码和过期时间
        verification_codes[email] = {
            'code': verification_code,
            'expires_at': expiration_time
        }
    print(f"[INFO] 收到前端请求，现在发送验证码。验证码: {verification_code}")
    # 启动3分钟后自动清理的线程
    threading.Timer(180, cleanup_verification_code, args=[email]).start()
    
    # 发送邮件
    # 创建邮件内容
    subject = '一谚控制台验证码'
    message = f'您的验证码是: {verification_code}，有效期3分钟。'
    
    msg = MIMEText(message, 'plain', 'utf-8')
    msg['From'] = Header(smtp_config['sender'])
    msg['To'] = Header(email)
    msg['Subject'] = Header(subject)
    
    # 使用全局SMTP连接发送邮件
    try:
        global smtp_connection
        # 检查连接是否存在且活跃
        if not smtp_connection:
            print(f"[WARN] SMTP连接不存在，尝试重新连接...")
            init_smtp_connection()
            if not smtp_connection:
                raise Exception("无法建立SMTP连接")

        smtp_connection.sendmail(smtp_config['sender'], [email], msg.as_string())
        print(f"[INFO] 验证码已发送到邮箱: {email}, 验证码: {verification_code}")
        return {'status': 'success', 'message': '验证码已发送到您的邮箱'}
    except smtplib.SMTPAuthenticationError:
        print(f"[ERROR] 邮箱认证失败: 请检查用户名和密码/授权码是否正确")
        # 尝试重新连接
        init_smtp_connection()
        return {'status': 'error', 'message': '邮箱认证失败: 请检查用户名和密码/授权码是否正确'}
    except smtplib.SMTPConnectError:
        print(f"[ERROR] 无法连接到SMTP服务器: {smtp_config['smtp_server']}:{smtp_config['smtp_port']}")
        # 尝试重新连接
        init_smtp_connection()
        return {'status': 'error', 'message': f'无法连接到SMTP服务器: {smtp_server}:{smtp_port}'}
    except Exception as e:
        print(f"[ERROR] 发送验证码失败: {str(e)}")
        # 尝试重新连接
        init_smtp_connection()
        return {'status': 'error', 'message': f'发送验证码失败: {str(e)}'}
@eel.expose
def register_user(email, password):
    """注册新用户（使用SQLite数据库）"""
    if not password:
        return {'status': 'error', 'message': '密码不能为空'}
    
    print(f"[INFO] 开始注册用户: {email}")
    
    # 检查邮箱是否已注册
    existing_user = db.get_user_by_email(email)
    if existing_user:
        print(f"[WARN] 邮箱已被注册: {email}")
        return {'status': 'error', 'message': '邮箱已被注册'}
    
    # 加密密码
    hashed_password = encrypt_password(password)
    print(f"[DEBUG] 密码加密后: {hashed_password}")
    
    # 创建新用户
    new_user = {
        'email': email,
        'password': hashed_password,
        'verified': False,  # 初始设置为未验证
        'zitat': json.dumps([])  # 将语录存储字段转换为JSON字符串
    }
    
    try:
        user_id = db.add_user(new_user)
        print(f"[INFO] 新用户注册成功: {email}, ID: {user_id}")
        return {'status': 'success', 'message': '注册成功!'}
    except Exception as e:
        print(f"[ERROR] 注册用户失败: {str(e)}")
        return {'status': 'error', 'message': '注册失败，请稍后再试'}

@eel.expose
def verify_email(email, code):
    """验证邮箱验证码"""
    with verification_lock:
        # 检查邮箱是否存在于验证码字典中
        if email not in verification_codes:
            print(f"[WARN] 邮箱不存在或验证码已过期: {email}")
            return {'status': 'error', 'message': '邮箱不存在或验证码已过期'}
        
        # 检查验证码是否匹配
        stored_data = verification_codes[email]
        if stored_data['code'] != code:
            print(f"[WARN] 验证码不匹配: {email}")
            return {'status': 'error', 'message': '验证码不匹配'}
        
        # 检查是否过期
        if datetime.now() > stored_data['expires_at']:
            del verification_codes[email]
            print(f"[WARN] 验证码已过期: {email}")
            return {'status': 'error', 'message': '验证码已过期'}
        
        # 验证成功，删除验证码
        del verification_codes[email]
        print(f"[INFO] 验证码验证成功: {email}")
        
        # 更新用户状态
        users = load_users()
        user_found = False
        for user in users:
            if user['email'] == email:
                user['verified'] = True
                save_users(users)
                user_found = True
                break
        
        if not user_found:
            print(f"[WARN] 验证成功但未找到用户: {email}")
            return {'status': 'error', 'message': '验证成功但未找到用户！'}
        
        return {'status': 'success', 'message': '验证码验证成功！'}

@eel.expose
def login_user(email, password):
    """用户登录验证（使用SQLite数据库）"""
    try:
        hashed_password = encrypt_password(password)
        print(f"[INFO] 登录尝试: {email}")
        print(f"[DEBUG] 加密后的密码: {hashed_password}")
        
        user = db.get_user_by_email(email)
        if user:
            if user['password'] == hashed_password:
                if user['verified']:
                    login_manager.set_login_status(True, email)
                    print(f"[INFO] 用户 {email} 登录成功")
                    return {'status': 'success', 'message': '登录成功!'}
                else:
                    print(f"[WARN] 用户 {email} 邮箱未验证")
                    return {'status': 'error', 'message': '邮箱未验证!'}
            else:
                print(f"[WARN] 用户 {email} 密码错误")
                return {'status': 'error', 'message': '密码错误!'}
        else:
            print(f"[WARN] 用户 {email} 不存在")
            return {'status': 'error', 'message': '用户不存在!'}
    except Exception as e:
        print(f"[ERROR] 登录过程中发生错误: {str(e)}")
        return {'status': 'error', 'message': f'登录失败: {str(e)}'}

# 登录状态管理
class LoginManager:
    _instance = None
    _is_logged_in = False
    _current_user_email = ''
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(LoginManager, cls).__new__(cls)
        return cls._instance
    
    @property
    def is_logged_in(self):
        with self._lock:
            return self._is_logged_in
    
    @property
    def current_user_email(self):
        with self._lock:
            return self._current_user_email
    
    def set_login_status(self, status, email=None):
        with self._lock:
            self._is_logged_in = status
            # 仅在登录成功时设置邮箱
            if status and email:
                self._current_user_email = email
            elif not status:
                self._current_user_email = ''
            print(f"[INFO] 登录状态已设置为: {status}")
            return {'status': 'success', 'message': '登录状态已更新'}

# 创建登录管理器实例
login_manager = LoginManager()

# 从配置文件中读取API配置
def load_api_config():
    config = read_config()
    api_config = config.get('api_config', {})
    return {
        'ai_http_url': api_config.get('ai_http_url', 'https://spark-api-open.xf-yun.com/v1/chat/completions'),
        'api_key': api_config.get('api_key', ''),
        'api_secret': api_config.get('api_secret', '')
    }

# 加载API配置
api_config = load_api_config()

# 生成HTTP认证头部
def generate_auth_headers():
    timestamp = str(int(time.time()))
    nonce = str(int(time.time() * 1000))
    
    # 从配置中获取API密钥
    api_key = api_config['api_key']
    
    # 生成签名
    signature_origin = f"api_key={api_key}&timestamp={timestamp}&nonce={nonce}"
    signature = hashlib.md5(signature_origin.encode('utf-8')).hexdigest()
    
    return {
        'Content-Type': 'application/json',
        'api_key': api_key,
        'timestamp': timestamp,
        'nonce': nonce,
        'signature': signature
    }

# AI审核句子内容
def ai_review_sentence(content, author, source):
    # 构建提示词
    prompt = f"有人发来一条来自{author}的{source}中的句子，内容是{content}，请使用纯文本JSON的passed布尔值判定是否通过。"
    
    try:
        # 更新状态为审核中
        eel.status_update(3)
        eel.log_push('开始AI审核...')
        eel.sleep(0.1)  # 确保消息被发送
        
        # 调用spark_ai模块中的call_spark函数
        review_result = spark_ai.call_spark(prompt)
        # 过滤掉所有"`"符号和"json"字眼
        review_result = review_result.replace("`", "").replace("json", "")
        eel.log_push(f'AI返回过滤后结果: {review_result}')
        eel.sleep(0.1)  # 确保消息被发送
        
        # 解析JSON结果
        try:
            review_json = json.loads(review_result)
            eel.log_push('审核结果解析成功')
            eel.sleep(0.1)
            passed = review_json.get('passed', False)
            # 更新状态为成功或失败
            eel.status_update(1 if passed else 2)
            eel.sleep(0.1)
            return passed
        except json.JSONDecodeError:
            eel.log_push(f'JSON解析失败，原始响应: {review_result}')
            eel.sleep(0.1)
            eel.status_update(2)  # 解析失败也视为审核未通过
            eel.sleep(0.1)
            raise ValueError(f'AI返回结果不是有效的JSON: {review_result}')
    except Exception as e:
        print(f"[ERROR] AI审核请求失败: {str(e)}")
        raise

# 同步包装AI审核函数
def review_sentence_sync(content, author, source):
    try:
        return ai_review_sentence(content, author, source)
    except Exception as e:
        print(f"[ERROR] AI审核同步调用失败: {str(e)}")
        raise



# 设置登录状态函数
@eel.expose
def set_login_status(status, email=None):
    return login_manager.set_login_status(status, email)

# 获取登录状态函数
@eel.expose
def get_login_status():
    return {
        'status': 'success',
        'is_logged_in': login_manager.is_logged_in,
        'email': login_manager.current_user_email
    }

# 待审核数据现在通过文件传递，不再需要全局变量

@eel.expose
def add_sentence(source, content, author, category):
    if not login_manager.is_logged_in:
        return {'status': 'error', 'message': '请先登录'}
    
    # 获取当前登录用户
    users = load_users()
    current_user = next((u for u in users if u['email'] == login_manager.current_user_email), None)
    if not current_user:
        return {'status': 'error', 'message': '用户信息异常'}
    
    # 保存待审核的句子数据到文件
    pending_review_data = {
        'source': source,
        'content': content,
        'author': author,
        'category': category,
        'user_email': login_manager.current_user_email
    }
    
    # 将新提交的句子数据保存到pending_review.json文件
    try:
        with open('pending_review.json', 'w', encoding='utf-8') as f:
            json.dump(pending_review_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        return {'status': 'error', 'message': f'保存待审核数据失败: {str(e)}'}
    
    # 确保没有编辑待审核文件
    if os.path.exists('pending_edit.json'):
        try:
            os.remove('pending_edit.json')
        except Exception:
            pass  # 忽略删除失败的情况
    
    # 重定向到审核页面
    eel.js_redirect_to_processing()
    return {'status': 'redirect', 'message': '正在跳转到审核页面'}

@eel.expose
def start_ai_review():
    """在processing.html页面加载后开始AI审核"""
    global pending_review_data
    
    # 检查是添加还是编辑审核
    is_edit = False
    review_file = None
    
    if os.path.exists('pending_review.json'):
        review_file = 'pending_review.json'
        is_edit = False
    elif os.path.exists('pending_edit.json'):
        review_file = 'pending_edit.json'
        is_edit = True
    else:
        eel.log_push('没有找到待审核的句子数据')
        eel.status_update(2)
        return {'status': 'error', 'message': '没有找到待审核的句子数据'}
    
    # 读取待审核数据
    with open(review_file, 'r', encoding='utf-8') as f:
        review_data = json.load(f)
    
    source = review_data['source']
    content = review_data['content']
    author = review_data['author']
    category = review_data['category']
    action_type = "编辑" if is_edit else "添加"
    
    # AI审核句子内容
    try:
        eel.log_push(f'开始对{action_type}的句子进行AI审核...')
        eel.status_update(3)  # 设置状态为审核中
        eel.sleep(0.1)  # 确保消息被发送
        
        review_passed = review_sentence_sync(content, author, source)
        
        if review_passed:
            eel.log_push('审核通过!')
            eel.sleep(0.1)
            
            if is_edit:
                # 编辑操作：更新数据库
                try:
                    eel.log_push('正在更新句子...')
                    update_result = db.update_sentence(
                        review_data['id'],
                        source,
                        content,
                        author,
                        category
                    )
                    if update_result:  # 直接检查布尔值
                        eel.log_push('句子更新成功!')
                        eel.status_update(1)  # 设置状态为成功
                        eel.sleep(0.1)
                        # 删除待审核文件
                        try:
                            os.remove('pending_edit.json')
                        except Exception as e:
                            eel.log_push(f'警告: 无法删除待审核文件: {str(e)}')
                        return {'status': 'success', 'message': '句子编辑成功'}
                    else:
                        eel.log_push('更新失败: 句子不存在或数据库错误')
                        eel.status_update(2)
                        return {'status': 'error', 'message': '句子更新失败'}
                except Exception as e:
                    eel.log_push(f'更新失败: {str(e)}')
                    eel.status_update(2)
                    return {'status': 'error', 'message': str(e)}
            else:
                # 添加操作：保存到数据库
                try:
                    eel.log_push('正在保存句子...')
                    save_result = save_sentence_to_db(source, content, author, category, review_data['user_email'])
                    if save_result['status'] == 'success':
                        eel.log_push('句子保存成功!')
                        config = read_config()
                        requests.post(f'http://localhost:{config.get('api_port', 8000)}/admin', headers={'Content-Type': 'application/json','Authorization': f'Bearer {config.get('zitat_key')}'},json={'action':'refresh_cache'})
                        eel.log_push('缓存刷新完成！')
                        eel.status_update(1)  # 设置状态为成功
                        eel.sleep(0.1)
                        # 删除待审核文件
                        try:
                            os.remove('pending_review.json')
                        except Exception as e:
                            eel.log_push(f'警告: 无法删除待审核文件: {str(e)}')
                        return {'status': 'success', 'message': '句子添加成功'}
                    else:
                        eel.log_push(f'保存失败: {save_result["message"]}')
                        eel.status_update(2)
                        return {'status': 'error', 'message': save_result['message']}
                except Exception as e:
                    eel.log_push(f'保存失败: {str(e)}')
                    eel.status_update(2)
                    return {'status': 'error', 'message': str(e)}
        else:
            eel.log_push('审核未通过!')
            eel.sleep(0.1)
            eel.status_update(2)  # 设置状态为打回
            eel.sleep(0.1)
            return {'status': 'error', 'message': '句子内容未通过AI审核'}
    except Exception as e:
        eel.log_push(f'审核失败: {str(e)}')
        eel.sleep(0.1)
        eel.status_update(2)  # 设置状态为打回
        eel.sleep(0.1)
        return {'status': 'error', 'message': str(e)}

# 句子数据管理（已迁移到SQLite）
def load_sentences():
    """从数据库加载所有句子数据（兼容接口）"""
    return db.get_all_sentences()

def save_sentences(sentences):
    """保存句子数据到数据库（兼容接口）"""
    # 由于SQLite是实时操作，这个方法现在主要用于兼容
    return True

@eel.expose
def save_edit_for_review(edit_data):
    """保存编辑后的句子到待审核数据"""
    try:
        # 保存到待审核文件
        with open('pending_edit.json', 'w', encoding='utf-8') as f:
            json.dump(edit_data, f, ensure_ascii=False, indent=2)
        return {'status': 'success', 'message': '编辑数据已保存，等待AI审核'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@eel.expose
def save_sentence_to_db(source, content, author, category, user_email):
    """保存句子到SQLite数据库并同步到外部API"""
    try:
        sentence_data = {
            'content': content,
            'author': author,
            'source': source,
            'category': category,
            'submitted_by': user_email,
            'submitted_at': datetime.now().isoformat(),
            'status': 'approved'
        }
        
        # 使用数据库保存句子
        sentence_id = db.add_sentence(
            content=content,
            author=author,
            source=source,
            category=category,
            submitted_by=user_email,
            status='approved'
        )
        
        # 同步到外部API
        try:
            # 获取配置
            config = read_config()
            api_port = config.get('api_port', 8000)
            zitat_key = config.get('zitat_key', '')
            
            if zitat_key:  # 只有在配置了API密钥时才同步
                api_url = f"http://127.0.0.1:{api_port}/admin"
                request_data = {
                    "action": "add_hitokoto",
                    "hitokoto": content,
                    "from": source,
                    "type": category,
                    "from_who": author
                }
                
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {zitat_key}'
                }
                
                response = requests.post(
                    api_url,
                    headers=headers,
                    json=request_data,
                    timeout=30
                )
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        return {'status': 'success', 'message': '句子保存成功并已同步到API', 'id': sentence_id, 'uid': result.get('uid')}
        except Exception as api_error:
            print(f"[WARNING] 同步到外部API失败: {str(api_error)}")
            # 即使API同步失败，本地保存仍然成功
            pass
        
        return {'status': 'success', 'message': '句子保存成功', 'id': sentence_id}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@eel.expose
def get_user_sentences():
    """获取当前用户的句子（从SQLite数据库）"""
    try:
        if not login_manager.is_logged_in:
            return {'status': 'error', 'message': '请先登录'}
        
        sentences = db.get_user_sentences(login_manager.current_user_email)
        return {'status': 'success', 'sentences': sentences}
    
    except Exception as e:
        print(f"[ERROR] 获取用户句子失败: {str(e)}")
        return {'status': 'error', 'message': str(e)}

@eel.expose
def get_all_sentences():
    """从SQLite数据库获取所有句子"""
    try:
        sentences = db.get_all_sentences()
        return {'status': 'success', 'sentences': sentences}
    except Exception as e:
        print(f"[ERROR] 获取句子失败: {str(e)}")
        return {'status': 'error', 'message': str(e)}

@eel.expose
def delete_sentence(sentence_id):
    """使用SQLite数据库删除句子"""
    try:
        success = db.delete_sentence(sentence_id)
        if success:
            return {'status': 'success', 'message': '句子删除成功'}
        return {'status': 'error', 'message': '未找到句子'}
    except Exception as e:
        print(f"[ERROR] 删除句子失败: {str(e)}")
        return {'status': 'error', 'message': str(e)}

@eel.expose
def get_sentence_by_id(sentence_id):
    """从SQLite数据库根据ID获取句子"""
    try:
        sentence = db.get_sentence_by_id(sentence_id)
        if sentence:
            return {'status': 'success', 'data': sentence}
        return {'status': 'error', 'message': '未找到句子'}
    except Exception as e:
        print(f"[ERROR] 获取句子失败: {str(e)}")
        return {'status': 'error', 'message': str(e)}

@eel.expose
def update_sentence(id, source, content, author, category):
    """更新句子"""
    try:
        db = DatabaseManager()
        result = db.update_sentence(id, source, content, author, category)
        return result
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@eel.expose
def check_password_set():
    config = read_config()
    return config['password_hash'] != ''

@eel.expose
def get_api_config():
    """获取API配置信息"""
    config = read_config()
    return {
        'api_port': config.get('api_port', 8000),
        'zitat_key': config.get('zitat_key', '')
    }



# 定义一个函数来启动EEL
def start_eel():
    print(f"[INFO] 一谚控制台现已运行在 127.0.0.1:1146 上。")
    eel.start('index.html', mode=None, port=1146, block=True, close_callback=lambda *a: None)

# 定义一个函数来模拟持续访问EEL页面
def keep_alive():
    print(f"[INFO] 保活线程准备启动...")
    # 增加等待时间至5秒，确保EEL服务完全启动
    time.sleep(5)
    print(f"[INFO] 启动保活线程...")
    attempt = 0
    while True:
        try:
            # 延长超时时间至3秒
            response = requests.get('http://localhost:1146', timeout=3)
            print(f"[INFO] 保活请求状态码: {response.status_code} (尝试 #{attempt})")
            attempt = 0  # 重置尝试计数
        except requests.exceptions.ConnectionError as e:
            attempt += 1
            print(f"[WARN] 保活请求连接错误 (尝试 #{attempt}): {str(e)}")
        except requests.exceptions.Timeout as e:
            attempt += 1
            print(f"[WARN] 保活请求超时 (尝试 #{attempt}): {str(e)}")
        except Exception as e:
            attempt += 1
            print(f"[WARN] 保活请求失败 (尝试 #{attempt}): {str(e)}")
        # 每5秒访问一次
        time.sleep(5)

# 数据迁移：为用户数据中的句子添加id字段
def migrate_user_data():
    """迁移用户数据，为没有id的句子添加id"""
    users = load_users()
    updated = False
    
    for user in users:
        zitat = user.get('zitat', [])
        for i, sentence in enumerate(zitat):
            if 'id' not in sentence:
                sentence['id'] = i + 1
                updated = True
    
    if updated:
        save_users(users)
        print("[INFO] 用户数据迁移完成，已为句子添加id字段")

# 执行数据迁移
migrate_user_data()

# 初始化SMTP连接
print(f"[INFO] 初始化SMTP连接...")
init_smtp_connection()

# 启动EEL
print(f"[INFO] 准备启动一谚控制台...")
try:
    
    def signal_handler(sig, frame):
        print('\n[INFO] 收到退出信号，正在优雅关闭...')
        close_smtp_connection()
        sys.exit(0)
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    start_eel()
except KeyboardInterrupt:
    print('\n[INFO] 用户中断，正在关闭...')
finally:
    # 确保在应用退出时关闭SMTP连接
    close_smtp_connection()
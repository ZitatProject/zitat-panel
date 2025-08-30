// 使用代理模式隐藏eel已在auth_check.js中定义，这里直接使用

// 检查用户是否已登录
function checkLoginStatus() {
    // 从后端获取登录状态
    eel.get_login_status()(function(response) {
        if (response.status === 'error') {
            // 如果发生错误，跳转到登录页面
            window.location.href = 'index.html';
            return;
        }

        if (!response.is_logged_in) {
            // 如果未登录，跳转到登录页面
            window.location.href = 'index.html';
            return;
        }

        // 如果已登录，显示用户信息
        showUserInfo(response.email);
    });
}

// 显示用户信息
function showUserInfo(email) {
    // 创建用户信息元素
    const userInfo = document.createElement('div');
    userInfo.className = 'user-info';
    userInfo.textContent = `当前登录用户: ${email}`;

    // 添加到页面
    const loginContainer = document.querySelector('.login-container');
    loginContainer.insertBefore(userInfo, loginContainer.firstChild);
}

// 退出登录
function logout() {
    // 清除登录状态
    localStorage.removeItem('isLoggedIn');
    // 跳转到登录页面
    window.location.href = 'index.html';
}

// 添加句子
async function addSentence() {
    const source = document.getElementById('source').value.trim();
    const content = document.getElementById('content').value.trim();
    const author = document.getElementById('author').value.trim();
    const category = document.getElementById('category').value.trim();
    const messageElement = document.getElementById('message');

    // 重置消息样式
    messageElement.className = 'message';

    // 简单验证
    if (!source || !content || !author || !category) {
        messageElement.textContent = '所有字段都是必填的';
        messageElement.classList.add('error');
        return;
    }

    try {
        messageElement.textContent = '正在添加句子...';
        messageElement.classList.add('info');

        // 保存句子到待审核队列
        const result = await eel.add_sentence(
            source, content, author, category
        )();

        if (result.status === 'success') {
            messageElement.textContent = '句子添加成功！';
            messageElement.classList.add('success');
            
            // 清空表单
            document.getElementById('source').value = '';
            document.getElementById('content').value = '';
            document.getElementById('author').value = '';
            document.getElementById('category').value = '';
        } else {
            messageElement.textContent = '添加失败：' + (result.message || '未知错误');
            messageElement.classList.add('error');
        }
    } catch (error) {
        messageElement.textContent = '请求失败：' + error.message;
        messageElement.classList.add('error');
    }
}

// 供 Python 调用的重定向函数
eel.expose(js_redirect_to_processing, 'js_redirect_to_processing');
function js_redirect_to_processing() {
    window.location.href = 'processing.html';
}

// 页面加载时检查登录状态
document.addEventListener('DOMContentLoaded', checkLoginStatus);
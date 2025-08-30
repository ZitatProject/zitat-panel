// 统一的登录状态检查脚本
// 用于所有受保护页面的登录验证

// 使用代理模式隐藏eel，阻止控制台直接调用
const originalEel = window.eel;
window.eel = new Proxy(originalEel, {
    get: function(target, prop) {
        // 检查是否在控制台环境
        const stack = new Error().stack;
        if (stack && stack.includes('at eval')) {
            return undefined; // 控制台中返回undefined
        }
        return target[prop];
    }
});

// 统一的登录状态检查函数
function checkAuthStatus() {
    // 首先检查localStorage中的登录标记
    const isLoggedIn = localStorage.getItem('isLoggedIn');
    if (!isLoggedIn) {
        // 如果localStorage中没有登录标记，直接跳转
        window.location.href = 'index.html';
        return;
    }

    // 然后验证后端登录状态
    eel.check_password_set()(function(password_set) {
        if (!password_set) {
            // 如果密码未设置，跳转到初始化页面
            window.location.href = 'init.html';
            return;
        }

        // 验证后端登录状态
        eel.get_login_status()(function(response) {
            if (response.status === 'error' || !response.is_logged_in) {
                // 如果后端验证失败，清除本地存储并跳转
                localStorage.removeItem('isLoggedIn');
                window.location.href = 'index.html';
                return;
            }

            // 验证通过，可以正常加载页面内容
            // 这里可以添加额外的初始化逻辑
            if (typeof onAuthSuccess === 'function') {
                onAuthSuccess(response);
            }
        });
    });
}

// 统一的退出登录函数
function logout() {
    // 清除登录状态
    localStorage.removeItem('isLoggedIn');
    // 跳转到登录页面
    window.location.href = 'index.html';
}

// 页面加载时自动检查登录状态
document.addEventListener('DOMContentLoaded', checkAuthStatus);
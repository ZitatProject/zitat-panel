function setPassword() {
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirm_password').value;

    if (password !== confirmPassword) {
        showToast('两次输入的密码不一致！', 'error');
        return;
    }

    if (password.length < 6) {
        showToast('密码长度不能少于6位！', 'error');
        return;
    }

    eel.set_initial_password(password);
}

// 暴露给Python调用的函数
eel.expose(navigate_to_login);
function navigate_to_login() {
    window.location.href = 'index.html';
}

// 暴露redirect_to_processing给Python调用
eel.expose(redirect_to_processing);
function redirect_to_processing() {
    window.location.href = 'processing.html';
}

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
// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 为按钮添加点击事件
    if (eel.anti_reset() === true) {
        log("AWA")
        window.location.href = 'index.html'
    }
    document.querySelector('.btn-set-password').addEventListener('click', setPassword);
});
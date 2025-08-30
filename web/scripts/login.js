// 用户注册功能
async function register() {
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    const confirmPassword = document.getElementById('register-confirm-password').value;
    const code = document.getElementById('verification-code').value;
    
    // 检查邮箱格式
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        showToast('请输入有效的邮箱地址', 'error');
        return;
    }
    
    // 检查密码强度
    if (password.length < 6) {
        showToast('密码长度至少为6位', 'error');
        return;
    }
    
    // 检查SessionEmail
    if (SessionEmail !== email) {
        showToast('请先发送验证码', 'warning');
        return;
    }
    
    // 检查密码是否一致
    if (password !== confirmPassword) {
        showToast('两次输入的密码不一致', 'error');
        return;
    }
    
    // 检查验证码是否填写
    const verificationSection = document.getElementById('verification-section');
    if (verificationSection && verificationSection.style.display === 'block' && !code) {
        showToast('请输入验证码', 'error');
        return;
    }
    
    try {
        // 先注册用户
        console.log('注册用户请求已触发，邮箱:', email);
        const result = await eel.register_user(email, password)();
        console.log('注册结果:', result);
        if (result.status !== 'success') {
            showToastFromResponse(result);
            return;
        }
        
        // 再验证验证码
        console.log('验证验证码请求已触发，邮箱:', SessionEmail, '验证码:', code);
        const verifyResult = await eel.verify_email(SessionEmail, code)();
        console.log('验证码验证结果:', verifyResult);
        if (verifyResult.status === 'success') {
            showToast('注册成功！请登录', 'success');
            verificationSection.style.display = 'none';
            document.getElementById('register-form').reset();
            SessionEmail = null; // 重置SessionEmail
            // 切换到登录表单
            document.getElementById('login-tab').click();
        } else {
            showToastFromResponse(verifyResult);
        }
    } catch (error) {
        console.error('注册失败:', error);
        showToast('注册失败，请重试', 'error');
    }
}

// 邮箱验证功能已整合到注册和登录流程中，此函数不再使用
// async function verifyEmail() {
//     const email = document.getElementById('register-email').value;
//     const code = document.getElementById('verification-code').value;
//     
//     try {
//         const verifyResult = await eel.verify_email(email, code)();
//         if (verifyResult.status === 'success') {
//             alert('邮箱验证成功！请登录');
//             document.getElementById('verification-section').style.display = 'none';
//             document.getElementById('register-form').reset();
//         } else {
//             showToast(verifyResult.message, 'error');
//         }
//     } catch (error) {
//         console.error('验证失败:', error);
//         alert('验证失败，请重试');
//     }
// }

// 用户登录功能
async function login() {
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    
    // 检查邮箱格式
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        showToast('请输入有效的邮箱地址', 'error');
        return;
    }
    
    // 检查密码是否填写
    if (!password) {
        showToast('请输入密码', 'error');
        return;
    }
    
    try {
        // 直接登录，无需验证码验证
        console.log('登录请求已触发，邮箱:', email);
        const result = await eel.login_user(email, password)();
        console.log('登录结果:', result);
        if (result.status === 'success') {
            showToast('登录成功！', 'success');
            // 登录状态已在后端设置，无需前端重复设置
            localStorage.setItem('isLoggedIn', 'true');
            window.location.href = 'panel.html';
        } else {
            showToastFromResponse(result);
        }
    } catch (error) {
        console.error('登录失败:', error);
        showToast('登录失败，请重试', 'error');
    }
}

// 倒计时功能
function startCountdown(btnId) {
    const sendBtn = document.getElementById(btnId);
    let countdown = 60;
    sendBtn.disabled = true;
    sendBtn.textContent = `重新发送(${countdown}s)`;
    
    const interval = setInterval(() => {
        countdown--;
        sendBtn.textContent = `重新发送(${countdown}s)`;
        
        if (countdown <= 0) {
            clearInterval(interval);
            sendBtn.disabled = false;
            sendBtn.textContent = '发送验证码';
        }
    }, 1000);
}

// 发送验证码
let SessionEmail = null;

async function sendVerificationCode(btnId, emailFieldId) {
    const email = document.getElementById(emailFieldId).value;
    if (!email) {
        showToast('请先输入邮箱', 'error');
        return;
    }
    
    // 简单的邮箱格式验证
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        showToast('请输入有效的邮箱地址', 'error');
        return;
    }
    
    // 存储邮箱到SessionEmail
    SessionEmail = email;
    console.log('发送验证码请求已触发，邮箱:', email); // 调试日志
    
    try {
        const result = await eel.send_verification_code(email)();
        console.log('发送验证码结果:', result); // 调试日志
        showToastFromResponse(result);
        if (result.status === 'success') {
            startCountdown(btnId);
            // 根据不同的emailFieldId显示对应的验证码区域
            if (emailFieldId === 'register-email') {
                const verificationSection = document.getElementById('verification-section');
                if (verificationSection) {
                    verificationSection.style.display = 'block';
                } else {
                    console.warn('未找到注册验证码区域元素');
                }
            } else if (emailFieldId === 'login-email') {
                const loginVerificationSection = document.getElementById('login-verification-section');
                if (loginVerificationSection) {
                    loginVerificationSection.style.display = 'block';
                } else {
                    console.warn('未找到登录验证码区域元素');
                }
            }
        }
    } catch (error) {
        console.error('发送验证码失败:', error);
        showToast('发送验证码失败，请重试', 'error');
    }
}

// 绑定表单提交事件

document.addEventListener('DOMContentLoaded', () => {
    // 注册相关事件
    document.getElementById('register-btn').addEventListener('click', register);
    const registerSendBtn = document.getElementById('send-code-btn');
    if (registerSendBtn) {
        registerSendBtn.addEventListener('click', () => sendVerificationCode('send-code-btn', 'register-email'));
    }
    
    // 登录相关事件
    document.getElementById('login-btn').addEventListener('click', login);
});
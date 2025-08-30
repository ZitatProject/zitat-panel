// Toast 弹窗组件
class Toast {
    constructor() {
        this.container = null;
        this.createContainer();
    }

    createContainer() {
        if (this.container) return;
        
        this.container = document.createElement('div');
        this.container.id = 'toast-container';
        this.container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            pointer-events: none;
        `;
        document.body.appendChild(this.container);
    }

    show(message, type = 'info', duration = 3000) {
        const kaomojis = {
            success: ['(≧▽≦)', '(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧', '٩(◕‿◕)۶', '(ﾉ´ヮ`)ﾉ*: ･ﾟ✧', '(≧◡≦)'],
            error: ['(╯°□°）╯︵ ┻━┻', '(ಥ﹏ಥ)', '(╥﹏╥)', '(；д；)', '(´；ω；`)'],
            warning: ['(￣ω￣;)', '(・・;)ゞ', '(￣ー￣;)', '(＠_＠;)', '(・_・;)'],
            info: ['(｡･ω･｡)', '(◕‿◕)', '(｀・ω・´)', '(＾◡＾)', '(≧∇≦)']
        };
        
        const kaomojiList = kaomojis[type] || kaomojis.info;
        const randomKaomoji = kaomojiList[Math.floor(Math.random() * kaomojiList.length)];
        const messageWithKaomoji = `${randomKaomoji} ${message}`;
        
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.style.cssText = `
            background: ${this.getBackgroundColor(type)};
            color: white;
            padding: 12px 20px;
            margin-bottom: 10px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            font-size: 14px;
            max-width: 300px;
            word-wrap: break-word;
            opacity: 0;
            transform: translateX(100%);
            transition: all 0.3s ease;
            pointer-events: auto;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        `;
        
        toast.textContent = messageWithKaomoji;
        
        this.container.appendChild(toast);
        
        // 触发重排以确保动画生效
        toast.offsetHeight;
        
        // 淡入动画
        setTimeout(() => {
            toast.style.opacity = '1';
            toast.style.transform = 'translateX(0)';
        }, 10);
        
        // 自动移除
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, duration);
    }

    getBackgroundColor(type) {
        const colors = {
            success: '#4caf50',
            error: '#f44336',
            warning: '#ff9800',
            info: '#2196f3'
        };
        return colors[type] || colors.info;
    }
}

// 创建全局实例
const toast = new Toast();

// 全局函数
function showToast(message, type = 'info', duration = 3000) {
    toast.show(message, type, duration);
}

// 智能包装函数：根据EEL返回对象自动决定Toast颜色
function showToastFromResponse(response, duration = 3000) {
    if (typeof response === 'object' && response !== null) {
        const status = response.status || response.success;
        const message = response.message || '操作完成';
        
        let type = 'info';
        if (status === 'success' || status === true) {
            type = 'success';
        } else if (status === 'error' || status === false) {
            type = 'error';
        } else if (status === 'warning') {
            type = 'warning';
        }
        
        toast.show(message, type, duration);
    } else {
        // 如果不是对象，直接显示为info类型
        toast.show(String(response), 'info', duration);
    }
}
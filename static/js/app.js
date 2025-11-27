// static/js/app.js

// 配置 Axios 全局默认值
axios.defaults.baseURL = '/api/'; // 之后请求只需写 'items/' 而不用写全路径
axios.defaults.timeout = 5000;

// 自动获取 Django 的 CSRF Cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');
// 将 Token 放入 Axios Header
if (csrftoken) {
    axios.defaults.headers.common['X-CSRFToken'] = csrftoken;
}

// 简单的 Vue 全局混入，用于处理时间格式化等
const commonMixin = {
    methods: {
        formatDate(dateStr) {
            if (!dateStr) return '';
            return new Date(dateStr).toLocaleString();
        },
        // 图片路径处理：如果没有 http 开头，加上 /media/
        fixImageUrl(path) {
            if (!path) return '/static/img/no-image.png'; // 需准备一张默认图
            if (path.startsWith('http')) return path;
            return '/media/' + path;
        }
    }
};
import axios from 'axios'
import Cookies from 'js-cookie'

const api = axios.create({
    baseURL: process.env.VUE_APP_API_BASE_URL,
    withCredentials: true,
    xsrfCookieName: 'csrftoken',
    xsrfHeaderName: 'X-CSRFToken',
})

api.interceptors.request.use((config) => {
    const csrfToken = Cookies.get('csrftoken')
    if (csrfToken) {
        config.headers['X-CSRFToken'] = csrfToken
    }
    return config
})

export default api

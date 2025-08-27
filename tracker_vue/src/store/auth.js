import { defineStore } from 'pinia'
import Cookies from 'js-cookie'
export const useAuthStore = defineStore('auth', {
    state: () => {
        const storedState = localStorage.getItem('authState')
        return storedState
            ? JSON.parse(storedState)
            : {
                user: null,
                isAuthenticated: false,
            }
    },
    actions: {
        async setCsrfToken() {
            await fetch(`${process.env.VUE_APP_API_BASE_URL}/set-csrf-token`, {
                method: 'GET',
                credentials: 'include',
            })
        },

        async login(email, password, router = null) {
            const response = await fetch(`${process.env.VUE_APP_API_BASE_URL}/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': Cookies.get('csrftoken'),
                },
                body: JSON.stringify({
                    email,
                    password,
                }),
                credentials: 'include',
            })
            const data = await response.json()
            if (data.success) {
                this.isAuthenticated = true
                this.saveState()
                if (router) {
                    await router.push({
                        name: 'home',
                    })
                }
            } else {
                this.user = null
                this.isAuthenticated = false
                this.saveState()
            }
        },

        async logout(router = null) {
            try {
                const response = await fetch(`${process.env.VUE_APP_API_BASE_URL}/logout`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': Cookies.get('csrftoken'),
                    },
                    credentials: 'include',
                })
                if (response.ok) {
                    this.user = null
                    this.isAuthenticated = false
                    this.saveState()
                    if (router) {
                        await router.push({
                            name: 'login',
                        })
                    }
                }
            } catch (error) {
                console.error('Logout failed', error)
                throw error
            }
        },

        async fetchUser() {
            try {
                const response = await fetch(`${process.env.VUE_APP_API_BASE_URL}/user`, {
                    credentials: 'include',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': Cookies.get('csrftoken'),
                    },
                })
                if (response.ok) {
                    const data = await response.json()
                    this.user = data
                    this.isAuthenticated = true
                } else {
                    this.user = null
                    this.isAuthenticated = false
                }
            } catch (error) {
                console.error('Failed to fetch user', error)
                this.user = null
                this.isAuthenticated = false
            }
            this.saveState()
        },

        saveState() {
            /*
                  We save state to local storage to keep the
                  state when the user reloads the page.
       
                  This is a simple way to persist state. For a more robust solution,
                  use pinia-persistent-state.
                   */
            localStorage.setItem(
                'authState',
                JSON.stringify({
                    user: this.user,
                    isAuthenticated: this.isAuthenticated,
                }),
            )
        },
    },
})

// export function getCSRFToken() {
//     // let cookieValue = null;
//     // if (document.cookie && document.cookie !== '') {
//     //     const cookies = document.cookie.split(';');
//     //     for (let i = 0; i < cookies.length; i++) {
//     //         const cookie = cookies[i].trim();
//     //         // Does this cookie string begin with the name we want?
//     //         if (cookie.substring(0, name.length + 1) === (name + '=')) {
//     //             cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
//     //             break;
//     //         }
//     //     }
//     // }
//     // console.log("CSRF Token:", cookieValue);
//     // return cookieValue;

    
// }
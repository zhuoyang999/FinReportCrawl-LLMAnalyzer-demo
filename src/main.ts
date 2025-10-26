import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

// Bootstrap styles & JS
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap-icons/font/bootstrap-icons.css'
import 'bootstrap/dist/js/bootstrap.bundle.min.js'
import './styles/theme.css'

import ElementPlus from 'element-plus'

const app = createApp(App)
app.use(router)
app.use(ElementPlus)
app.mount('#app')

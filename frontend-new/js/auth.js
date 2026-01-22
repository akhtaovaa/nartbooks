/**
 * Модуль авторизации для входа в систему
 */

let currentEmail = null;
let currentPhone = null;
let resendTimer = null;
let timerInterval = null;

/**
 * Сохранение токена в localStorage
 */
function saveToken(token) {
    localStorage.setItem('auth_token', token);
}

/**
 * Получение токена из localStorage
 */
function getToken() {
    return localStorage.getItem('auth_token');
}

/**
 * Удаление токена
 */
function removeToken() {
    localStorage.removeItem('auth_token');
}

/**
 * Показать сообщение
 */
function showMessage(elementId, message, type = 'error') {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    element.textContent = message;
    element.className = `form-message ${type}`;
    element.classList.remove('hidden');
}

/**
 * Скрыть сообщение
 */
function hideMessage(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.classList.add('hidden');
    }
}

/**
 * Запуск таймера для повторной отправки
 */
function startResendTimer() {
    let seconds = 60;
    const timerEl = document.getElementById('timer');
    const resendBtn = document.getElementById('resendCodeBtn');
    
    if (timerEl) {
        timerEl.textContent = `Можно отправить код повторно через ${seconds} секунд`;
        timerEl.classList.remove('hidden');
    }
    
    if (resendBtn) {
        resendBtn.style.display = 'none';
    }
    
    timerInterval = setInterval(() => {
        seconds--;
        if (timerEl) {
            timerEl.textContent = `Можно отправить код повторно через ${seconds} секунд`;
        }
        
        if (seconds <= 0) {
            clearInterval(timerInterval);
            if (timerEl) {
                timerEl.classList.add('hidden');
            }
            if (resendBtn) {
                resendBtn.style.display = 'block';
            }
        }
    }, 1000);
}

/**
 * Остановка таймера
 */
function stopResendTimer() {
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
    const timerEl = document.getElementById('timer');
    if (timerEl) {
        timerEl.classList.add('hidden');
    }
}

/**
 * Отправка кода верификации
 */
async function sendCode() {
    // Проверка наличия API
    if (!window.api || !window.api.sendAuthCode) {
        showMessage('sendStatus', 'Ошибка: API не загружен. Обновите страницу.', 'error');
        console.error('window.api.sendAuthCode не найдена. Доступные функции:', window.api ? Object.keys(window.api) : 'window.api не определен');
        return;
    }
    
    const emailInput = document.getElementById('emailInput');
    const phoneInput = document.getElementById('phoneInput');
    const sendBtn = document.getElementById('sendCodeBtn');
    const btnText = sendBtn.querySelector('.btn-text');
    const btnSpinner = sendBtn.querySelector('.btn-spinner');
    
    const email = emailInput ? emailInput.value.trim() : '';
    const phone = phoneInput ? phoneInput.value.trim() : '';
    
    // Валидация
    if (!email && !phone) {
        showMessage('sendStatus', 'Укажите email или телефон', 'error');
        return;
    }
    
    // Очистка предыдущих сообщений
    hideMessage('sendStatus');
    sendBtn.disabled = true;
    btnText.textContent = 'Отправляем...';
    btnSpinner.classList.remove('hidden');
    
    try {
        const data = {};
        if (email) {
            data.email = email;
            currentEmail = email;
            currentPhone = null;
        } else {
            data.phone = phone;
            currentPhone = phone;
            currentEmail = null;
        }
        
        const response = await window.api.sendAuthCode(data);
        
        // Проверяем, включен ли режим разработки
        if (response.dev_mode && response.code) {
            // Режим разработки - показываем код крупно и заметно
            const codeMessage = document.getElementById('codeMessage');
            const devCodeBlock = document.getElementById('devCodeBlock');
            const devCodeDisplay = document.getElementById('devCodeDisplay');
            
            if (codeMessage) {
                codeMessage.innerHTML = '<strong>⚠️ Режим разработки</strong><br>Сервис отправки недоступен. Используйте код ниже:';
                codeMessage.className = 'form-message';
                codeMessage.style.background = '#fff3cd';
                codeMessage.style.borderColor = '#ffc107';
                codeMessage.style.color = '#856404';
            }
            
            if (devCodeBlock && devCodeDisplay) {
                devCodeDisplay.textContent = response.code;
                devCodeBlock.style.display = 'block';
            }
            
            // Автоматически заполняем поле кода
            const codeInput = document.getElementById('codeInput');
            if (codeInput) {
                codeInput.value = response.code;
                // Выделяем код для удобства копирования
                setTimeout(() => {
                    codeInput.select();
                }, 100);
            }
            
            // Показываем сообщение в статусе
            showMessage('sendStatus', `Код создан: ${response.code}`, 'success');
        } else {
            // Обычный режим - код отправлен
            showMessage('sendStatus', '✅ Код отправлен. Проверьте почту или телефон.', 'success');
            
            // Скрываем блок режима разработки, если он был показан
            const devCodeBlock = document.getElementById('devCodeBlock');
            if (devCodeBlock) {
                devCodeBlock.style.display = 'none';
            }
        }
        
        // Переход к шагу ввода кода
        document.getElementById('stepSend').classList.add('hidden');
        document.getElementById('stepVerify').classList.remove('hidden');
        
        // Фокус на поле ввода кода
        setTimeout(() => {
            const codeInput = document.getElementById('codeInput');
            if (codeInput) {
                if (!response.dev_mode || !response.code) {
                    codeInput.value = '';
                }
                codeInput.focus();
            }
        }, 100);
        
        // Запуск таймера
        startResendTimer();
        
    } catch (error) {
        showMessage('sendStatus', `Ошибка: ${error.message}`, 'error');
    } finally {
        sendBtn.disabled = false;
        btnText.textContent = 'Отправить код';
        btnSpinner.classList.add('hidden');
    }
}

/**
 * Верификация кода
 */
async function verifyCode() {
    // Проверка наличия API
    if (!window.api || !window.api.verifyAuthCode) {
        showMessage('verifyStatus', 'Ошибка: API не загружен. Обновите страницу.', 'error');
        console.error('window.api.verifyAuthCode не найдена. Доступные функции:', window.api ? Object.keys(window.api) : 'window.api не определен');
        return;
    }
    
    const codeInput = document.getElementById('codeInput');
    const verifyBtn = document.getElementById('verifyCodeBtn');
    const btnText = verifyBtn.querySelector('.btn-text');
    const btnSpinner = verifyBtn.querySelector('.btn-spinner');
    
    const code = codeInput ? codeInput.value.trim() : '';
    
    // Валидация
    if (!code) {
        showMessage('verifyStatus', 'Введите код подтверждения', 'error');
        return;
    }
    
    if (!currentEmail && !currentPhone) {
        showMessage('verifyStatus', 'Ошибка: не указан email или телефон', 'error');
        return;
    }
    
    // Очистка предыдущих сообщений
    hideMessage('verifyStatus');
    verifyBtn.disabled = true;
    btnText.textContent = 'Проверяем...';
    btnSpinner.classList.remove('hidden');
    
    try {
        const data = { code };
        if (currentEmail) {
            data.email = currentEmail;
        } else {
            data.phone = currentPhone;
        }
        
        const response = await window.api.verifyAuthCode(data);
        
        if (response.access_token) {
            // Сохраняем токен
            const token = response.access_token;
            saveToken(token);
            
            // Проверяем, что токен действительно сохранился
            const savedToken = localStorage.getItem('auth_token');
            if (!savedToken || savedToken !== token) {
                console.error('Ошибка: токен не сохранился в localStorage');
                showMessage('verifyStatus', 'Ошибка: не удалось сохранить токен', 'error');
                return;
            }
            
            console.log('Токен успешно сохранен:', savedToken.substring(0, 20) + '...');
            
            showMessage('verifyStatus', '✅ Авторизация успешна! Перенаправляем...', 'success');
            
            // Останавливаем таймер
            stopResendTimer();
            
            // Перенаправление
            setTimeout(() => {
                // Проверяем, откуда пришли (может быть редирект с admin.html)
                const urlParams = new URLSearchParams(window.location.search);
                let redirect = urlParams.get('redirect') || 'index.html';
                
                // Если редирект указан как путь без расширения, добавляем .html
                if (redirect && !redirect.includes('.')) {
                    redirect = redirect + '.html';
                }
                
                // Убеждаемся, что токен всё ещё есть перед редиректом
                const tokenBeforeRedirect = localStorage.getItem('auth_token');
                if (!tokenBeforeRedirect) {
                    console.error('Токен пропал перед редиректом!');
                    showMessage('verifyStatus', 'Ошибка: токен был потерян', 'error');
                    return;
                }
                
                console.log('Перенаправление на:', redirect);
                window.location.href = redirect;
            }, 1000);
        } else {
            showMessage('verifyStatus', 'Ошибка: токен не получен', 'error');
            console.error('Ответ от сервера не содержит access_token:', response);
        }
    } catch (error) {
        showMessage('verifyStatus', `Ошибка: ${error.message}`, 'error');
    } finally {
        verifyBtn.disabled = false;
        btnText.textContent = 'Подтвердить код';
        btnSpinner.classList.add('hidden');
    }
}

/**
 * Повторная отправка кода
 */
async function resendCode() {
    const resendBtn = document.getElementById('resendCodeBtn');
    if (resendBtn) {
        resendBtn.disabled = true;
        resendBtn.textContent = 'Отправляем...';
    }
    
    stopResendTimer();
    await sendCode();
    
    if (resendBtn) {
        resendBtn.disabled = false;
        resendBtn.textContent = 'Отправить код повторно';
    }
}

/**
 * Инициализация формы авторизации
 */
function initAuth() {
    // Обработчик отправки кода
    const sendBtn = document.getElementById('sendCodeBtn');
    if (sendBtn) {
        sendBtn.addEventListener('click', sendCode);
    }
    
    // Обработчик верификации кода
    const verifyBtn = document.getElementById('verifyCodeBtn');
    if (verifyBtn) {
        verifyBtn.addEventListener('click', verifyCode);
    }
    
    // Обработчик повторной отправки
    const resendBtn = document.getElementById('resendCodeBtn');
    if (resendBtn) {
        resendBtn.addEventListener('click', resendCode);
    }
    
    // Ввод кода по Enter
    const codeInput = document.getElementById('codeInput');
    if (codeInput) {
        codeInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                verifyCode();
            }
        });
    }
    
    // Ввод email/телефона по Enter
    const emailInput = document.getElementById('emailInput');
    const phoneInput = document.getElementById('phoneInput');
    
    if (emailInput) {
        emailInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendCode();
            }
        });
    }
    
    if (phoneInput) {
        phoneInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendCode();
            }
        });
    }
}

// Проверка готовности API перед инициализацией
function waitForAPI() {
    if (window.api && window.api.sendAuthCode && window.api.verifyAuthCode) {
        initAuth();
    } else {
        // Ждём немного и проверяем снова
        setTimeout(waitForAPI, 100);
    }
}

// Запуск инициализации
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', waitForAPI);
} else {
    waitForAPI();
}

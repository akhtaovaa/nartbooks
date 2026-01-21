/**
 * Модуль для обработки формы регистрации
 * Включает валидацию и отправку данных
 */

/**
 * Валидация email
 * @param {string} email - email для проверки
 * @returns {boolean} - валидный ли email
 */
function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * Разделяет имя на first_name и last_name
 * @param {string} fullName - полное имя
 * @returns {Object} - объект с first_name и last_name
 */
function splitName(fullName) {
    const trimmed = fullName.trim();
    const parts = trimmed.split(/\s+/);
    
    if (parts.length === 0) {
        return { first_name: '', last_name: '' };
    }
    
    if (parts.length === 1) {
        return { first_name: parts[0], last_name: '' };
    }
    
    // Первое слово - имя, остальное - фамилия
    const first_name = parts[0];
    const last_name = parts.slice(1).join(' ');
    
    return { first_name, last_name };
}

/**
 * Собирает значения из группы полей (например, три жанра)
 * @param {string} prefix - префикс имени полей (например, 'genre')
 * @returns {Array<string>} - массив значений
 */
function collectFieldGroup(prefix) {
    const values = [];
    for (let i = 1; i <= 3; i++) {
        const field = document.querySelector(`input[name="${prefix}${i}"]`);
        if (field) {
            const value = field.value.trim();
            if (value) {
                values.push(value);
            }
        }
    }
    return values;
}

/**
 * Валидация поля формы
 * @param {HTMLElement} field - поле для валидации
 * @returns {boolean} - валидно ли поле
 */
function validateField(field) {
    const fieldContainer = field.closest('.form-field');
    const errorElement = fieldContainer.querySelector('.field-error');
    
    // Убираем предыдущие ошибки
    fieldContainer.classList.remove('error');
    if (errorElement) {
        errorElement.textContent = '';
    }
    
    // Проверка на пустое поле
    if (field.hasAttribute('required') && !field.value.trim()) {
        fieldContainer.classList.add('error');
        if (errorElement) {
            errorElement.textContent = 'Это поле обязательно для заполнения';
        }
        return false;
    }
    
    // Специальная валидация для email
    if (field.type === 'email' && field.value.trim()) {
        if (!validateEmail(field.value.trim())) {
            fieldContainer.classList.add('error');
            if (errorElement) {
                errorElement.textContent = 'Введите корректный email адрес';
            }
            return false;
        }
    }
    
    return true;
}

/**
 * Валидация всей формы
 * @returns {boolean} - валидна ли форма
 */
function validateForm() {
    const form = document.getElementById('registration-form');
    if (!form) return false;
    
    const fields = form.querySelectorAll('input[required]');
    let isValid = true;
    
    fields.forEach(field => {
        if (!validateField(field)) {
            isValid = false;
        }
    });
    
    // Проверка групп полей (должно быть заполнено ровно 3 поля в каждой группе)
    const groups = ['genre', 'author', 'book', 'discuss'];
    groups.forEach(prefix => {
        const values = collectFieldGroup(prefix);
        if (values.length !== 3) {
            isValid = false;
            // Помечаем все поля группы как ошибочные
            for (let i = 1; i <= 3; i++) {
                const field = document.querySelector(`input[name="${prefix}${i}"]`);
                if (field) {
                    const fieldContainer = field.closest('.form-field');
                    fieldContainer.classList.add('error');
                    const errorElement = fieldContainer.querySelector('.field-error');
                    if (errorElement && !errorElement.textContent) {
                        errorElement.textContent = 'Необходимо заполнить все три поля';
                    }
                }
            }
        }
    });
    
    return isValid;
}

/**
 * Собирает данные формы в формат для API
 * @returns {Object} - данные пользователя в формате UserCreate
 */
function collectFormData() {
    const nameField = document.getElementById('name');
    const emailField = document.getElementById('email');
    
    const { first_name, last_name } = splitName(nameField.value.trim());
    
    return {
        first_name,
        last_name,
        email: emailField.value.trim(),
        phone: null, // Не обязательное поле
        birth_date: null, // Не обязательное поле
        fav_genres: collectFieldGroup('genre'),
        fav_authors: collectFieldGroup('author'),
        fav_books: collectFieldGroup('book'),
        discuss_books: collectFieldGroup('discuss'),
    };
}

/**
 * Показывает сообщение об успехе или ошибке
 * @param {string} message - текст сообщения
 * @param {string} type - тип сообщения ('success' или 'error')
 */
function showFormMessage(message, type = 'error') {
    const messageElement = document.getElementById('form-message');
    if (!messageElement) return;
    
    messageElement.textContent = message;
    messageElement.className = `form-message ${type}`;
    messageElement.classList.remove('hidden');
    
    // Прокрутка к сообщению
    messageElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    
    // Автоматически скрываем сообщение об успехе через 5 секунд
    if (type === 'success') {
        setTimeout(() => {
            messageElement.classList.add('hidden');
        }, 5000);
    }
}

/**
 * Сбрасывает форму
 */
function resetForm() {
    const form = document.getElementById('registration-form');
    if (form) {
        form.reset();
        
        // Убираем все ошибки
        const errorFields = form.querySelectorAll('.form-field.error');
        errorFields.forEach(field => {
            field.classList.remove('error');
            const errorElement = field.querySelector('.field-error');
            if (errorElement) {
                errorElement.textContent = '';
            }
        });
        
        // Скрываем сообщения
        const messageElement = document.getElementById('form-message');
        if (messageElement) {
            messageElement.classList.add('hidden');
        }
    }
}

/**
 * Обработчик отправки формы
 * @param {Event} event - событие формы
 */
async function handleFormSubmit(event) {
    event.preventDefault();
    
    const form = event.target;
    const submitButton = form.querySelector('button[type="submit"]');
    const btnText = submitButton.querySelector('.btn-text');
    const btnSpinner = submitButton.querySelector('.btn-spinner');
    
    // Валидация формы
    if (!validateForm()) {
        showFormMessage('Пожалуйста, заполните все обязательные поля корректно', 'error');
        return;
    }
    
    // Блокируем кнопку и показываем спиннер
    submitButton.disabled = true;
    if (btnText) btnText.textContent = 'Отправка...';
    if (btnSpinner) btnSpinner.classList.remove('hidden');
    
    try {
        const formData = collectFormData();
        
        // Отправка данных на сервер
        const response = await window.api.registerUser(formData);
        
        // Успешная регистрация
        showFormMessage(
            'Спасибо! Ваша заявка успешно отправлена. Мы свяжемся с вами в ближайшее время.',
            'success'
        );
        
        // Сбрасываем форму через небольшую задержку
        setTimeout(() => {
            resetForm();
        }, 2000);
        
    } catch (error) {
        // Обработка ошибок
        let errorMessage = 'Произошла ошибка при отправке формы. Попробуйте позже.';
        
        if (error.message) {
            errorMessage = error.message;
        }
        
        showFormMessage(errorMessage, 'error');
    } finally {
        // Разблокируем кнопку и скрываем спиннер
        submitButton.disabled = false;
        if (btnText) btnText.textContent = 'Отправить заявку';
        if (btnSpinner) btnSpinner.classList.add('hidden');
    }
}

/**
 * Инициализация обработчиков формы
 */
function initForm() {
    const form = document.getElementById('registration-form');
    if (!form) return;
    
    // Обработчик отправки формы
    form.addEventListener('submit', handleFormSubmit);
    
    // Валидация полей при потере фокуса
    const fields = form.querySelectorAll('input');
    fields.forEach(field => {
        field.addEventListener('blur', () => {
            validateField(field);
        });
        
        // Убираем ошибку при вводе
        field.addEventListener('input', () => {
            const fieldContainer = field.closest('.form-field');
            if (fieldContainer && fieldContainer.classList.contains('error')) {
                // Проверяем поле снова при вводе
                if (field.value.trim() && (field.type !== 'email' || validateEmail(field.value.trim()))) {
                    fieldContainer.classList.remove('error');
                    const errorElement = fieldContainer.querySelector('.field-error');
                    if (errorElement) {
                        errorElement.textContent = '';
                    }
                }
            }
        });
    });
}

// Инициализация при загрузке DOM
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initForm);
} else {
    initForm();
}

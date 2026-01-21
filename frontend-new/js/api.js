/**
 * API модуль для работы с бэкендом NartBooks
 * Базовый URL можно настроить через переменную окружения или изменить здесь
 */

const API_BASE_URL = window.API_BASE_URL || 'http://localhost:8000';

/**
 * Выполняет HTTP запрос к API
 * @param {string} endpoint - эндпоинт API (например, '/books/current')
 * @param {Object} options - опции для fetch (method, body, headers и т.д.)
 * @returns {Promise<Object>} - ответ от сервера
 */
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
    };
    
    const config = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers,
        },
    };
    
    try {
        const response = await fetch(url, config);
        
        // Проверяем статус ответа
        if (!response.ok) {
            let errorMessage = `Ошибка ${response.status}`;
            try {
                const errorData = await response.json();
                if (errorData.detail) {
                    errorMessage = errorData.detail;
                }
            } catch (e) {
                // Если не удалось распарсить JSON, используем стандартное сообщение
                errorMessage = `Ошибка ${response.status}: ${response.statusText}`;
            }
            
            // Если 401 (Unauthorized), удаляем токен из localStorage
            if (response.status === 401) {
                const token = localStorage.getItem('auth_token');
                if (token) {
                    console.warn('Получен 401, удаляем токен из localStorage');
                    localStorage.removeItem('auth_token');
                    // Если это не страница авторизации, перенаправляем на неё
                    if (!window.location.pathname.includes('auth.html')) {
                        const currentPath = window.location.pathname.split('/').pop() || 'index.html';
                        window.location.href = `auth.html?redirect=${currentPath}`;
                    }
                }
            }
            
            throw new Error(errorMessage);
        }
        
        // Пытаемся распарсить JSON
        const data = await response.json();
        return data;
    } catch (error) {
        // Обработка сетевых ошибок
        if (error.name === 'TypeError' && (error.message.includes('fetch') || error.message.includes('Failed to fetch') || error.message.includes('NetworkError'))) {
            throw new Error('Не удалось подключиться к серверу. Проверьте, запущен ли бэкенд на http://localhost:8000');
        }
        // Если это уже наша ошибка, просто пробрасываем её дальше
        if (error.message && error.message.includes('Ошибка')) {
            throw error;
        }
        // Для других ошибок добавляем контекст
        throw new Error(error.message || 'Неизвестная ошибка при запросе к серверу');
    }
}

/**
 * Получает текущую книгу месяца
 * @returns {Promise<Object>} - данные о книге месяца
 */
async function getCurrentBook() {
    return apiRequest('/books/current');
}

/**
 * Получает список книг (событий)
 * @param {Object} params - параметры запроса (page, limit, search)
 * @returns {Promise<Object>} - список книг с пагинацией
 */
async function getBooks(params = {}) {
    const { page = 1, limit = 10, search = null } = params;
    
    let endpoint = `/books?page=${page}&limit=${limit}`;
    if (search) {
        endpoint += `&search=${encodeURIComponent(search)}`;
    }
    
    return apiRequest(endpoint);
}

/**
 * Регистрирует нового пользователя
 * @param {Object} userData - данные пользователя согласно схеме UserCreate
 * @returns {Promise<Object>} - ответ от сервера
 */
async function registerUser(userData) {
    return apiRequest('/register', {
        method: 'POST',
        body: JSON.stringify(userData),
    });
}

/**
 * Получает информацию о текущем пользователе (требует авторизации)
 * @returns {Promise<Object>} - данные пользователя
 */
async function getCurrentUser() {
    const token = localStorage.getItem('auth_token');
    if (!token) {
        throw new Error('Токен авторизации не найден');
    }
    return apiRequest('/me', {
        headers: {
            'Authorization': `Bearer ${token}`,
        },
    });
}

/**
 * Получает книгу по ID
 * @param {number} bookId - ID книги
 * @returns {Promise<Object>} - данные о книге
 */
async function getBookById(bookId) {
    return apiRequest(`/books/${bookId}`);
}

/**
 * Создает новую книгу (требует авторизации админа)
 * @param {Object} bookData - данные книги
 * @returns {Promise<Object>} - ответ от сервера
 */
async function createBook(bookData) {
    const token = localStorage.getItem('auth_token');
    if (!token) {
        throw new Error('Токен авторизации не найден');
    }
    return apiRequest('/books', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(bookData),
    });
}

/**
 * Обновляет книгу (требует авторизации админа)
 * @param {number} bookId - ID книги
 * @param {Object} bookData - данные книги
 * @returns {Promise<Object>} - ответ от сервера
 */
async function updateBook(bookId, bookData) {
    const token = localStorage.getItem('auth_token');
    if (!token) {
        throw new Error('Токен авторизации не найден');
    }
    return apiRequest(`/books/${bookId}`, {
        method: 'PUT',
        headers: {
            'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(bookData),
    });
}

/**
 * Удаляет книгу (требует авторизации админа)
 * @param {number} bookId - ID книги
 * @returns {Promise<Object>} - ответ от сервера
 */
async function deleteBook(bookId) {
    const token = localStorage.getItem('auth_token');
    if (!token) {
        throw new Error('Токен авторизации не найден');
    }
    return apiRequest(`/books/${bookId}`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${token}`,
        },
    });
}

/**
 * Получает список пользователей (требует авторизации админа)
 * @param {Object} params - параметры запроса (page, limit)
 * @returns {Promise<Object>} - список пользователей с пагинацией
 */
async function getUsers(params = {}) {
    const { page = 1, limit = 10 } = params;
    const token = localStorage.getItem('auth_token');
    if (!token) {
        throw new Error('Токен авторизации не найден');
    }
    return apiRequest(`/users?page=${page}&limit=${limit}`, {
        headers: {
            'Authorization': `Bearer ${token}`,
        },
    });
}

/**
 * Получает пользователя по ID (требует авторизации админа)
 * @param {number} userId - ID пользователя
 * @returns {Promise<Object>} - данные пользователя
 */
async function getUserById(userId) {
    const token = localStorage.getItem('auth_token');
    if (!token) {
        throw new Error('Токен авторизации не найден');
    }
    return apiRequest(`/users/${userId}`, {
        headers: {
            'Authorization': `Bearer ${token}`,
        },
    });
}

/**
 * Обновляет роль пользователя (требует авторизации админа)
 * @param {number} userId - ID пользователя
 * @param {string} role - новая роль (user или admin)
 * @returns {Promise<Object>} - ответ от сервера
 */
async function updateUserRole(userId, role) {
    const token = localStorage.getItem('auth_token');
    if (!token) {
        throw new Error('Токен авторизации не найден');
    }
    return apiRequest(`/users/${userId}/role`, {
        method: 'PUT',
        headers: {
            'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ role }),
    });
}

/**
 * Отправляет код верификации на email или телефон
 * @param {Object} data - данные запроса {email: string} или {phone: string}
 * @returns {Promise<Object>} - ответ от сервера
 */
async function sendAuthCode(data) {
    return apiRequest('/auth/send-code', {
        method: 'POST',
        body: JSON.stringify(data),
    });
}

/**
 * Верифицирует код и получает токен авторизации
 * @param {Object} data - данные запроса {email: string, code: string} или {phone: string, code: string}
 * @returns {Promise<Object>} - ответ с токеном
 */
async function verifyAuthCode(data) {
    return apiRequest('/auth/verify-code', {
        method: 'POST',
        body: JSON.stringify(data),
    });
}

/**
 * Записаться на встречу (книгу месяца)
 * @param {number} bookId - ID книги
 * @returns {Promise<Object>} - ответ от сервера
 */
async function registerForMeeting(bookId) {
    const token = localStorage.getItem('auth_token');
    if (!token) {
        throw new Error('Токен авторизации не найден');
    }
    return apiRequest(`/meetings/register/${bookId}`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
        },
    });
}

/**
 * Отменить запись на встречу
 * @param {number} bookId - ID книги
 * @returns {Promise<Object>} - ответ от сервера
 */
async function cancelMeetingRegistration(bookId) {
    const token = localStorage.getItem('auth_token');
    if (!token) {
        throw new Error('Токен авторизации не найден');
    }
    return apiRequest(`/meetings/register/${bookId}`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${token}`,
        },
    });
}

/**
 * Получить список встреч, на которые записан текущий пользователь
 * @returns {Promise<Object>} - список встреч
 */
async function getMyMeetings() {
    const token = localStorage.getItem('auth_token');
    if (!token) {
        throw new Error('Токен авторизации не найден');
    }
    return apiRequest('/meetings/my', {
        headers: {
            'Authorization': `Bearer ${token}`,
        },
    });
}

/**
 * Получить список участников встречи (только для админов)
 * @param {number} bookId - ID книги
 * @returns {Promise<Object>} - список участников
 */
async function getMeetingParticipants(bookId) {
    const token = localStorage.getItem('auth_token');
    if (!token) {
        throw new Error('Токен авторизации не найден');
    }
    return apiRequest(`/meetings/${bookId}/participants`, {
        headers: {
            'Authorization': `Bearer ${token}`,
        },
    });
}

/**
 * Установить книгу как текущую книгу месяца (только для админов)
 * @param {number} bookId - ID книги
 * @returns {Promise<Object>} - ответ от сервера
 */
async function setCurrentBook(bookId) {
    const token = localStorage.getItem('auth_token');
    if (!token) {
        throw new Error('Токен авторизации не найден');
    }
    return apiRequest(`/books/${bookId}/set-current`, {
        method: 'PUT',
        headers: {
            'Authorization': `Bearer ${token}`,
        },
    });
}

/**
 * Обновить профиль текущего пользователя
 * @param {Object} userData - данные для обновления
 * @returns {Promise<Object>} - обновлённый профиль
 */
async function updateProfile(userData) {
    const token = localStorage.getItem('auth_token');
    if (!token) {
        throw new Error('Токен авторизации не найден');
    }
    return apiRequest('/me', {
        method: 'PATCH',
        headers: {
            'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(userData),
    });
}

// Экспорт функций для использования в других модулях
window.api = {
    getCurrentBook,
    getBooks,
    registerUser,
    getCurrentUser,
    getBookById,
    createBook,
    updateBook,
    deleteBook,
    getUsers,
    getUserById,
    updateUserRole,
    sendAuthCode,
    verifyAuthCode,
    registerForMeeting,
    cancelMeetingRegistration,
    getMyMeetings,
    getMeetingParticipants,
    setCurrentBook,
    updateProfile,
};

// Проверка экспорта (для отладки)
if (typeof window !== 'undefined' && window.console) {
    console.log('API модуль загружен. Доступные функции:', Object.keys(window.api));
}

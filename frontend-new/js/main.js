/**
 * Основной модуль для инициализации страницы и загрузки данных
 */

/**
 * Экранирование HTML для безопасности
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Проверяет, записан ли текущий пользователь на встречу
 */
async function checkMeetingRegistration(bookId) {
    try {
        const token = localStorage.getItem('auth_token');
        if (!token) return false;
        
        const meetings = await window.api.getMyMeetings();
        return meetings.items.some(m => m.book_id === bookId);
    } catch (error) {
        return false;
    }
}

/**
 * Отображает текущую книгу месяца
 * @param {Object} book - данные о книге
 */
async function displayCurrentBook(book) {
    const container = document.getElementById('current-book');
    if (!container) return;
    
    const loadingEl = container.querySelector('.book-loading');
    const errorEl = container.querySelector('.book-error');
    const contentEl = container.querySelector('.book-content');
    
    // Скрываем загрузку и ошибки
    if (loadingEl) loadingEl.classList.add('hidden');
    if (errorEl) errorEl.classList.add('hidden');
    
    // Показываем контент
    if (contentEl) {
        const titleEl = contentEl.querySelector('.book-title');
        const authorEl = contentEl.querySelector('.book-author');
        const descriptionEl = contentEl.querySelector('.book-description');
        const dateEl = contentEl.querySelector('.book-date');
        const locationEl = contentEl.querySelector('.book-location');
        const participantsEl = contentEl.querySelector('.book-participants');
        const actionsDiv = document.getElementById('book-actions');
        const registerBtn = document.getElementById('registerMeetingBtn');
        const cancelBtn = document.getElementById('cancelMeetingBtn');
        const statusEl = document.getElementById('registration-status');
        
        if (titleEl) {
            titleEl.textContent = book.title || 'Без названия';
            titleEl.dataset.bookId = book.id; // Сохраняем ID для записи
        }
        if (authorEl) authorEl.textContent = book.author || 'Автор не указан';
        if (descriptionEl) {
            descriptionEl.textContent = book.description || 'Описание отсутствует';
        }
        if (dateEl) {
            dateEl.textContent = book.date || 'Дата не указана';
        }
        if (locationEl) {
            locationEl.textContent = book.location || 'Место не указано';
        }
        if (participantsEl) {
            const count = book.registered_count || 0;
            participantsEl.textContent = `👥 Записавшихся: ${count}`;
        }
        
        // Проверяем авторизацию и статус записи
        const token = localStorage.getItem('auth_token');
        const authActions = document.getElementById('authActions');
        const guestActions = document.getElementById('guestActions');
        
        if (token && actionsDiv) {
            // Показываем действия для авторизованных
            if (authActions) authActions.classList.remove('hidden');
            if (guestActions) guestActions.classList.add('hidden');
            
            const isRegistered = await checkMeetingRegistration(book.id);
            
            if (isRegistered) {
                if (registerBtn) registerBtn.style.display = 'none';
                if (cancelBtn) cancelBtn.style.display = 'block';
                if (statusEl) {
                    statusEl.textContent = '✓ Вы записаны на эту встречу';
                    statusEl.style.color = 'var(--color-success)';
                }
            } else {
                if (registerBtn) registerBtn.style.display = 'block';
                if (cancelBtn) cancelBtn.style.display = 'none';
                if (statusEl) statusEl.textContent = '';
            }
        } else if (actionsDiv) {
            // Показываем подсказку для неавторизованных
            if (authActions) authActions.classList.add('hidden');
            if (guestActions) guestActions.classList.remove('hidden');
        }
        
        contentEl.classList.remove('hidden');
    }
}

/**
 * Отображает ошибку загрузки книги месяца
 * @param {string} errorMessage - сообщение об ошибке
 */
function displayCurrentBookError(errorMessage) {
    const container = document.getElementById('current-book');
    if (!container) return;
    
    const loadingEl = container.querySelector('.book-loading');
    const errorEl = container.querySelector('.book-error');
    const contentEl = container.querySelector('.book-content');
    
    if (loadingEl) loadingEl.classList.add('hidden');
    if (contentEl) contentEl.classList.add('hidden');
    
    if (errorEl) {
        const errorText = errorEl.querySelector('p');
        if (errorText) {
            errorText.textContent = errorMessage || 'Не удалось загрузить книгу месяца';
        }
        errorEl.classList.remove('hidden');
    }
}

/**
 * Загружает и отображает текущую книгу месяца
 */
async function loadCurrentBook() {
    const container = document.getElementById('current-book');
    if (!container) return;
    
    const loadingEl = container.querySelector('.book-loading');
    const errorEl = container.querySelector('.book-error');
    const contentEl = container.querySelector('.book-content');
    
    // Показываем загрузку
    if (loadingEl) loadingEl.classList.remove('hidden');
    if (errorEl) errorEl.classList.add('hidden');
    if (contentEl) contentEl.classList.add('hidden');
    
    try {
        const book = await window.api.getCurrentBook();
        displayCurrentBook(book);
    } catch (error) {
        const errorMessage = error.message || 'Не удалось загрузить книгу месяца';
        displayCurrentBookError(errorMessage);
    }
}

/**
 * Создает карточку события
 * @param {Object} book - данные о книге (событии)
 * @returns {HTMLElement} - элемент карточки
 */
function createEventCard(book) {
    const card = document.createElement('div');
    card.className = 'event-card';
    
    const registeredCount = book.registered_count || 0;
    const isCurrent = book.is_current ? '<span style="color: var(--color-accent); font-size: var(--font-size-sm);">★ Текущая книга</span>' : '';
    
    card.innerHTML = `
        <div class="event-date">${escapeHtml(book.date || 'Дата не указана')}</div>
        <div class="event-location">${escapeHtml(book.location || 'Место не указано')}</div>
        ${isCurrent ? `<div style="margin-bottom: var(--spacing-xs);">${isCurrent}</div>` : ''}
        <div class="event-book-title">${escapeHtml(book.title || 'Без названия')}</div>
        <div class="event-book-author">${escapeHtml(book.author || 'Автор не указан')}</div>
        <div style="margin-top: var(--spacing-sm); font-size: var(--font-size-sm); color: var(--color-text-light);">
            👥 Записавшихся: ${registeredCount}
        </div>
    `;
    
    return card;
}

/**
 * Отображает список событий
 * @param {Array<Object>} books - массив книг (событий)
 */
function displayEvents(books) {
    const container = document.getElementById('events-list');
    if (!container) return;
    
    const loadingEl = container.querySelector('.events-loading');
    const errorEl = container.querySelector('.events-error');
    const contentEl = container.querySelector('.events-content');
    
    // Скрываем загрузку и ошибки
    if (loadingEl) loadingEl.classList.add('hidden');
    if (errorEl) errorEl.classList.add('hidden');
    
    // Очищаем предыдущий контент
    if (contentEl) {
        contentEl.innerHTML = '';
        
        if (books && books.length > 0) {
            books.forEach(book => {
                const card = createEventCard(book);
                contentEl.appendChild(card);
            });
            contentEl.classList.remove('hidden');
        } else {
            // Если событий нет
            contentEl.innerHTML = '<p style="text-align: center; color: var(--color-text-light);">События пока не запланированы</p>';
            contentEl.classList.remove('hidden');
        }
    }
}

/**
 * Отображает ошибку загрузки событий
 * @param {string} errorMessage - сообщение об ошибке
 */
function displayEventsError(errorMessage) {
    const container = document.getElementById('events-list');
    if (!container) return;
    
    const loadingEl = container.querySelector('.events-loading');
    const errorEl = container.querySelector('.events-error');
    const contentEl = container.querySelector('.events-content');
    
    if (loadingEl) loadingEl.classList.add('hidden');
    if (contentEl) contentEl.classList.add('hidden');
    
    if (errorEl) {
        const errorText = errorEl.querySelector('p');
        if (errorText) {
            errorText.textContent = errorMessage || 'Не удалось загрузить события';
        }
        errorEl.classList.remove('hidden');
    }
}

/**
 * Загружает и отображает события
 */
async function loadEvents() {
    const container = document.getElementById('events-list');
    if (!container) return;
    
    const loadingEl = container.querySelector('.events-loading');
    const errorEl = container.querySelector('.events-error');
    const contentEl = container.querySelector('.events-content');
    
    // Показываем загрузку
    if (loadingEl) loadingEl.classList.remove('hidden');
    if (errorEl) errorEl.classList.add('hidden');
    if (contentEl) contentEl.classList.add('hidden');
    
    try {
        const response = await window.api.getBooks({ limit: 10 });
        const books = response.items || [];
        displayEvents(books);
    } catch (error) {
        const errorMessage = error.message || 'Не удалось загрузить события';
        displayEventsError(errorMessage);
    }
}

/**
 * Плавная прокрутка к элементу при клике на якорные ссылки
 */
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href === '#') return;
            
            const target = document.querySelector(href);
            if (target) {
                e.preventDefault();
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

/**
 * Записаться на встречу
 */
async function registerForCurrentMeeting() {
    const bookCard = document.getElementById('current-book');
    if (!bookCard) return;
    
    const bookContent = bookCard.querySelector('.book-content');
    if (!bookContent || bookContent.classList.contains('hidden')) return;
    
    const registerBtn = document.getElementById('registerMeetingBtn');
    const statusEl = document.getElementById('registration-status');
    const btnText = registerBtn.querySelector('.btn-text');
    const btnSpinner = registerBtn.querySelector('.btn-spinner');
    
    // Получаем ID книги из данных
    const titleEl = bookContent.querySelector('.book-title');
    if (!titleEl || !titleEl.dataset.bookId) {
        // Если ID не сохранён, перезагружаем книгу
        await loadCurrentBook();
        return;
    }
    
    const bookId = parseInt(titleEl.dataset.bookId);
    
    registerBtn.disabled = true;
    btnText.textContent = 'Записываем...';
    btnSpinner.classList.remove('hidden');
    
    try {
        await window.api.registerForMeeting(bookId);
        
        // Обновляем интерфейс
        registerBtn.style.display = 'none';
        document.getElementById('cancelMeetingBtn').style.display = 'block';
        if (statusEl) {
            statusEl.textContent = '✓ Вы успешно записались на встречу!';
            statusEl.style.color = 'var(--color-success)';
        }
        
        // Обновляем количество участников
        await loadCurrentBook();
    } catch (error) {
        if (statusEl) {
            statusEl.textContent = `Ошибка: ${error.message}`;
            statusEl.style.color = 'var(--color-error)';
        }
    } finally {
        registerBtn.disabled = false;
        btnText.textContent = 'Записаться на встречу';
        btnSpinner.classList.add('hidden');
    }
}

/**
 * Отменить запись на встречу
 */
async function cancelCurrentMeeting() {
    const bookCard = document.getElementById('current-book');
    if (!bookCard) return;
    
    const bookContent = bookCard.querySelector('.book-content');
    if (!bookContent || bookContent.classList.contains('hidden')) return;
    
    if (!confirm('Вы уверены, что хотите отменить запись на эту встречу?')) {
        return;
    }
    
    const cancelBtn = document.getElementById('cancelMeetingBtn');
    const statusEl = document.getElementById('registration-status');
    const btnText = cancelBtn.querySelector('.btn-text');
    const btnSpinner = cancelBtn.querySelector('.btn-spinner');
    
    const titleEl = bookContent.querySelector('.book-title');
    const bookId = parseInt(titleEl.dataset.bookId);
    
    cancelBtn.disabled = true;
    btnText.textContent = 'Отменяем...';
    btnSpinner.classList.remove('hidden');
    
    try {
        await window.api.cancelMeetingRegistration(bookId);
        
        // Обновляем интерфейс
        cancelBtn.style.display = 'none';
        document.getElementById('registerMeetingBtn').style.display = 'block';
        if (statusEl) {
            statusEl.textContent = '';
        }
        
        // Обновляем количество участников
        await loadCurrentBook();
    } catch (error) {
        if (statusEl) {
            statusEl.textContent = `Ошибка: ${error.message}`;
            statusEl.style.color = 'var(--color-error)';
        }
    } finally {
        cancelBtn.disabled = false;
        btnText.textContent = 'Отменить запись';
        btnSpinner.classList.add('hidden');
    }
}

/**
 * Обновление навигации в зависимости от авторизации
 */
async function updateNavigation() {
    const token = localStorage.getItem('auth_token');
    const profileLink = document.getElementById('profileLink');
    const adminLink = document.getElementById('adminLink');
    const authLink = document.getElementById('authLink');
    const logoutBtn = document.getElementById('logoutBtn');
    
    if (!token) {
        console.log('Токен не найден, показываем ссылку на вход');
        if (profileLink) profileLink.classList.add('hidden');
        if (adminLink) adminLink.classList.add('hidden');
        if (authLink) authLink.classList.remove('hidden');
        if (logoutBtn) logoutBtn.classList.add('hidden');
        return;
    }
    
    console.log('Токен найден, проверяем авторизацию...');
    
    // Проверяем, что API загружен
    if (!window.api || !window.api.getCurrentUser) {
        console.warn('API не загружен, ждём...');
        // Ждём до 2 секунд для загрузки API
        for (let i = 0; i < 20; i++) {
            await new Promise(resolve => setTimeout(resolve, 100));
            if (window.api && window.api.getCurrentUser) {
                break;
            }
        }
    }
    
    if (!window.api || !window.api.getCurrentUser) {
        console.warn('API не загружен, но токен есть - показываем авторизованный интерфейс');
        // Показываем авторизованный интерфейс даже если API не загружен
        if (profileLink) profileLink.classList.remove('hidden');
        if (authLink) authLink.classList.add('hidden');
        if (logoutBtn) {
            logoutBtn.classList.remove('hidden');
            const newLogoutBtn = logoutBtn.cloneNode(true);
            logoutBtn.parentNode.replaceChild(newLogoutBtn, logoutBtn);
            newLogoutBtn.addEventListener('click', () => {
                localStorage.removeItem('auth_token');
                window.location.reload();
            });
        }
        return;
    }
    
    try {
        const user = await window.api.getCurrentUser();
        console.log('✅ Пользователь авторизован:', user.email);
        
        if (profileLink) profileLink.classList.remove('hidden');
        if (authLink) authLink.classList.add('hidden');
        if (logoutBtn) {
            logoutBtn.classList.remove('hidden');
            // Удаляем старые обработчики, чтобы не дублировать
            const newLogoutBtn = logoutBtn.cloneNode(true);
            logoutBtn.parentNode.replaceChild(newLogoutBtn, logoutBtn);
            newLogoutBtn.addEventListener('click', () => {
                localStorage.removeItem('auth_token');
                window.location.reload();
            });
        }
        
        if (user.role === 'admin' && adminLink) {
            adminLink.classList.remove('hidden');
        }
    } catch (error) {
        console.error('Ошибка проверки авторизации:', error);
        
        // Удаляем токен ТОЛЬКО при явных ошибках авторизации
        const isAuthError = error.message && (
            error.message.includes('401') || 
            error.message.includes('Токен истек') ||
            error.message.includes('Неверный токен') ||
            error.message.includes('Токен авторизации не предоставлен') ||
            error.message.includes('Неверный формат токена')
        );
        
        if (isAuthError) {
            console.log('❌ Токен недействителен, удаляем');
            localStorage.removeItem('auth_token');
        } else {
            console.warn('⚠️ Ошибка при проверке (не удаляем токен):', error.message);
            // При других ошибках (сеть и т.д.) не удаляем токен
            // Но и не показываем авторизованный интерфейс
        }
        
        // Показываем ссылку на вход
        if (profileLink) profileLink.classList.add('hidden');
        if (adminLink) adminLink.classList.add('hidden');
        if (authLink) authLink.classList.remove('hidden');
        if (logoutBtn) logoutBtn.classList.add('hidden');
    }
}

/**
 * Проверка валидности токена при загрузке страницы
 * НЕ удаляет токен при ошибках - только проверяет
 */
async function validateTokenOnLoad() {
    const token = localStorage.getItem('auth_token');
    if (!token) {
        console.log('Токен не найден в localStorage');
        return false;
    }
    
    console.log('Проверка токена при загрузке страницы...');
    
    // Проверяем, что API загружен - ждём немного если нужно
    if (!window.api || !window.api.getCurrentUser) {
        console.warn('API не загружен, ждём...');
        // Ждём до 2 секунд для загрузки API
        for (let i = 0; i < 20; i++) {
            await new Promise(resolve => setTimeout(resolve, 100));
            if (window.api && window.api.getCurrentUser) {
                break;
            }
        }
        
        if (!window.api || !window.api.getCurrentUser) {
            console.warn('API не загружен после ожидания, пропускаем проверку токена');
            return false; // Не удаляем токен, просто пропускаем проверку
        }
    }
    
    try {
        // Проверяем токен через запрос к /me
        const user = await window.api.getCurrentUser();
        console.log('✅ Токен валиден, пользователь:', user.email);
        return true;
    } catch (error) {
        // НЕ удаляем токен при проверке - только логируем
        // Токен будет удалён только при реальной ошибке 401 в API запросах
        console.warn('⚠️ Ошибка при проверке токена (не удаляем):', error.message);
        
        // Если это явная ошибка авторизации, только тогда удаляем
        if (error.message && (
            error.message.includes('401') || 
            error.message.includes('Токен истек') ||
            error.message.includes('Неверный токен') ||
            error.message.includes('Токен авторизации не предоставлен')
        )) {
            console.warn('❌ Токен действительно невалиден, удаляем');
            localStorage.removeItem('auth_token');
            return false;
        }
        
        // Для других ошибок (сеть, таймаут и т.д.) не удаляем токен
        return false; // Но возвращаем false, чтобы не показывать авторизованный интерфейс
    }
}

/**
 * Инициализация страницы
 */
async function init() {
    console.log('Инициализация страницы...');
    
    // Сначала обновляем навигацию (она сама проверит токен)
    // НЕ вызываем validateTokenOnLoad отдельно, чтобы не удалять токен
    await updateNavigation();
    
    // Инициализируем плавную прокрутку
    initSmoothScroll();
    
    // Обработчики кнопок записи на встречу
    const registerBtn = document.getElementById('registerMeetingBtn');
    const cancelBtn = document.getElementById('cancelMeetingBtn');
    
    if (registerBtn) {
        registerBtn.addEventListener('click', registerForCurrentMeeting);
    }
    if (cancelBtn) {
        cancelBtn.addEventListener('click', cancelCurrentMeeting);
    }
    
    // Загружаем данные
    await Promise.all([
        loadCurrentBook(),
        loadEvents()
    ]);
    
    console.log('Инициализация завершена');
}

// Делаем функции доступными глобально для обработчиков ошибок
window.loadCurrentBook = loadCurrentBook;
window.loadEvents = loadEvents;
window.registerForCurrentMeeting = registerForCurrentMeeting;
window.cancelCurrentMeeting = cancelCurrentMeeting;

// Запускаем инициализацию при загрузке DOM
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        console.log('DOM загружен, запускаем init()');
        init();
    });
} else {
    console.log('DOM уже загружен, запускаем init()');
    init();
}

// Добавляем глобальную функцию для проверки токена (для отладки)
window.checkAuth = async function() {
    const token = localStorage.getItem('auth_token');
    console.log('Токен в localStorage:', token ? token.substring(0, 30) + '...' : 'НЕТ');
    
    if (token) {
        try {
            const user = await window.api.getCurrentUser();
            console.log('✅ Токен валиден, пользователь:', user);
            return { valid: true, user };
        } catch (error) {
            console.error('❌ Токен невалиден:', error);
            localStorage.removeItem('auth_token');
            return { valid: false, error: error.message };
        }
    } else {
        console.log('❌ Токен не найден');
        return { valid: false, error: 'Токен не найден' };
    }
};

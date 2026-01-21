/**
 * Модуль админ-панели для управления книгами и пользователями
 */

let currentUser = null;
let booksPage = 1;
let usersPage = 1;
const limit = 10;

/**
 * Экранирование HTML для безопасности
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Проверка прав доступа администратора
 */
async function checkAdminAccess() {
    try {
        // Проверяем наличие токена
        const token = localStorage.getItem('auth_token');
        if (!token) {
            // Перенаправляем на страницу авторизации
            redirectToAuth();
            return false;
        }

        // Проверяем, что API доступен
        if (!window.api || !window.api.getCurrentUser) {
            showAccessDenied('Ошибка: API не загружен. Обновите страницу.');
            console.error('window.api.getCurrentUser не найдена');
            return false;
        }

        try {
            currentUser = await window.api.getCurrentUser();
        } catch (apiError) {
            console.error('Ошибка API при получении пользователя:', apiError);
            
            // Если ошибка подключения
            if (apiError.message && apiError.message.includes('подключиться к серверу')) {
                showAccessDenied('Ошибка: Не удалось подключиться к серверу. Проверьте, запущен ли бэкенд на http://localhost:8000');
                return false;
            }
            
            // Если ошибка 401, значит токен недействителен
            if (apiError.message && (apiError.message.includes('401') || apiError.message.includes('Токен') || apiError.message.includes('авторизации'))) {
                localStorage.removeItem('auth_token');
                redirectToAuth();
                return false;
            }
            
            throw apiError;
        }
        
        // Проверяем роль (может быть 'admin' или 'ADMIN')
        const userRole = currentUser.role ? currentUser.role.toLowerCase() : null;
        
        if (!currentUser || userRole !== 'admin') {
            showAccessDenied('Доступ запрещён. Требуется роль администратора.');
            return false;
        }
        
        return true;
    } catch (error) {
        console.error('Ошибка при проверке доступа:', error);
        
        // Если ошибка подключения
        if (error.message && error.message.includes('подключиться к серверу')) {
            showAccessDenied('Ошибка: Не удалось подключиться к серверу. Проверьте, запущен ли бэкенд на http://localhost:8000');
        } else if (error.message && (error.message.includes('401') || error.message.includes('Токен'))) {
            // Удаляем недействительный токен
            localStorage.removeItem('auth_token');
            // Перенаправляем на страницу авторизации
            redirectToAuth();
        } else {
            showAccessDenied(`Ошибка: ${error.message || 'Не удалось проверить доступ'}`);
        }
        return false;
    }
}

/**
 * Показать сообщение об отказе в доступе
 */
function showAccessDenied(message) {
    const booksTab = document.getElementById('booksTab');
    const usersTab = document.getElementById('usersTab');
    const accessDenied = document.getElementById('accessDenied');
    
    if (booksTab) booksTab.classList.add('hidden');
    if (usersTab) usersTab.classList.add('hidden');
    
    if (accessDenied) {
        accessDenied.classList.remove('hidden');
        const messageEl = accessDenied.querySelector('.form-description');
        const errorEl = document.getElementById('accessError');
        
        if (messageEl) {
            messageEl.textContent = 'Для доступа к админ-панели требуется роль администратора.';
        }
        
        if (errorEl) {
            errorEl.textContent = message;
            errorEl.classList.remove('hidden');
        }
    }
}

/**
 * Перенаправление на страницу авторизации
 */
function redirectToAuth() {
    const currentUrl = window.location.pathname;
    window.location.href = `auth.html?redirect=${encodeURIComponent(currentUrl)}`;
}

/**
 * Переключение вкладок
 */
function switchTab(tab) {
    // Обновляем кнопки вкладок
    document.querySelectorAll('.admin-tab-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.tab === tab) {
            btn.classList.add('active');
        }
    });

    // Показываем/скрываем контент
    document.getElementById('booksTab').classList.toggle('hidden', tab !== 'books');
    document.getElementById('usersTab').classList.toggle('hidden', tab !== 'users');

    // Загружаем данные для активной вкладки
    if (tab === 'books') {
        loadBooks(booksPage);
    } else if (tab === 'users') {
        loadUsers(usersPage);
    }
}

/**
 * Загрузка списка книг
 */
async function loadBooks(page = 1) {
    const container = document.getElementById('booksList');
    const pagination = document.getElementById('booksPagination');
    
    container.innerHTML = '<div class="spinner"></div><p>Загрузка...</p>';
    pagination.innerHTML = '';

    try {
        const data = await window.api.getBooks({ page, limit });
        
        if (!data.items || data.items.length === 0) {
            container.innerHTML = '<p class="form-description">Книг пока нет</p>';
            return;
        }

        container.innerHTML = '<div class="admin-grid"></div>';
        const grid = container.querySelector('.admin-grid');

        data.items.forEach(book => {
            const card = document.createElement('div');
            card.className = 'admin-card';
            const isCurrent = book.is_current ? '<span class="role-badge role-admin" style="margin-bottom: var(--spacing-sm); display: inline-block;">Текущая книга месяца</span>' : '';
            const registeredCount = book.registered_count || 0;
            card.innerHTML = `
                <div class="admin-card-content">
                    <div class="admin-card-main">
                        ${isCurrent}
                        <h3 class="admin-card-title">${escapeHtml(book.title)}</h3>
                        <p class="admin-card-author">${escapeHtml(book.author)}</p>
                        <div class="admin-card-meta">
                            <span>📅 ${escapeHtml(book.date || 'Не указана')}</span>
                            <span>📍 ${escapeHtml(book.location || 'Не указано')}</span>
                            <span>👥 Записавшихся: ${registeredCount}</span>
                        </div>
                        ${book.description ? `<p class="admin-card-description">${escapeHtml(book.description)}</p>` : ''}
                    </div>
                    <div class="admin-card-actions">
                        ${!book.is_current ? `<button class="btn btn-primary btn-sm" onclick="setCurrentBook(${book.id})" title="Сделать текущей книгой месяца">★ Сделать текущей</button>` : ''}
                        <button class="btn btn-secondary btn-sm" onclick="editBook(${book.id})">Редактировать</button>
                        <button class="btn btn-danger btn-sm" onclick="deleteBook(${book.id})">Удалить</button>
                    </div>
                </div>
            `;
            grid.appendChild(card);
        });

        // Пагинация
        if (data.pages > 1) {
            for (let i = 1; i <= data.pages; i++) {
                const btn = document.createElement('button');
                btn.className = `btn ${i === page ? 'btn-primary' : 'btn-secondary'} btn-sm`;
                btn.textContent = i;
                btn.onclick = () => {
                    booksPage = i;
                    loadBooks(i);
                };
                pagination.appendChild(btn);
            }
        }
    } catch (error) {
        container.innerHTML = `<div class="form-message error">Ошибка: ${error.message}</div>`;
    }
}

/**
 * Показать форму добавления книги
 */
function showAddBookForm() {
    document.getElementById('bookIdInput').value = '';
    document.getElementById('bookFormTitle').textContent = 'Добавить книгу';
    document.getElementById('bookForm').reset();
    document.getElementById('bookFormSection').classList.remove('hidden');
    document.getElementById('bookFormStatus').classList.add('hidden');
    window.scrollTo({ top: document.getElementById('bookFormSection').offsetTop - 20, behavior: 'smooth' });
}

/**
 * Редактирование книги
 */
async function editBook(bookId) {
    try {
        const book = await window.api.getBookById(bookId);
        document.getElementById('bookIdInput').value = book.id;
        document.getElementById('bookTitleInput').value = book.title || '';
        document.getElementById('bookAuthorInput').value = book.author || '';
        document.getElementById('bookDateInput').value = book.date || '';
        document.getElementById('bookLocationInput').value = book.location || '';
        document.getElementById('bookDescriptionInput').value = book.description || '';
        document.getElementById('bookFormTitle').textContent = 'Редактировать книгу';
        document.getElementById('bookFormSection').classList.remove('hidden');
        document.getElementById('bookFormStatus').classList.add('hidden');
        window.scrollTo({ top: document.getElementById('bookFormSection').offsetTop - 20, behavior: 'smooth' });
    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
}

/**
 * Отмена формы
 */
function cancelBookForm() {
    document.getElementById('bookFormSection').classList.add('hidden');
    document.getElementById('bookFormStatus').classList.add('hidden');
}

/**
 * Сохранение книги
 */
async function saveBook(e) {
    e.preventDefault();
    const statusDiv = document.getElementById('bookFormStatus');
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const btnText = submitBtn.querySelector('.btn-text');
    const btnSpinner = submitBtn.querySelector('.btn-spinner');

    statusDiv.classList.remove('hidden');
    statusDiv.innerHTML = '<div class="spinner"></div><p>Сохранение...</p>';
    submitBtn.disabled = true;
    btnText.textContent = 'Сохранение...';
    btnSpinner.classList.remove('hidden');

    try {
        const bookData = {
            title: document.getElementById('bookTitleInput').value.trim(),
            author: document.getElementById('bookAuthorInput').value.trim(),
            date: document.getElementById('bookDateInput').value.trim(),
            location: document.getElementById('bookLocationInput').value.trim(),
            description: document.getElementById('bookDescriptionInput').value.trim() || null,
        };

        const bookId = document.getElementById('bookIdInput').value;
        if (bookId) {
            await window.api.updateBook(bookId, bookData);
        } else {
            await window.api.createBook(bookData);
        }

        statusDiv.className = 'form-message success';
        statusDiv.textContent = 'Книга успешно сохранена!';
        
        setTimeout(() => {
            cancelBookForm();
            loadBooks(booksPage);
        }, 1500);
    } catch (error) {
        statusDiv.className = 'form-message error';
        statusDiv.textContent = `Ошибка: ${error.message}`;
    } finally {
        submitBtn.disabled = false;
        btnText.textContent = 'Сохранить';
        btnSpinner.classList.add('hidden');
    }
}

/**
 * Удаление книги
 */
async function deleteBook(bookId) {
    if (!confirm('Вы уверены, что хотите удалить эту книгу?')) {
        return;
    }
    
    try {
        await window.api.deleteBook(bookId);
        loadBooks(booksPage);
    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
}

/**
 * Установить книгу как текущую
 */
async function setCurrentBook(bookId) {
    if (!confirm('Установить эту книгу как текущую книгу месяца? Текущий флаг будет снят с других книг.')) {
        return;
    }
    
    try {
        await window.api.setCurrentBook(bookId);
        loadBooks(booksPage);
    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
}

/**
 * Показать детальную информацию о пользователе
 */
async function showUserDetails(userId) {
    try {
        const user = await window.api.getUserById(userId);
        
        const formatList = (arr) => arr && arr.length > 0 ? arr.join(', ') : 'Не указано';
        
        const detailsHtml = `
            <div class="admin-form-card" style="max-width: 800px; margin: var(--spacing-xl) auto;">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: var(--spacing-lg);">
                    <h3 class="admin-form-title">Информация о пользователе</h3>
                    <button class="btn btn-secondary btn-sm" onclick="closeUserDetails()">✕ Закрыть</button>
                </div>
                
                <div style="display: grid; gap: var(--spacing-lg);">
                    <div>
                        <h4 style="font-family: var(--font-serif); color: var(--color-accent); margin-bottom: var(--spacing-sm);">Основная информация</h4>
                        <p><strong>Имя:</strong> ${escapeHtml(user.first_name || '')} ${escapeHtml(user.last_name || '')}</p>
                        <p><strong>Email:</strong> ${escapeHtml(user.email || '')}</p>
                        ${user.phone ? `<p><strong>Телефон:</strong> ${escapeHtml(user.phone)}</p>` : ''}
                        ${user.birth_date ? `<p><strong>Дата рождения:</strong> ${escapeHtml(user.birth_date)}</p>` : ''}
                        ${user.created_at ? `<p><strong>Дата регистрации:</strong> ${escapeHtml(user.created_at)}</p>` : ''}
                        <p><strong>Роль:</strong> <span class="role-badge role-${user.role || 'user'}">${escapeHtml(user.role || 'user')}</span></p>
                    </div>
                    
                    <div>
                        <h4 style="font-family: var(--font-serif); color: var(--color-accent); margin-bottom: var(--spacing-sm);">Статистика</h4>
                        <p><strong>Записей на встречи:</strong> ${user.statistics?.meetings_count || 0}</p>
                        <p><strong>Избранных книг:</strong> ${user.statistics?.favorites_count || 0}</p>
                        <p><strong>Отзывов:</strong> ${user.statistics?.reviews_count || 0}</p>
                    </div>
                    
                    <div>
                        <h4 style="font-family: var(--font-serif); color: var(--color-accent); margin-bottom: var(--spacing-sm);">Интересы</h4>
                        <p><strong>Любимые авторы:</strong> ${escapeHtml(formatList(user.fav_authors))}</p>
                        <p><strong>Любимые жанры:</strong> ${escapeHtml(formatList(user.fav_genres))}</p>
                        <p><strong>Любимые книги:</strong> ${escapeHtml(formatList(user.fav_books))}</p>
                        <p><strong>Книги для обсуждения:</strong> ${escapeHtml(formatList(user.discuss_books))}</p>
                    </div>
                    
                    ${user.registered_meetings && user.registered_meetings.length > 0 ? `
                    <div>
                        <h4 style="font-family: var(--font-serif); color: var(--color-accent); margin-bottom: var(--spacing-sm);">Записанные встречи</h4>
                        <div style="display: grid; gap: var(--spacing-sm);">
                            ${user.registered_meetings.map(meeting => `
                                <div style="padding: var(--spacing-sm); background: var(--color-bg-secondary); border-radius: var(--radius-sm);">
                                    <strong>${escapeHtml(meeting.book_title)}</strong> - ${escapeHtml(meeting.book_author)}<br>
                                    <small>${escapeHtml(meeting.book_date)} | ${escapeHtml(meeting.book_location)}</small>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    ` : ''}
                </div>
            </div>
        `;
        
        // Создаём модальное окно
        const modal = document.createElement('div');
        modal.id = 'userDetailsModal';
        modal.style.cssText = 'position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 1000; overflow-y: auto; padding: var(--spacing-xl);';
        modal.innerHTML = detailsHtml;
        document.body.appendChild(modal);
        
    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
}

/**
 * Закрыть детальную информацию о пользователе
 */
function closeUserDetails() {
    const modal = document.getElementById('userDetailsModal');
    if (modal) {
        modal.remove();
    }
}

/**
 * Загрузка списка пользователей
 */
async function loadUsers(page = 1) {
    const container = document.getElementById('usersList');
    const pagination = document.getElementById('usersPagination');
    
    container.innerHTML = '<div class="spinner"></div><p>Загрузка...</p>';
    pagination.innerHTML = '';

    try {
        const data = await window.api.getUsers({ page, limit });
        
        if (!data.items || data.items.length === 0) {
            container.innerHTML = '<p class="form-description">Пользователей пока нет</p>';
            return;
        }

        container.innerHTML = '<div class="admin-grid"></div>';
        const grid = container.querySelector('.admin-grid');

        data.items.forEach(user => {
            const card = document.createElement('div');
            card.className = 'admin-card';
            const fullName = `${user.first_name || ''} ${user.last_name || ''}`.trim() || 'Без имени';
            const stats = `Встреч: ${user.meetings_count || 0} | Избранных: ${user.favorites_count || 0} | Отзывов: ${user.reviews_count || 0}`;
            card.innerHTML = `
                <div class="admin-card-content">
                    <div class="admin-card-main">
                        <h3 class="admin-card-title">${escapeHtml(fullName)}</h3>
                        <p class="admin-card-author">${escapeHtml(user.email || '')}</p>
                        ${user.phone ? `<p class="admin-card-meta"><span>📞 ${escapeHtml(user.phone)}</span></p>` : ''}
                        ${user.birth_date ? `<p class="admin-card-meta"><span>📅 ${escapeHtml(user.birth_date)}</span></p>` : ''}
                        <p style="color: var(--color-text-light); font-size: var(--font-size-sm); margin-top: var(--spacing-xs);">${stats}</p>
                        <div class="admin-card-role" style="margin-top: var(--spacing-sm);">
                            <span class="role-badge role-${user.role || 'user'}">${escapeHtml(user.role || 'user')}</span>
                        </div>
                    </div>
                    <div class="admin-card-actions">
                        <button class="btn btn-secondary btn-sm" onclick="showUserDetails(${user.id})">Подробнее</button>
                        <select class="role-select" id="roleSelect_${user.id}" onchange="updateUserRole(${user.id}, this.value)">
                            <option value="user" ${(user.role || 'user') === 'user' ? 'selected' : ''}>user</option>
                            <option value="admin" ${user.role === 'admin' ? 'selected' : ''}>admin</option>
                        </select>
                    </div>
                </div>
            `;
            grid.appendChild(card);
        });

        // Пагинация
        if (data.pages > 1) {
            for (let i = 1; i <= data.pages; i++) {
                const btn = document.createElement('button');
                btn.className = `btn ${i === page ? 'btn-primary' : 'btn-secondary'} btn-sm`;
                btn.textContent = i;
                btn.onclick = () => {
                    usersPage = i;
                    loadUsers(i);
                };
                pagination.appendChild(btn);
            }
        }
    } catch (error) {
        container.innerHTML = `<div class="form-message error">Ошибка: ${error.message}</div>`;
    }
}

/**
 * Обновление роли пользователя
 */
async function updateUserRole(userId, newRole) {
    if (!confirm(`Изменить роль пользователя на "${newRole}"?`)) {
        // Восстанавливаем старое значение
        try {
            const user = await window.api.getUserById(userId);
            const select = document.getElementById(`roleSelect_${userId}`);
            if (select) {
                select.value = user.role || 'user';
            }
        } catch (error) {
            console.error('Ошибка при восстановлении роли:', error);
        }
        return;
    }

    try {
        await window.api.updateUserRole(userId, newRole);
        loadUsers(usersPage);
    } catch (error) {
        alert('Ошибка: ' + error.message);
        // Восстанавливаем старое значение
        try {
            const user = await window.api.getUserById(userId);
            const select = document.getElementById(`roleSelect_${userId}`);
            if (select) {
                select.value = user.role || 'user';
            }
        } catch (e) {
            console.error('Ошибка при восстановлении роли:', e);
        }
    }
}

/**
 * Показ сообщения об ошибке
 */
function showError(message) {
    const container = document.getElementById('booksList');
    if (container) {
        container.innerHTML = `<div class="form-message error">${escapeHtml(message)}</div>`;
    }
}

/**
 * Инициализация админ-панели
 */
async function initAdmin() {
    try {
        // Проверяем доступ
        const hasAccess = await checkAdminAccess();
        
        if (!hasAccess) {
            console.log('Доступ запрещён');
            return;
        }

        // Обработчики вкладок
        const tabButtons = document.querySelectorAll('.admin-tab-btn');
        if (tabButtons.length === 0) {
            console.error('Кнопки вкладок не найдены');
            return;
        }
        
        tabButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                switchTab(btn.dataset.tab);
            });
        });

        // Обработчики формы книги
        const addBookBtn = document.getElementById('addBookBtn');
        const cancelBookBtn = document.getElementById('cancelBookBtn');
        const bookForm = document.getElementById('bookForm');
        
        if (addBookBtn) {
            addBookBtn.addEventListener('click', showAddBookForm);
        } else {
            console.warn('Кнопка добавления книги не найдена');
        }
        
        if (cancelBookBtn) {
            cancelBookBtn.addEventListener('click', cancelBookForm);
        } else {
            console.warn('Кнопка отмены не найдена');
        }
        
        if (bookForm) {
            bookForm.addEventListener('submit', saveBook);
        } else {
            console.warn('Форма книги не найдена');
        }

        // Загружаем первую вкладку
        loadBooks(booksPage);
    } catch (error) {
        console.error('Ошибка при инициализации админ-панели:', error);
        showAccessDenied(`Ошибка инициализации: ${error.message}`);
    }
}

// Делаем функции доступными глобально
window.editBook = editBook;
window.deleteBook = deleteBook;
window.setCurrentBook = setCurrentBook;
window.updateUserRole = updateUserRole;
window.showUserDetails = showUserDetails;
window.closeUserDetails = closeUserDetails;
window.checkAdminAccess = checkAdminAccess; // Для отладки

// Запускаем инициализацию
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        console.log('DOM загружен, инициализация админ-панели...');
        initAdmin();
    });
} else {
    console.log('DOM уже загружен, инициализация админ-панели...');
    initAdmin();
}

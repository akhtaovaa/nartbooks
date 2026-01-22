/**
 * Модуль личного кабинета пользователя
 */

let currentProfile = null;

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
 * Форматирование списка
 */
function formatList(arr) {
    if (!arr || arr.length === 0) return 'Не указано';
    return arr.join(', ');
}

/**
 * Загрузка профиля пользователя
 */
async function loadProfile() {
    const container = document.getElementById('profileContainer');
    
    try {
        currentProfile = await window.api.getCurrentUser();
        
        container.innerHTML = `
            <div class="admin-card">
                <div class="admin-card-content">
                    <div class="admin-card-main">
                        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: var(--spacing-lg); flex-wrap: wrap; gap: var(--spacing-md);">
                            <div>
                                <h2 class="admin-card-title">${escapeHtml(currentProfile.first_name || '')} ${escapeHtml(currentProfile.last_name || '')}</h2>
                                <p style="color: var(--color-text-secondary); margin-top: var(--spacing-xs);">${escapeHtml(currentProfile.email || '')}</p>
                                ${currentProfile.phone ? `<p style="color: var(--color-text-light); margin-top: var(--spacing-xs); font-size: var(--font-size-sm);">📞 ${escapeHtml(currentProfile.phone)}</p>` : ''}
                                ${currentProfile.birth_date ? `<p style="color: var(--color-text-light); margin-top: var(--spacing-xs); font-size: var(--font-size-sm);">📅 ${escapeHtml(currentProfile.birth_date)}</p>` : ''}
                                ${currentProfile.role ? `<div style="margin-top: var(--spacing-sm);"><span class="role-badge role-${currentProfile.role}">${escapeHtml(currentProfile.role)}</span></div>` : ''}
                            </div>
                            <button class="btn btn-primary" id="editProfileBtn">Редактировать профиль</button>
                        </div>

                        <div style="margin-top: var(--spacing-xl); padding-top: var(--spacing-lg); border-top: 1px solid var(--color-border-light);">
                            <h3 style="font-family: var(--font-serif); font-size: var(--font-size-xl); font-weight: 400; margin-bottom: var(--spacing-md); color: var(--color-text-primary);">Интересы</h3>
                            <div style="display: grid; gap: var(--spacing-md);">
                                <div>
                                    <strong style="color: var(--color-text-secondary);">Любимые авторы:</strong>
                                    <p style="margin: var(--spacing-xs) 0 0; color: var(--color-text-primary); font-weight: 300;">${escapeHtml(formatList(currentProfile.fav_authors))}</p>
                                </div>
                                <div>
                                    <strong style="color: var(--color-text-secondary);">Любимые жанры:</strong>
                                    <p style="margin: var(--spacing-xs) 0 0; color: var(--color-text-primary); font-weight: 300;">${escapeHtml(formatList(currentProfile.fav_genres))}</p>
                                </div>
                                <div>
                                    <strong style="color: var(--color-text-secondary);">Любимые книги:</strong>
                                    <p style="margin: var(--spacing-xs) 0 0; color: var(--color-text-primary); font-weight: 300;">${escapeHtml(formatList(currentProfile.fav_books))}</p>
                                </div>
                                <div>
                                    <strong style="color: var(--color-text-secondary);">Книги для обсуждения:</strong>
                                    <p style="margin: var(--spacing-xs) 0 0; color: var(--color-text-primary); font-weight: 300;">${escapeHtml(formatList(currentProfile.discuss_books))}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Обработчик кнопки редактирования
        const editBtn = document.getElementById('editProfileBtn');
        if (editBtn) {
            editBtn.addEventListener('click', showEditForm);
        }
        
        // Загружаем встречи
        loadMeetings();
        
    } catch (error) {
        if (error.message && (error.message.includes('401') || error.message.includes('Токен'))) {
            container.innerHTML = `
                <div class="admin-form-card">
                    <h2 class="section-title">Требуется авторизация</h2>
                    <p class="form-description">Для доступа к личному кабинету необходимо войти в систему.</p>
                    <div class="form-submit">
                        <a href="auth.html?redirect=profile.html" class="btn btn-primary">Войти в систему</a>
                    </div>
                </div>
            `;
        } else {
            container.innerHTML = `<div class="form-message error">Ошибка: ${escapeHtml(error.message)}</div>`;
        }
    }
}

/**
 * Загрузка записанных встреч
 */
async function loadMeetings() {
    const section = document.getElementById('meetingsSection');
    const container = document.getElementById('meetingsList');
    
    try {
        const response = await window.api.getMyMeetings();
        const meetings = response.items || [];
        
        if (meetings.length === 0) {
            container.innerHTML = '<p class="form-description">Вы пока не записаны ни на одну встречу</p>';
        } else {
            container.innerHTML = '<div class="admin-grid"></div>';
            const grid = container.querySelector('.admin-grid');
            
            meetings.forEach(meeting => {
                const card = document.createElement('div');
                card.className = 'admin-card';
                card.innerHTML = `
                    <div class="admin-card-content">
                        <div class="admin-card-main">
                            <h3 class="admin-card-title">${escapeHtml(meeting.book_title || 'Без названия')}</h3>
                            <p class="admin-card-author">${escapeHtml(meeting.book_author || 'Автор не указан')}</p>
                            <div class="admin-card-meta">
                                <span>📅 ${escapeHtml(meeting.book_date || 'Дата не указана')}</span>
                                <span>📍 ${escapeHtml(meeting.book_location || 'Место не указано')}</span>
                            </div>
                            ${meeting.book_description ? `<p class="admin-card-description">${escapeHtml(meeting.book_description)}</p>` : ''}
                            <p style="color: var(--color-text-light); font-size: var(--font-size-sm); margin-top: var(--spacing-sm);">
                                Записан: ${escapeHtml(new Date(meeting.registered_at).toLocaleDateString('ru-RU'))}
                            </p>
                        </div>
                        <div class="admin-card-actions">
                            <button class="btn btn-danger btn-sm" onclick="cancelMeeting(${meeting.book_id})">Отменить запись</button>
                        </div>
                    </div>
                `;
                grid.appendChild(card);
            });
        }
        
        section.classList.remove('hidden');
    } catch (error) {
        container.innerHTML = `<div class="form-message error">Ошибка загрузки встреч: ${escapeHtml(error.message)}</div>`;
    }
}

/**
 * Показать форму редактирования
 */
function showEditForm() {
    if (!currentProfile) return;
    
    const formSection = document.getElementById('editFormSection');
    document.getElementById('firstNameInput').value = currentProfile.first_name || '';
    document.getElementById('lastNameInput').value = currentProfile.last_name || '';
    document.getElementById('phoneInput').value = currentProfile.phone || '';
    document.getElementById('birthDateInput').value = currentProfile.birth_date || '';
    document.getElementById('favAuthorsInput').value = formatList(currentProfile.fav_authors);
    document.getElementById('favGenresInput').value = formatList(currentProfile.fav_genres);
    document.getElementById('favBooksInput').value = formatList(currentProfile.fav_books);
    document.getElementById('discussBooksInput').value = formatList(currentProfile.discuss_books);
    
    formSection.classList.remove('hidden');
    window.scrollTo({ top: formSection.offsetTop - 20, behavior: 'smooth' });
}

/**
 * Скрыть форму редактирования
 */
function cancelEdit() {
    document.getElementById('editFormSection').classList.add('hidden');
    document.getElementById('profileStatus').classList.add('hidden');
}

/**
 * Обновление профиля
 */
async function updateProfile(e) {
    e.preventDefault();
    const statusDiv = document.getElementById('profileStatus');
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const btnText = submitBtn.querySelector('.btn-text');
    const btnSpinner = submitBtn.querySelector('.btn-spinner');
    
    statusDiv.classList.remove('hidden');
    statusDiv.innerHTML = '<div class="spinner"></div><p>Сохранение...</p>';
    submitBtn.disabled = true;
    btnText.textContent = 'Сохранение...';
    btnSpinner.classList.remove('hidden');
    
    try {
        const parseList = (str) => {
            if (!str || !str.trim()) return [];
            return str.split(',').map(s => s.trim()).filter(s => s);
        };
        
        const userData = {
            first_name: document.getElementById('firstNameInput').value.trim(),
            last_name: document.getElementById('lastNameInput').value.trim(),
            phone: document.getElementById('phoneInput').value.trim() || null,
            birth_date: document.getElementById('birthDateInput').value || null,
            fav_authors: parseList(document.getElementById('favAuthorsInput').value),
            fav_genres: parseList(document.getElementById('favGenresInput').value),
            fav_books: parseList(document.getElementById('favBooksInput').value),
            discuss_books: parseList(document.getElementById('discussBooksInput').value),
        };
        
        await window.api.updateProfile(userData);
        
        statusDiv.className = 'form-message success';
        statusDiv.textContent = 'Профиль успешно обновлён!';
        
        setTimeout(() => {
            cancelEdit();
            loadProfile();
        }, 1500);
    } catch (error) {
        statusDiv.className = 'form-message error';
        statusDiv.textContent = `Ошибка: ${error.message}`;
    } finally {
        submitBtn.disabled = false;
        btnText.textContent = 'Сохранить изменения';
        btnSpinner.classList.add('hidden');
    }
}

/**
 * Отменить запись на встречу
 */
async function cancelMeeting(bookId) {
    if (!confirm('Вы уверены, что хотите отменить запись на эту встречу?')) {
        return;
    }
    
    try {
        await window.api.cancelMeetingRegistration(bookId);
        loadMeetings();
    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
}

/**
 * Проверка валидности токена при загрузке страницы
 */
async function validateTokenOnLoad() {
    const token = localStorage.getItem('auth_token');
    if (!token) {
        console.log('Токен не найден, перенаправляем на авторизацию');
        window.location.href = 'auth.html?redirect=profile.html';
        return false;
    }
    
    console.log('Проверка токена...');
    
    // Ждём загрузки API
    if (!window.api || !window.api.getCurrentUser) {
        console.warn('API не загружен, ждём...');
        for (let i = 0; i < 20; i++) {
            await new Promise(resolve => setTimeout(resolve, 100));
            if (window.api && window.api.getCurrentUser) {
                break;
            }
        }
    }
    
    try {
        // Проверяем токен через запрос к /me
        const user = await window.api.getCurrentUser();
        console.log('✅ Токен валиден, пользователь:', user.email);
        return true;
    } catch (error) {
        // Удаляем токен ТОЛЬКО при явных ошибках авторизации
        const isAuthError = error.message && (
            error.message.includes('401') || 
            error.message.includes('Токен истек') ||
            error.message.includes('Неверный токен') ||
            error.message.includes('Токен авторизации не предоставлен')
        );
        
        if (isAuthError) {
            console.warn('❌ Токен невалиден, удаляем:', error.message);
            localStorage.removeItem('auth_token');
            window.location.href = 'auth.html?redirect=profile.html';
        } else {
            console.warn('⚠️ Ошибка при проверке (не удаляем токен):', error.message);
            // При других ошибках не удаляем токен, но всё равно перенаправляем
            // чтобы пользователь мог попробовать снова
        }
        return false;
    }
}

/**
 * Инициализация
 */
async function initProfile() {
    // Проверяем токен при загрузке
    const isValid = await validateTokenOnLoad();
    if (!isValid) {
        return; // Редирект уже произошёл в validateTokenOnLoad
    }
    
    const cancelBtn = document.getElementById('cancelEditBtn');
    const profileForm = document.getElementById('profileForm');
    
    if (cancelBtn) {
        cancelBtn.addEventListener('click', cancelEdit);
    }
    
    if (profileForm) {
        profileForm.addEventListener('submit', updateProfile);
    }
    
    loadProfile();
}

// Делаем функции доступными глобально
window.cancelMeeting = cancelMeeting;

// Запускаем инициализацию
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initProfile);
} else {
    initProfile();
}

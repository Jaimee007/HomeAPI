const getApiBaseUrl = () => {
            if (window.location.protocol === 'file:') {
                console.log('📍 Detectado: Archivo local → usando localhost');
                return 'http://localhost:8000';
            }
            if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
                console.log('📍 Detectado: Localhost → usando localhost');
                return 'http://localhost:8000';
            }
            console.log('📍 Detectado: Producción → usando homeapi.beadpaws.es');
            return 'https://homeapi.beadpaws.es';
        };

        const API_BASE_URL = getApiBaseUrl();
        const API_KEY = 'homeapi_default_key_2024';

        class MenuApp {
            constructor() {
                this.meals = [];
                this.categories = [];
                this.dailyMenus = {};
                this.tempRecipes = [];
                this.currentDate = new Date();
                this.selectedDay = null;
                this.selectedMealType = null;
                this.draggedMealData = null;
                this.filterText = '';
                this.selectedCategoryIds = [];
                this.pendingCategoryIds = [];
                this.currentMealView = 'all';
                this.favoriteMealIds = this.loadStoredIds('homeapi_favorite_meals');
                this.recentMealIds = this.loadStoredIds('homeapi_recent_meals');
                this.historyStack = [];
                this.maxHistoryEntries = 30;
                this.isRestoringHistory = false;
                console.log('📱 MenuApp constructor iniciado');
                console.log('📱 API URL:', API_BASE_URL);
                this.init();
            }

            loadStoredIds(key) {
                try {
                    const raw = localStorage.getItem(key);
                    const parsed = raw ? JSON.parse(raw) : [];
                    return Array.isArray(parsed) ? parsed.filter(n => Number.isInteger(n)) : [];
                } catch (e) {
                    return [];
                }
            }

            storeIds(key, ids) {
                localStorage.setItem(key, JSON.stringify(ids));
            }

            async init() {
                try {
                    console.log('🔄 Cargando datos de la API...');
                    await this.loadData();
                    console.log('✅ Datos cargados');
                    this.renderCalendar();
                    this.updateMealViewButtons();
                    this.updateHistoryUI();
                    this.setupEventListeners();
                    console.log('🎉 ¡MenuApp inicializado correctamente!');
                } catch (error) {
                    console.error('❌ Error en init():', error);
                }
            }

            cloneStateSnapshot() {
                return {
                    dailyMenus: JSON.parse(JSON.stringify(this.dailyMenus)),
                    tempRecipes: JSON.parse(JSON.stringify(this.tempRecipes))
                };
            }

            pushHistory(label) {
                if (this.isRestoringHistory) return;
                this.historyStack.push({
                    label,
                    timestamp: Date.now(),
                    snapshot: this.cloneStateSnapshot()
                });
                if (this.historyStack.length > this.maxHistoryEntries) {
                    this.historyStack.shift();
                }
                this.updateHistoryUI();
            }

            updateHistoryUI() {
                const list = document.getElementById('historyList');
                const undoBtn = document.getElementById('undoBtn');
                if (!list || !undoBtn) return;

                undoBtn.disabled = this.historyStack.length === 0;
                undoBtn.style.opacity = this.historyStack.length === 0 ? '0.6' : '1';
                undoBtn.style.cursor = this.historyStack.length === 0 ? 'not-allowed' : 'pointer';

                list.innerHTML = '';
                if (this.historyStack.length === 0) {
                    list.innerHTML = '<div class="history-item">Sin cambios recientes</div>';
                    return;
                }

                const recent = [...this.historyStack].slice(-8).reverse();
                recent.forEach(entry => {
                    const item = document.createElement('div');
                    item.className = 'history-item';
                    const time = new Date(entry.timestamp).toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
                    item.innerHTML = `${entry.label}<span class="history-item-time">${time}</span>`;
                    list.appendChild(item);
                });
            }

            async undoLastAction() {
                if (this.historyStack.length === 0) return;
                const entry = this.historyStack.pop();
                this.updateHistoryUI();
                await this.restoreSnapshot(entry.snapshot);
            }

            async restoreSnapshot(snapshot) {
                this.isRestoringHistory = true;
                try {
                    const targetMenus = snapshot.dailyMenus || {};
                    const currentMenus = this.dailyMenus || {};
                    const keys = new Set([...Object.keys(targetMenus), ...Object.keys(currentMenus)]);

                    for (const key of keys) {
                        const current = currentMenus[key];
                        const target = targetMenus[key];

                        const currentPersistent = current && !current.isTemp;
                        const targetPersistent = target && !target.isTemp;

                        if (currentPersistent && !targetPersistent) {
                            await this.deleteDailyMenu(current.id);
                            continue;
                        }

                        if (!currentPersistent && targetPersistent) {
                            await this.createDailyMenu({
                                mes: target.mes,
                                año: target.año,
                                dia: target.dia,
                                meal_lunch_id: target.meal_lunch_id ?? null,
                                meal_dinner_id: target.meal_dinner_id ?? null
                            });
                            continue;
                        }

                        if (currentPersistent && targetPersistent) {
                            const cLunch = current.meal_lunch_id ?? null;
                            const cDinner = current.meal_dinner_id ?? null;
                            const tLunch = target.meal_lunch_id ?? null;
                            const tDinner = target.meal_dinner_id ?? null;
                            if (cLunch !== tLunch || cDinner !== tDinner) {
                                await this.updateDailyMenu(current.id, {
                                    meal_lunch_id: tLunch,
                                    meal_dinner_id: tDinner
                                });
                            }
                        }
                    }

                    await this.loadData();
                    this.tempRecipes = JSON.parse(JSON.stringify(snapshot.tempRecipes || []));

                    Object.entries(targetMenus).forEach(([k, menu]) => {
                        if (menu && menu.isTemp) {
                            this.dailyMenus[k] = JSON.parse(JSON.stringify(menu));
                        }
                    });

                    this.renderCalendar();
                    this.updateSummary();
                } finally {
                    this.isRestoringHistory = false;
                }
            }

            setMealView(mode) {
                this.currentMealView = mode;
                this.updateMealViewButtons();
                this.filterMeals();
            }

            updateMealViewButtons() {
                const allBtn = document.getElementById('viewAllBtn');
                const favBtn = document.getElementById('viewFavoritesBtn');
                const recentBtn = document.getElementById('viewRecentBtn');
                if (!allBtn || !favBtn || !recentBtn) return;

                allBtn.classList.toggle('active', this.currentMealView === 'all');
                favBtn.classList.toggle('active', this.currentMealView === 'favorites');
                recentBtn.classList.toggle('active', this.currentMealView === 'recent');
            }

            getMealsForCurrentView() {
                if (this.currentMealView === 'favorites') {
                    return this.meals.filter(m => this.favoriteMealIds.includes(m.id));
                }
                if (this.currentMealView === 'recent') {
                    const map = new Map(this.meals.map(m => [m.id, m]));
                    return this.recentMealIds.map(id => map.get(id)).filter(Boolean);
                }
                return [...this.meals];
            }

            toggleFavorite(mealId, event) {
                if (event) {
                    event.stopPropagation();
                    event.preventDefault();
                }
                if (this.favoriteMealIds.includes(mealId)) {
                    this.favoriteMealIds = this.favoriteMealIds.filter(id => id !== mealId);
                } else {
                    this.favoriteMealIds.push(mealId);
                }
                this.storeIds('homeapi_favorite_meals', this.favoriteMealIds);
                this.filterMeals();
            }

            markAsRecent(mealId) {
                if (!mealId || mealId < 0) return;
                this.recentMealIds = [mealId, ...this.recentMealIds.filter(id => id !== mealId)].slice(0, 20);
                this.storeIds('homeapi_recent_meals', this.recentMealIds);
            }

            async loadData() {
                try {
                    const mealsRes = await fetch(`${API_BASE_URL}/meals`, { headers: { 'X-API-Key': API_KEY } });
                    const categoriesRes = await fetch(`${API_BASE_URL}/categories`, { headers: { 'X-API-Key': API_KEY } });
                    const menusRes = await fetch(`${API_BASE_URL}/daily-menu`, { headers: { 'X-API-Key': API_KEY } });

                    this.meals = await mealsRes.json();
                    this.categories = await categoriesRes.json();
                    
                    let menus = [];
                    if (menusRes.ok) {
                        menus = await menusRes.json();
                    }
                    
                    this.dailyMenus = {};
                    if (Array.isArray(menus)) {
                        menus.forEach(menu => {
                            const key = `${menu.año}-${String(menu.mes).padStart(2, '0')}-${String(menu.dia).padStart(2, '0')}`;
                            this.dailyMenus[key] = menu;
                        });
                    }

                    this.updateSummary();
                } catch (error) {
                    console.error('❌ Error cargando datos:', error);
                }
            }

            renderCalendar() {
                const container = document.getElementById('weeksContainer');
                container.innerHTML = '';

                const weeks = this.getWeeks();
                weeks.forEach((week, index) => {
                    const weekDiv = document.createElement('div');
                    weekDiv.className = 'week-container';
                    
                    const title = document.createElement('div');
                    title.className = 'week-title';
                    title.innerHTML = `Semana ${index === 0 ? 'Actual' : 'Próxima'} 
                        <span>${this.formatDateRange(week[0], week[6])}</span>`;
                    weekDiv.appendChild(title);

                    const grid = document.createElement('div');
                    grid.className = 'days-grid';

                    week.forEach(date => {
                        grid.appendChild(this.createDayCard(date));
                    });

                    weekDiv.appendChild(grid);
                    container.appendChild(weekDiv);
                });
            }

            createDayCard(date) {
                const dayCard = document.createElement('div');
                const isToday = this.isToday(date);
                dayCard.className = `day-card ${isToday ? 'today' : ''}`;

                const dayName = date.toLocaleDateString('es-ES', { weekday: 'short' });
                const dayNum = date.getDate();
                const key = this.getDateKey(date);
                const menu = this.dailyMenus[key];

                let html = `<div class="day-header">
                    <span class="day-number">${dayName} ${dayNum}</span>
                    ${isToday ? '<span class="today-badge">HOY</span>' : ''}
                </div>`;

                html += '<div class="meals-container">';

                const lunch = menu?.meal_lunch;
                html += `<div class="meal-slot">
                    <div class="meal-item ${lunch ? 'filled' : 'empty'}" draggable="${lunch ? 'true' : 'false'}" data-date="${key}" data-type="lunch" ondragstart="app.handleDragStart(event)" ondragend="app.handleDragEnd(event)" ondragover="app.handleDragOver(event)" ondragleave="app.handleDragLeave(event)" ondrop="app.handleDrop(event)" onclick="app.selectMeal(this, '${key}', 'lunch')">
                        ${lunch ? `
                            <div class="meal-info"><span class="meal-name">${lunch.nombre}</span></div>
                            <button class="btn-remove-meal" onclick="event.stopPropagation(); app.removeMeal('${key}', 'lunch')">✕</button>
                        ` : '<span style="color: #ccc;">+ Almuerzo</span>'}
                    </div>
                </div>`;

                const dinner = menu?.meal_dinner;
                html += `<div class="meal-slot">
                    <div class="meal-item ${dinner ? 'filled' : 'empty'}" draggable="${dinner ? 'true' : 'false'}" data-date="${key}" data-type="dinner" ondragstart="app.handleDragStart(event)" ondragend="app.handleDragEnd(event)" ondragover="app.handleDragOver(event)" ondragleave="app.handleDragLeave(event)" ondrop="app.handleDrop(event)" onclick="app.selectMeal(this, '${key}', 'dinner')">
                        ${dinner ? `
                            <div class="meal-info"><span class="meal-name">${dinner.nombre}</span></div>
                            <button class="btn-remove-meal" onclick="event.stopPropagation(); app.removeMeal('${key}', 'dinner')">✕</button>
                        ` : '<span style="color: #ccc;">+ Cena</span>'}
                    </div>
                </div>`;

                html += '</div>';
                dayCard.innerHTML = html;
                return dayCard;
            }

            isToday(date) {
                const today = new Date();
                return date.getDate() === today.getDate() && date.getMonth() === today.getMonth() && date.getFullYear() === today.getFullYear();
            }

            getDateKey(date) {
                return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
            }

            getWeeks() {
                const today = new Date();
                const currentWeek = this.getWeek(today);
                const nextWeek = this.getWeek(new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000));
                return [currentWeek, nextWeek];
            }

            getWeek(date) {
                const current = new Date(date);
                const first = current.getDate() - ((current.getDay() + 6) % 7);
                const week = [];
                for (let i = 0; i < 7; i++) {
                    const day = new Date(current.setDate(first + i));
                    week.push(new Date(day));
                }
                return week;
            }

            formatDateRange(start, end) {
                const startStr = start.toLocaleDateString('es-ES', { day: 'numeric', month: 'short' });
                const endStr = end.toLocaleDateString('es-ES', { day: 'numeric', month: 'short' });
                return `${startStr} - ${endStr}`;
            }

            selectMeal(element, dateKey, type) {
                this.selectedDay = dateKey;
                this.selectedMealType = type;
                this.openSelectMealModal();
            }

            async removeMeal(dateKey, type) {
                const menu = this.dailyMenus[dateKey];
                if (!menu) return;
                this.pushHistory('Quitar receta');

                const mealId = type === 'lunch' ? menu.meal_lunch_id : menu.meal_dinner_id;
                const otherMealId = type === 'lunch' ? menu.meal_dinner_id : menu.meal_lunch_id;

                if (!mealId && !otherMealId) {
                    delete this.dailyMenus[dateKey];
                    await this.deleteDailyMenu(menu.id);
                } else {
                    const updateData = type === 'lunch' 
                        ? { meal_lunch_id: null, meal_dinner_id: otherMealId || null }
                        : { meal_lunch_id: otherMealId || null, meal_dinner_id: null };
                    await this.updateDailyMenu(menu.id, updateData);
                }

                await this.loadData();
                this.renderCalendar();
            }

            openSelectMealModal() {
                const modal = document.getElementById('selectMealModal');
                this.renderCategoryFilterCheckboxes();
                
                this.filterText = '';
                this.selectedCategoryIds = [];
                this.pendingCategoryIds = [];
                document.getElementById('mealSearchInput').value = '';
                document.getElementById('categoryFilterPopup').classList.remove('active');
                this.updateCategoryFilterSummary();
                
                this.filterMeals();
                modal.classList.add('active');
            }

            filterMeals() {
                this.filterText = document.getElementById('mealSearchInput').value.toLowerCase();
                
                const list = document.getElementById('mealsSelectList');
                const noResults = document.getElementById('noResultsMessage');
                const noResultsText = document.getElementById('noResultsText');
                const addTempBtn = document.getElementById('addTempFromSearchBtn');
                list.innerHTML = '';
                
                const grouped = {};
                const noCategoryMeals = [];
                
                const baseMeals = this.getMealsForCurrentView();

                baseMeals.forEach(meal => {
                    if (this.filterText && !meal.nombre.toLowerCase().includes(this.filterText)) return;
                    
                    if (this.selectedCategoryIds.length > 0) {
                        const hasCategory = meal.categories && meal.categories.some(c => this.selectedCategoryIds.includes(c.id));
                        if (!hasCategory) return;
                    }
                    
                    if (meal.categories && meal.categories.length > 0) {
                        const categoryName = meal.categories[0].nombre;
                        if (!grouped[categoryName]) grouped[categoryName] = [];
                        grouped[categoryName].push(meal);
                    } else {
                        noCategoryMeals.push(meal);
                    }
                });
                
                let hasItems = false;
                Object.keys(grouped).sort().forEach(categoryName => {
                    const header = document.createElement('div');
                    header.className = 'meal-group-header';
                    header.innerHTML = categoryName + ' <span class="meal-count">' + grouped[categoryName].length + '</span>';
                    list.appendChild(header);
                    
                    grouped[categoryName].forEach(meal => {
                        const item = document.createElement('div');
                        item.className = 'item';
                        const isFav = this.favoriteMealIds.includes(meal.id);
                        item.innerHTML = '<div class="item-info"><div class="item-name" onclick="app.assignMealToDay(' + meal.id + ', false, null)" style="cursor: pointer; padding: 5px 0;">' + meal.nombre + '</div><div class="item-price">' + (meal.precio || 0).toFixed(2) + '€</div></div><button class="favorite-btn ' + (isFav ? 'active' : '') + '" onclick="app.toggleFavorite(' + meal.id + ', event)">' + (isFav ? '★' : '☆') + '</button>';
                        list.appendChild(item);
                        hasItems = true;
                    });
                });
                
                if (noCategoryMeals.length > 0) {
                    const header = document.createElement('div');
                    header.className = 'meal-group-header';
                    header.innerHTML = 'Sin categoría <span class="meal-count">' + noCategoryMeals.length + '</span>';
                    list.appendChild(header);
                    
                    noCategoryMeals.forEach(meal => {
                        const item = document.createElement('div');
                        item.className = 'item';
                        const isFav = this.favoriteMealIds.includes(meal.id);
                        item.innerHTML = '<div class="item-info"><div class="item-name" onclick="app.assignMealToDay(' + meal.id + ', false, null)" style="cursor: pointer; padding: 5px 0;">' + meal.nombre + '</div><div class="item-price">' + (meal.precio || 0).toFixed(2) + '€</div></div><button class="favorite-btn ' + (isFav ? 'active' : '') + '" onclick="app.toggleFavorite(' + meal.id + ', event)">' + (isFav ? '★' : '☆') + '</button>';
                        list.appendChild(item);
                        hasItems = true;
                    });
                }
                
                noResults.style.display = hasItems ? 'none' : 'block';
                if (!hasItems) {
                    const trimmedSearch = this.getCurrentSearchText();
                    const canCreateTemp = trimmedSearch.length > 0;
                    noResultsText.textContent = canCreateTemp
                        ? `No existe "${trimmedSearch}"`
                        : '❌ No se encontraron recetas';
                    addTempBtn.style.display = canCreateTemp ? 'inline-flex' : 'none';
                }
            }

            getCurrentSearchText() {
                return (document.getElementById('mealSearchInput')?.value || '').trim();
            }

            assignSearchAsTempRecipe() {
                const name = this.getCurrentSearchText();
                if (!name) return;
                this.assignMealToDay(-1, true, { nombre: name, precio: 0, isTemp: true });
            }

            clearFilters() {
                document.getElementById('mealSearchInput').value = '';
                this.selectedCategoryIds = [];
                this.pendingCategoryIds = [];
                this.setCategoryFilterCheckboxes(this.pendingCategoryIds);
                this.updateCategoryFilterSummary();
                this.filterMeals();
            }

            renderCategoryFilterCheckboxes() {
                const container = document.getElementById('categoryFilterCheckboxes');
                container.innerHTML = '';
                this.categories.forEach(cat => {
                    const label = document.createElement('label');
                    label.className = 'checkbox-item';
                    const checked = this.pendingCategoryIds.includes(cat.id) ? 'checked' : '';
                    label.innerHTML = `<input type="checkbox" value="${cat.id}" ${checked}><span>${cat.nombre}</span>`;
                    container.appendChild(label);
                });
            }

            setCategoryFilterCheckboxes(ids) {
                const checks = document.querySelectorAll('#categoryFilterCheckboxes input[type="checkbox"]');
                checks.forEach(cb => {
                    cb.checked = ids.includes(parseInt(cb.value));
                });
            }

            toggleCategoryFilterPopup() {
                const popup = document.getElementById('categoryFilterPopup');
                popup.classList.toggle('active');
            }

            resetCategoryFilterSelection() {
                this.pendingCategoryIds = [];
                this.setCategoryFilterCheckboxes(this.pendingCategoryIds);
            }

            applyCategoryFilterSelection() {
                const selected = Array.from(document.querySelectorAll('#categoryFilterCheckboxes input:checked')).map(cb => parseInt(cb.value));
                this.pendingCategoryIds = selected;
                this.selectedCategoryIds = [...selected];
                this.updateCategoryFilterSummary();
                document.getElementById('categoryFilterPopup').classList.remove('active');
                this.filterMeals();
            }

            updateCategoryFilterSummary() {
                const summary = document.getElementById('categoryFilterSummary');
                if (this.selectedCategoryIds.length === 0) {
                    summary.textContent = 'Sin categorías seleccionadas';
                    return;
                }
                const names = this.categories
                    .filter(c => this.selectedCategoryIds.includes(c.id))
                    .map(c => c.nombre);
                summary.textContent = `Filtrando por: ${names.join(', ')}`;
            }

            handleDragStart(e) {
                const mealItem = e.target.closest('.meal-item');
                if (!mealItem) {
                    e.preventDefault();
                    return;
                }

                const sourceDate = mealItem.dataset.date;
                const sourceType = mealItem.dataset.type;
                const sourceMenu = this.dailyMenus[sourceDate];
                const sourceMeal = sourceType === 'lunch' ? sourceMenu?.meal_lunch : sourceMenu?.meal_dinner;

                if (!sourceMeal) {
                    e.preventDefault();
                    return;
                }

                mealItem.classList.add('dragging');
                this.draggedMealData = {
                    sourceDate,
                    sourceType,
                    mealName: sourceMeal.nombre
                };
                e.dataTransfer.effectAllowed = 'move';
                e.dataTransfer.setData('text/plain', sourceMeal.nombre);
            }

            handleDragEnd(e) {
                const mealItem = e.target.closest('.meal-item');
                if (mealItem) mealItem.classList.remove('dragging');
            }

            handleDragOver(e) {
                const mealItem = e.target.closest('.meal-item');
                if (mealItem && this.draggedMealData) {
                    e.preventDefault();
                    e.dataTransfer.dropEffect = 'move';
                    mealItem.classList.add('drag-over');
                }
            }

            handleDragLeave(e) {
                const mealItem = e.target.closest('.meal-item');
                if (mealItem) {
                    mealItem.classList.remove('drag-over');
                }
            }

            handleDrop(e) {
                e.preventDefault();
                const targetMealItem = e.target.closest('.meal-item');
                
                if (!targetMealItem || !this.draggedMealData) return;
                
                targetMealItem.classList.remove('drag-over');
                
                const targetDate = targetMealItem.dataset.date;
                const targetType = targetMealItem.dataset.type;
                
                if (targetDate === this.draggedMealData.sourceDate && targetType === this.draggedMealData.sourceType) {
                    return;
                }
                
                this.swapOrMoveMeal(this.draggedMealData.sourceDate, this.draggedMealData.sourceType, targetDate, targetType);
                this.draggedMealData = null;
            }

            async swapOrMoveMeal(sourceDate, sourceType, targetDate, targetType) {
                this.pushHistory('Mover/intercambiar receta');
                const sourceMenu = this.dailyMenus[sourceDate];
                const targetMenu = this.dailyMenus[targetDate];
                
                if (!sourceMenu) return;
                
                const sourceMealKey = sourceType === 'lunch' ? 'meal_lunch' : 'meal_dinner';
                const sourceMealIdKey = sourceType === 'lunch' ? 'meal_lunch_id' : 'meal_dinner_id';
                const sourceMeal = sourceMenu[sourceMealKey];
                
                if (!sourceMeal) return;
                
                const targetMealKey = targetType === 'lunch' ? 'meal_lunch' : 'meal_dinner';
                const targetMealIdKey = targetType === 'lunch' ? 'meal_lunch_id' : 'meal_dinner_id';
                const targetMeal = targetMenu ? targetMenu[targetMealKey] : null;

                if (sourceMeal?.isTemp || targetMeal?.isTemp) {
                    if (!targetMenu) {
                        const parts = targetDate.split('-');
                        this.dailyMenus[targetDate] = {
                            id: 'temp_menu_' + Date.now(),
                            año: parseInt(parts[0]),
                            mes: parseInt(parts[1]),
                            dia: parseInt(parts[2]),
                            meal_lunch_id: null,
                            meal_dinner_id: null,
                            meal_lunch: null,
                            meal_dinner: null,
                            isTemp: true
                        };
                    }
                    this.dailyMenus[targetDate][targetMealKey] = sourceMeal || null;
                    this.dailyMenus[sourceDate][sourceMealKey] = targetMeal || null;
                } else {
                    const sourceOtherIdKey = sourceType === 'lunch' ? 'meal_dinner_id' : 'meal_lunch_id';
                    const targetOtherIdKey = targetType === 'lunch' ? 'meal_dinner_id' : 'meal_lunch_id';

                    if (!targetMenu) {
                        const parts = targetDate.split('-');
                        const createData = targetType === 'lunch'
                            ? { mes: parseInt(parts[1]), año: parseInt(parts[0]), dia: parseInt(parts[2]), meal_lunch_id: sourceMeal.id, meal_dinner_id: null }
                            : { mes: parseInt(parts[1]), año: parseInt(parts[0]), dia: parseInt(parts[2]), meal_lunch_id: null, meal_dinner_id: sourceMeal.id };
                        await this.createDailyMenu(createData);

                        await this.updateDailyMenu(sourceMenu.id, {
                            [sourceMealIdKey]: null,
                            [sourceOtherIdKey]: sourceMenu[sourceOtherIdKey] || null
                        });
                    } else {
                        if (sourceMenu.id === targetMenu.id) {
                            await this.updateDailyMenu(sourceMenu.id, {
                                meal_lunch_id: sourceType === 'lunch'
                                    ? (targetMeal ? targetMeal.id : null)
                                    : sourceMeal.id,
                                meal_dinner_id: sourceType === 'dinner'
                                    ? (targetMeal ? targetMeal.id : null)
                                    : sourceMeal.id
                            });
                        } else {
                            await this.updateDailyMenu(sourceMenu.id, {
                                [sourceMealIdKey]: targetMeal ? targetMeal.id : null,
                                [sourceOtherIdKey]: sourceMenu[sourceOtherIdKey] || null
                            });

                            await this.updateDailyMenu(targetMenu.id, {
                                [targetMealIdKey]: sourceMeal.id,
                                [targetOtherIdKey]: targetMenu[targetOtherIdKey] || null
                            });
                        }
                    }
                }
                
                await this.loadData();
                this.renderCalendar();
                this.updateSummary();
            }

            async assignMealToDay(mealId, isTemp = false, tempRecipe = null) {
                this.pushHistory(isTemp ? 'Asignar receta temporal' : 'Asignar receta');
                const parts = this.selectedDay.split('-');
                const menu = this.dailyMenus[this.selectedDay];
                
                let mealData = null;
                if (isTemp && tempRecipe) {
                    mealData = {
                        id: 'temp_' + Date.now(),
                        nombre: tempRecipe.nombre,
                        precio: tempRecipe.precio,
                        isTemp: true
                    };
                } else if (mealId === -1) {
                    return;
                } else {
                    mealData = this.meals.find(m => m.id === mealId);
                    if (mealData) this.markAsRecent(mealData.id);
                }

                if (!mealData) return;

                if (isTemp) {
                    if (!this.dailyMenus[this.selectedDay]) {
                        this.dailyMenus[this.selectedDay] = {
                            id: 'temp_menu_' + Date.now(),
                            año: parseInt(parts[0]),
                            mes: parseInt(parts[1]),
                            dia: parseInt(parts[2]),
                            meal_lunch_id: null,
                            meal_dinner_id: null,
                            meal_lunch: null,
                            meal_dinner: null,
                            isTemp: true
                        };
                    }
                    
                    if (this.selectedMealType === 'lunch') {
                        this.dailyMenus[this.selectedDay].meal_lunch = mealData;
                    } else {
                        this.dailyMenus[this.selectedDay].meal_dinner = mealData;
                    }
                } else {
                    if (menu) {
                        const updateData = this.selectedMealType === 'lunch' ? { meal_lunch_id: mealId, meal_dinner_id: menu.meal_dinner_id ?? null } : { meal_lunch_id: menu.meal_lunch_id ?? null, meal_dinner_id: mealId };
                        await this.updateDailyMenu(menu.id, updateData);
                    } else {
                        const createData = this.selectedMealType === 'lunch' ? { mes: parseInt(parts[1]), año: parseInt(parts[0]), dia: parseInt(parts[2]), meal_lunch_id: mealId, meal_dinner_id: null } : { mes: parseInt(parts[1]), año: parseInt(parts[0]), dia: parseInt(parts[2]), meal_lunch_id: null, meal_dinner_id: mealId };
                        await this.createDailyMenu(createData);
                    }
                    
                    await this.loadData();
                }

                closeModal('selectMealModal');
                this.renderCalendar();
                this.updateSummary();
            }

            async createDailyMenu(data) {
                try {
                    const response = await fetch(`${API_BASE_URL}/daily-menu`, {
                        method: 'POST',
                        headers: { 'X-API-Key': API_KEY, 'Content-Type': 'application/json' },
                        body: JSON.stringify(data)
                    });
                    return await response.json();
                } catch (error) {
                    console.error('Error creando menú:', error);
                }
            }

            async updateDailyMenu(id, data) {
                try {
                    const response = await fetch(`${API_BASE_URL}/daily-menu/${id}`, {
                        method: 'PUT',
                        headers: { 'X-API-Key': API_KEY, 'Content-Type': 'application/json' },
                        body: JSON.stringify(data)
                    });
                    return await response.json();
                } catch (error) {
                    console.error('Error actualizando menú:', error);
                }
            }

            async deleteDailyMenu(id) {
                try {
                    await fetch(`${API_BASE_URL}/daily-menu/${id}`, {
                        method: 'DELETE',
                        headers: { 'X-API-Key': API_KEY }
                    });
                } catch (error) {
                    console.error('Error eliminando menú:', error);
                }
            }

            updateSummary() {
                document.getElementById('totalMeals').textContent = this.meals.length;
                document.getElementById('totalCategories').textContent = this.categories.length;
                
                let weekTotal = 0;
                const weeks = this.getWeeks();
                weeks[0].forEach(date => {
                    const key = this.getDateKey(date);
                    const menu = this.dailyMenus[key];
                    if (menu?.meal_lunch) weekTotal += menu.meal_lunch.precio;
                    if (menu?.meal_dinner) weekTotal += menu.meal_dinner.precio;
                });
                
                document.getElementById('weekTotal').textContent = '€' + weekTotal.toFixed(2);
            }

            setupEventListeners() {
                document.getElementById('addMealForm').addEventListener('submit', (e) => this.handleAddMeal(e));
                document.getElementById('addMealForm2').addEventListener('submit', (e) => this.handleAddMeal2(e));
                document.getElementById('addCategoryForm').addEventListener('submit', (e) => this.handleAddCategory(e));
            }

            async handleAddMeal(e) {
                e.preventDefault();
                const name = document.getElementById('mealName').value;
                const price = parseFloat(document.getElementById('mealPrice').value);
                
                const categoryIds = Array.from(document.querySelectorAll('#categoriesCheckboxes input:checked')).map(cb => parseInt(cb.value));

                try {
                    const response = await fetch(`${API_BASE_URL}/meals`, {
                        method: 'POST',
                        headers: { 'X-API-Key': API_KEY, 'Content-Type': 'application/json' },
                        body: JSON.stringify({ nombre: name, precio: price, category_ids: categoryIds })
                    });

                    if (response.ok) {
                        this.showMessage('addMealMessage', 'Receta creada correctamente', 'success');
                        setTimeout(() => {
                            closeModal('addMealModal');
                            document.getElementById('addMealForm').reset();
                        }, 1000);
                        await this.loadData();
                        this.renderCalendar();
                    } else {
                        this.showMessage('addMealMessage', 'Error al crear la receta', 'error');
                    }
                } catch (error) {
                    this.showMessage('addMealMessage', 'Error: ' + error.message, 'error');
                }
            }

            async handleAddMeal2(e) {
                e.preventDefault();
                const name = document.getElementById('mealName2').value;
                const price = parseFloat(document.getElementById('mealPrice2').value);
                
                const categoryIds = Array.from(document.querySelectorAll('#categoriesCheckboxes2 input:checked')).map(cb => parseInt(cb.value));

                try {
                    const response = await fetch(`${API_BASE_URL}/meals`, {
                        method: 'POST',
                        headers: { 'X-API-Key': API_KEY, 'Content-Type': 'application/json' },
                        body: JSON.stringify({ nombre: name, precio: price, category_ids: categoryIds })
                    });

                    if (response.ok) {
                        document.getElementById('addMealForm2').reset();
                        await this.loadData();
                        this.renderMealsList();
                        this.renderCategoriesCheckboxes2();
                    } else {
                        alert('Error al crear la receta');
                    }
                } catch (error) {
                    alert('Error: ' + error.message);
                }
            }

            async handleAddCategory(e) {
                e.preventDefault();
                const name = document.getElementById('categoryName').value;

                try {
                    const response = await fetch(`${API_BASE_URL}/categories`, {
                        method: 'POST',
                        headers: { 'X-API-Key': API_KEY, 'Content-Type': 'application/json' },
                        body: JSON.stringify({ nombre: name })
                    });

                    if (response.ok) {
                        this.showMessage('categoriesMessage', 'Categoría creada correctamente', 'success');
                        document.getElementById('categoryName').value = '';
                        await this.loadData();
                        this.renderCategoriesList();
                        this.renderCategoriesCheckboxes();
                    } else {
                        this.showMessage('categoriesMessage', 'Error al crear la categoría', 'error');
                    }
                } catch (error) {
                    this.showMessage('categoriesMessage', 'Error: ' + error.message, 'error');
                }
            }

            renderCategoriesCheckboxes() {
                const container = document.getElementById('categoriesCheckboxes');
                container.innerHTML = '';
                this.categories.forEach(cat => {
                    const label = document.createElement('label');
                    label.className = 'checkbox-item';
                    label.innerHTML = `<input type="checkbox" value="${cat.id}"><span>${cat.nombre}</span>`;
                    container.appendChild(label);
                });
            }

            renderCategoriesList() {
                const container = document.getElementById('categoriesList');
                container.innerHTML = '';
                this.categories.forEach(cat => {
                    const item = document.createElement('div');
                    item.className = 'item';
                    item.innerHTML = `<div class="item-name">${cat.nombre}</div><button class="btn-small btn-delete" onclick="app.deleteCategory(${cat.id})">Eliminar</button>`;
                    container.appendChild(item);
                });
            }

            async deleteCategory(id) {
                if (!confirm('¿Eliminar esta categoría?')) return;
                
                try {
                    const response = await fetch(`${API_BASE_URL}/categories/${id}`, {
                        method: 'DELETE',
                        headers: { 'X-API-Key': API_KEY }
                    });

                    if (response.ok) {
                        this.showMessage('categoriesMessage', 'Categoría eliminada', 'success');
                        await this.loadData();
                        this.renderCategoriesList();
                        this.renderCategoriesCheckboxes();
                    }
                } catch (error) {
                    console.error('Error:', error);
                }
            }

            showMessage(elementId, message, type) {
                const element = document.getElementById(elementId);
                element.innerHTML = '<div class="' + type + '">' + message + '</div>';
                setTimeout(() => { element.innerHTML = ''; }, 3000);
            }

            renderMealsList() {
                const container = document.getElementById('mealsList');
                container.innerHTML = '';
                this.meals.forEach(meal => {
                    const item = document.createElement('div');
                    item.className = 'item';
                    item.innerHTML = `<div class="item-info"><div class="item-name">${meal.nombre}</div><div class="item-price">${(meal.precio || 0).toFixed(2)}€</div></div><div class="item-actions"><button class="btn-small btn-edit" onclick="app.editMeal(${meal.id})">Editar</button><button class="btn-small btn-delete" onclick="app.deleteMeal(${meal.id})">Eliminar</button></div>`;
                    container.appendChild(item);
                });
            }

            renderCategoriesCheckboxes2() {
                const container = document.getElementById('categoriesCheckboxes2');
                container.innerHTML = '';
                this.categories.forEach(cat => {
                    const label = document.createElement('label');
                    label.className = 'checkbox-item';
                    label.innerHTML = `<input type="checkbox" value="${cat.id}"><span>${cat.nombre}</span>`;
                    container.appendChild(label);
                });
            }

            async deleteMeal(id) {
                if (!confirm('¿Eliminar esta receta?')) return;
                
                try {
                    const response = await fetch(`${API_BASE_URL}/meals/${id}`, {
                        method: 'DELETE',
                        headers: { 'X-API-Key': API_KEY }
                    });

                    if (response.ok) {
                        this.showMessage('mealsMessage', 'Receta eliminada', 'success');
                        await this.loadData();
                        this.renderMealsList();
                        this.renderCalendar();
                    }
                } catch (error) {
                    console.error('Error:', error);
                }
            }

            editMeal(id) {
                this.showMessage('mealsMessage', 'Editar recetas - próximamente', 'error');
            }
        }

        function openAddMealModal() {
            if (!window.app) return;
            try {
                window.app.renderCategoriesCheckboxes();
                document.getElementById('addMealModal').classList.add('active');
            } catch (error) {
                console.error('❌ Error abriendo modal:', error);
            }
        }

        function openManageMealsModal() {
            if (!window.app) return;
            try {
                window.app.renderMealsList();
                window.app.renderCategoriesCheckboxes2();
                document.getElementById('manageMealsModal').classList.add('active');
            } catch (error) {
                console.error('❌ Error abriendo modal:', error);
            }
        }

        function openManageCategoriesModal() {
            if (!window.app) return;
            try {
                window.app.renderCategoriesList();
                document.getElementById('manageCategoriesModal').classList.add('active');
            } catch (error) {
                console.error('❌ Error abriendo modal:', error);
            }
        }

        function closeModal(modalId) {
            document.getElementById(modalId).classList.remove('active');
        }

        window.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                e.target.classList.remove('active');
            }
        });

        let app;
        console.log('%c🚀 HomeAPI - Gestor de Menú Semanal', 'color: #FF69B4; font-size: 14px; font-weight: bold;');
        console.log('📍 URL Base de API:', API_BASE_URL);
        
        document.addEventListener('DOMContentLoaded', () => {
            console.log('%c✅ Inicializando aplicación...', 'color: #5FB35F; font-size: 12px;');
            app = new MenuApp();
            window.app = app;
            console.log('✅ Aplicación lista');
        });


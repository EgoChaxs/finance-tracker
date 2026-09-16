// FamilyVault frontend
// CRUD data comes from Flask APIs. Dashboard/report calculations below are
// temporary presentation calculations until dedicated statistics endpoints exist.

const state = {
  currentUser: null,
  transactions: [],
  categories: [],
  budgets: [],
  goals: [],

  currentPage: 'dashboard',
  sortField: 'date',
  sortDir: 'desc',
  filterType: '',
  filterCategory: '',
  filterDateFrom: '',
  filterDateTo: '',
  searchQuery: '',

  editingTransactionId: null,
  editingCategoryId: null,
  confirmCallback: null,

  currentPageNum: 1,
  itemsPerPage: 10,
  chartPeriod: '1y',
};

let incomeExpenseChartInstance = null;
let reportBarChartInstance = null;
let reportIncomePieChartInstance = null;
let reportPieChartInstance = null;
let reportBalanceTrendChartInstance = null;


// ==================== API ====================

async function apiRequest(url, options = {}) {
  const config = {
    credentials: 'same-origin',
    ...options,
    headers: {
      ...(options.body ? { 'Content-Type': 'application/json' } : {}),
      ...(options.headers || {}),
    },
  };

  const response = await fetch(url, config);

  let data = null;
  const contentType = response.headers.get('content-type') || '';

  if (contentType.includes('application/json')) {
    data = await response.json();
  }

  if (response.status === 401) {
    window.location.href = '/login';
    throw new Error('Authentication required');
  }

  if (!response.ok) {
    throw new Error(data?.message || `Request failed with status ${response.status}`);
  }

  return data;
}

async function refreshTransactions() {
  const data = await apiRequest('/api/transactions');
  state.transactions = data.transactions || [];
  document.getElementById('txCount').textContent = state.transactions.length;
}

async function refreshCategories() {
  const data = await apiRequest('/api/categories');
  state.categories = data.categories || [];
}

async function refreshBudgets() {
  const data = await apiRequest('/api/budgets');
  state.budgets = data.budgets || [];
}

async function refreshGoals() {
  const data = await apiRequest('/api/goals');
  const goals = data.goals || [];

  state.goals = await Promise.all(
    goals.map(async goal => {
      const contributionsData = await apiRequest(
        `/api/goals/${goal.goal_id}/contributions`
      );

      const contributions = contributionsData.contributions || [];

      return {
        ...goal,
        contributions,
        current_amount: contributions.reduce(
          (sum, contribution) => sum + Number(contribution.amount),
          0
        ),
      };
    })
  );
}

async function refreshFinanceData() {
  await Promise.all([
    refreshTransactions(),
    refreshCategories(),
    refreshBudgets(),
    refreshGoals(),
  ]);
}


// ==================== HELPERS ====================

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function formatCurrency(amount) {
  const value = Number(amount) || 0;

  return (value < 0 ? '-$' : '$') +
    Math.abs(value).toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
}

function formatDateTime(dateStr) {
  if (!dateStr) return '—';

  const date = new Date(dateStr);

  if (Number.isNaN(date.getTime())) {
    return dateStr;
  }

  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function dateOnly(dateStr) {
  return String(dateStr || '').slice(0, 10);
}

function localDateTimeValue(date = new Date()) {
  const pad = value => String(value).padStart(2, '0');

  return [
    date.getFullYear(),
    '-',
    pad(date.getMonth() + 1),
    '-',
    pad(date.getDate()),
    'T',
    pad(date.getHours()),
    ':',
    pad(date.getMinutes()),
  ].join('');
}

function currentMonthStart() {
  const now = new Date();
  const pad = value => String(value).padStart(2, '0');

  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-01T00:00:00`;
}

function sameMonth(a, b) {
  return String(a || '').slice(0, 7) === String(b || '').slice(0, 7);
}

function getCategoryInfo(category) {
  if (!category || category.category_id == null) {
    return {
      category_id: null,
      name: 'Unknown',
      icon: 'fas fa-tag',
      color: '#636e72',
    };
  }

  return {
    category_id: category.category_id,
    name: category.name || 'Unknown',
    icon: category.icon || 'fas fa-tag',
    color: category.color || '#636e72',
  };
}

function updateUserCard() {
  if (!state.currentUser) return;

  const name = state.currentUser.name || 'Family Member';

  document.getElementById('userName').textContent = name;

  const initials = name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map(part => part[0].toUpperCase())
    .join('') || 'FV';

  document.getElementById('userAvatar').textContent = initials;
}


// ==================== NAVIGATION ====================

function navigateTo(page) {
  state.currentPage = page;

  document.querySelectorAll('.page-section').forEach(section => {
    section.classList.remove('active');
  });

  document.getElementById(`page-${page}`)?.classList.add('active');

  document.querySelectorAll('.nav-item').forEach(item => {
    item.classList.remove('active');
  });

  document.querySelector(`.nav-item[data-page="${page}"]`)?.classList.add('active');

  const titles = {
    dashboard: 'Dashboard',
    transactions: 'Transactions',
    categories: 'Categories',
    budgets: 'Budgets',
    goals: 'Savings Goals',
    reports: 'Reports',
  };

  document.getElementById('pageTitle').textContent = titles[page] || page;

  closeSidebar();
  renderPage(page);
}

document.querySelectorAll('.nav-item').forEach(item => {
  item.addEventListener('click', () => navigateTo(item.dataset.page));
});


// ==================== SIDEBAR ====================

const menuToggle = document.getElementById('menuToggle');
const sidebar = document.getElementById('sidebar');
const sidebarOverlay = document.getElementById('sidebarOverlay');

menuToggle.addEventListener('click', () => {
  sidebar.classList.toggle('open');
  sidebarOverlay.classList.toggle('active');
});

sidebarOverlay.addEventListener('click', closeSidebar);

function closeSidebar() {
  sidebar.classList.remove('open');
  sidebarOverlay.classList.remove('active');
}


// ==================== LOGOUT ====================

document.getElementById('logoutButton').addEventListener('click', async () => {
  try {
    await apiRequest('/auth/logout', {
      method: 'POST',
    });

    window.location.href = '/login';
  } catch (error) {
    showToast(error.message, 'error');
  }
});


// ==================== TOASTS / CONFIRMATION ====================

function showToast(message, type = 'success') {
  const container = document.getElementById('toastContainer');

  const icons = {
    success: 'fas fa-check-circle',
    error: 'fas fa-times-circle',
    info: 'fas fa-info-circle',
  };

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <i class="toast-icon ${icons[type] || icons.info}"></i>
    <span class="toast-message">${escapeHtml(message)}</span>
  `;

  container.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}

function showConfirm(title, message, callback) {
  document.getElementById('confirmTitle').textContent = title;
  document.getElementById('confirmMessage').textContent = message;
  state.confirmCallback = callback;
  document.getElementById('confirmModal').classList.add('active');
}

async function confirmAction() {
  const callback = state.confirmCallback;
  state.confirmCallback = null;

  try {
    if (callback) {
      await callback();
    }
  } catch (error) {
    showToast(error.message, 'error');
  } finally {
    closeConfirm();
  }
}

function closeConfirm() {
  document.getElementById('confirmModal').classList.remove('active');
  state.confirmCallback = null;
}


// ==================== TRANSACTIONS ====================

function setType(type, selectedCategoryId = null) {
  const expenseButton = document.getElementById('btnExpense');
  const incomeButton = document.getElementById('btnIncome');

  expenseButton.className =
    'type-btn' + (type === 'expense' ? ' active-expense' : '');

  incomeButton.className =
    'type-btn' + (type === 'income' ? ' active-income' : '');

  populateTransactionCategorySelect(selectedCategoryId);
}

function populateTransactionCategorySelect(selectedCategoryId = null) {
  const select = document.getElementById('txCategory');

  const currentType =
    document.getElementById('btnExpense').classList.contains('active-expense')
      ? 'expense'
      : 'income';

  select.innerHTML = '<option value="">Select category</option>';

  state.categories
    .filter(category =>
      category.type === currentType || category.type === 'both'
    )
    .forEach(category => {
      const option = document.createElement('option');
      option.value = category.category_id;
      option.textContent = category.name;
      option.selected =
        Number(selectedCategoryId) === Number(category.category_id);
      select.appendChild(option);
    });
}

function openModal(transactionId = null) {
  state.editingTransactionId = transactionId;

  const modal = document.getElementById('transactionModal');
  const title = document.getElementById('modalTitle');

  if (transactionId !== null) {
    const transaction = state.transactions.find(
      item => item.transaction_id === transactionId
    );

    if (!transaction) {
      showToast('Transaction not found', 'error');
      return;
    }

    title.textContent = 'Edit Transaction';
    document.getElementById('txAmount').value = transaction.amount;
    document.getElementById('txDate').value =
      String(transaction.occurred_at).slice(0, 16);

    setType(
      transaction.type,
      transaction.category?.category_id ?? null
    );

    document.getElementById('txDescription').value =
      transaction.description || '';

    document.getElementById('txNotes').value =
      transaction.notes || '';
  } else {
    title.textContent = 'Add Transaction';
    document.getElementById('txAmount').value = '';
    document.getElementById('txDate').value = localDateTimeValue();
    document.getElementById('txDescription').value = '';
    document.getElementById('txNotes').value = '';
    setType('expense');
  }

  modal.classList.add('active');
}

function closeModal() {
  document.getElementById('transactionModal').classList.remove('active');
  state.editingTransactionId = null;
}

async function saveTransaction() {
  const amount = Number(document.getElementById('txAmount').value);
  const occurredAt = document.getElementById('txDate').value;
  const categoryId = Number(document.getElementById('txCategory').value);
  const description = document.getElementById('txDescription').value.trim();
  const notes = document.getElementById('txNotes').value.trim() || null;

  const type =
    document.getElementById('btnExpense').classList.contains('active-expense')
      ? 'expense'
      : 'income';

  if (!amount || amount <= 0) {
    return showToast('Please enter a valid amount', 'error');
  }

  if (!occurredAt) {
    return showToast('Please select a date and time', 'error');
  }

  if (!categoryId) {
    return showToast('Please select a category', 'error');
  }

  if (!description) {
    return showToast('Please enter a description', 'error');
  }

  const payload = {
    category_id: categoryId,
    type,
    amount,
    occurred_at: occurredAt,
    description,
    notes,
  };

  try {
    if (state.editingTransactionId !== null) {
      await apiRequest(
        `/api/transactions/${state.editingTransactionId}`,
        {
          method: 'PUT',
          body: JSON.stringify(payload),
        }
      );

      showToast('Transaction updated successfully');
    } else {
      await apiRequest('/api/transactions', {
        method: 'POST',
        body: JSON.stringify(payload),
      });

      showToast('Transaction added successfully');
    }

    await refreshTransactions();

    closeModal();
    renderAll();
  } catch (error) {
    showToast(error.message, 'error');
  }
}

function deleteTransaction(transactionId) {
  showConfirm(
    'Delete Transaction?',
    'This action cannot be undone.',
    async () => {
      await apiRequest(`/api/transactions/${transactionId}`, {
        method: 'DELETE',
      });

      await refreshTransactions();
      renderAll();
      showToast('Transaction deleted', 'info');
    }
  );
}

function getFilteredTransactions() {
  let transactions = [...state.transactions];

  if (state.filterType) {
    transactions = transactions.filter(
      transaction => transaction.type === state.filterType
    );
  }

  if (state.filterCategory) {
    transactions = transactions.filter(
      transaction =>
        String(transaction.category?.category_id ?? '') ===
        String(state.filterCategory)
    );
  }

  if (state.filterDateFrom) {
    transactions = transactions.filter(
      transaction =>
        dateOnly(transaction.occurred_at) >= state.filterDateFrom
    );
  }

  if (state.filterDateTo) {
    transactions = transactions.filter(
      transaction =>
        dateOnly(transaction.occurred_at) <= state.filterDateTo
    );
  }

  if (state.searchQuery) {
    const query = state.searchQuery.toLowerCase();

    transactions = transactions.filter(transaction => {
      const category = getCategoryInfo(transaction.category);

      return (
        String(transaction.description || '').toLowerCase().includes(query) ||
        String(transaction.notes || '').toLowerCase().includes(query) ||
        category.name.toLowerCase().includes(query)
      );
    });
  }

  transactions.sort((a, b) => {
    let aValue;
    let bValue;

    switch (state.sortField) {
      case 'description':
        aValue = String(a.description || '').toLowerCase();
        bValue = String(b.description || '').toLowerCase();
        break;

      case 'category':
        aValue = getCategoryInfo(a.category).name.toLowerCase();
        bValue = getCategoryInfo(b.category).name.toLowerCase();
        break;

      case 'type':
        aValue = a.type;
        bValue = b.type;
        break;

      case 'amount':
        aValue = Number(a.amount);
        bValue = Number(b.amount);
        break;

      case 'date':
      default:
        aValue = a.occurred_at;
        bValue = b.occurred_at;
        break;
    }

    if (aValue < bValue) return state.sortDir === 'asc' ? -1 : 1;
    if (aValue > bValue) return state.sortDir === 'asc' ? 1 : -1;
    return 0;
  });

  return transactions;
}

function transactionRow(transaction, includeActions = true) {
  const category = getCategoryInfo(transaction.category);

  return `
    <tr>
      <td>${escapeHtml(formatDateTime(transaction.occurred_at))}</td>
      <td>
        <strong>${escapeHtml(transaction.description)}</strong>
        ${
          transaction.notes
            ? `<br><small style="color:var(--text-muted)">${escapeHtml(transaction.notes)}</small>`
            : ''
        }
      </td>
      <td>
        <span class="tx-category">
          <span class="category-dot" style="background:${escapeHtml(category.color)}"></span>
          ${escapeHtml(category.name)}
        </span>
      </td>
      <td>
        <span class="tx-type-badge type-${escapeHtml(transaction.type)}">
          ${escapeHtml(transaction.type)}
        </span>
      </td>
      <td class="tx-amount ${escapeHtml(transaction.type)}">
        ${transaction.type === 'income' ? '+' : '-'}${formatCurrency(transaction.amount)}
      </td>
      ${
        includeActions
          ? `<td>
              <div class="tx-actions">
                <button class="btn-icon" title="Edit" onclick="openModal(${transaction.transaction_id})">
                  <i class="fas fa-pen" style="font-size:11px"></i>
                </button>
                <button class="btn-icon" title="Delete" onclick="deleteTransaction(${transaction.transaction_id})">
                  <i class="fas fa-trash" style="font-size:11px;color:var(--red)"></i>
                </button>
              </div>
            </td>`
          : ''
      }
    </tr>
  `;
}

function renderTransactions() {
  populateFilterCategories();

  const filtered = getFilteredTransactions();
  const total = filtered.length;
  const totalPages = Math.ceil(total / state.itemsPerPage);

  if (state.currentPageNum > totalPages) {
    state.currentPageNum = Math.max(1, totalPages);
  }

  const start = (state.currentPageNum - 1) * state.itemsPerPage;
  const pageTransactions = filtered.slice(
    start,
    start + state.itemsPerPage
  );

  document.querySelectorAll('thead th[data-sort]').forEach(header => {
    header.classList.remove('sorted');

    const icon = header.querySelector('.sort-icon');

    if (icon) {
      icon.className = 'fas fa-chevron-up sort-icon';
    }

    if (header.dataset.sort === state.sortField) {
      header.classList.add('sorted');

      if (icon) {
        icon.className =
          `fas fa-chevron-${state.sortDir === 'asc' ? 'up' : 'down'} sort-icon`;
      }
    }
  });

  const tbody = document.getElementById('transactionsTable');

  if (pageTransactions.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6">
          <div class="empty-state">
            <i class="fas fa-inbox"></i>
            <h3>No transactions found</h3>
            <p>Try adjusting your filters or add a new transaction.</p>
          </div>
        </td>
      </tr>
    `;
  } else {
    tbody.innerHTML = pageTransactions
      .map(transaction => transactionRow(transaction, true))
      .join('');
  }

  document.getElementById('tableInfo').textContent =
    total === 0
      ? 'Showing 0 transactions'
      : `Showing ${start + 1}–${Math.min(start + state.itemsPerPage, total)} of ${total} transactions`;

  renderPagination(totalPages);
}

function renderPagination(totalPages) {
  const pagination = document.getElementById('pagination');

  if (totalPages <= 1) {
    pagination.innerHTML = '';
    return;
  }

  let html = `
    <button class="page-btn"
            onclick="goToPage(${state.currentPageNum - 1})"
            ${state.currentPageNum === 1 ? 'disabled' : ''}>
      <i class="fas fa-chevron-left"></i>
    </button>
  `;

  for (let page = 1; page <= totalPages; page++) {
    if (
      totalPages > 7 &&
      page > 3 &&
      page < totalPages - 2 &&
      Math.abs(page - state.currentPageNum) > 1
    ) {
      if (page === 4 || page === totalPages - 3) {
        html += '<button class="page-btn" disabled>…</button>';
      }

      continue;
    }

    html += `
      <button class="page-btn ${page === state.currentPageNum ? 'active' : ''}"
              onclick="goToPage(${page})">
        ${page}
      </button>
    `;
  }

  html += `
    <button class="page-btn"
            onclick="goToPage(${state.currentPageNum + 1})"
            ${state.currentPageNum === totalPages ? 'disabled' : ''}>
      <i class="fas fa-chevron-right"></i>
    </button>
  `;

  pagination.innerHTML = html;
}

function goToPage(page) {
  const totalPages = Math.ceil(
    getFilteredTransactions().length / state.itemsPerPage
  );

  if (page < 1 || page > totalPages) return;

  state.currentPageNum = page;
  renderTransactions();
}


// ==================== CATEGORY CRUD ====================

function openCategoryModal(categoryId = null) {
  state.editingCategoryId = categoryId;

  if (categoryId !== null) {
    const category = state.categories.find(
      item => item.category_id === categoryId
    );

    if (!category) {
      showToast('Category not found', 'error');
      return;
    }

    document.getElementById('catModalTitle').textContent = 'Edit Category';
    document.getElementById('catName').value = category.name;
    document.getElementById('catIcon').value = category.icon || '';
    document.getElementById('catColor').value = category.color || '#6c5ce7';
    document.getElementById('catType').value = category.type;
  } else {
    document.getElementById('catModalTitle').textContent = 'Add Category';
    document.getElementById('catName').value = '';
    document.getElementById('catIcon').value = 'fas fa-tag';
    document.getElementById('catColor').value = '#6c5ce7';
    document.getElementById('catType').value = 'expense';
  }

  document.getElementById('categoryModal').classList.add('active');
}

function closeCategoryModal() {
  document.getElementById('categoryModal').classList.remove('active');
  state.editingCategoryId = null;
}

async function saveCategory() {
  const payload = {
    name: document.getElementById('catName').value.trim(),
    icon: document.getElementById('catIcon').value.trim() || null,
    color: document.getElementById('catColor').value || null,
    type: document.getElementById('catType').value,
  };

  if (!payload.name) {
    return showToast('Please enter a category name', 'error');
  }

  try {
    if (state.editingCategoryId !== null) {
      await apiRequest(
        `/api/categories/${state.editingCategoryId}`,
        {
          method: 'PUT',
          body: JSON.stringify(payload),
        }
      );

      showToast('Category updated');
    } else {
      await apiRequest('/api/categories', {
        method: 'POST',
        body: JSON.stringify(payload),
      });

      showToast('Category added');
    }

    await Promise.all([
      refreshCategories(),
      refreshTransactions(),
      refreshBudgets(),
    ]);

    closeCategoryModal();
    renderAll();
  } catch (error) {
    showToast(error.message, 'error');
  }
}

function deleteCategory(categoryId) {
  showConfirm(
    'Delete Category?',
    'Transactions will be preserved as Unknown. Any budget using this category will be deleted.',
    async () => {
      await apiRequest(`/api/categories/${categoryId}`, {
        method: 'DELETE',
      });

      await Promise.all([
        refreshCategories(),
        refreshTransactions(),
        refreshBudgets(),
      ]);

      renderAll();
      showToast('Category deleted', 'info');
    }
  );
}

function renderCategories() {
  const grid = document.getElementById('categoriesGrid');

  if (state.categories.length === 0) {
    grid.innerHTML = `
      <div class="empty-state" style="grid-column:1/-1;">
        <i class="fas fa-tags"></i>
        <h3>No categories yet</h3>
        <p>Create a category to organize your transactions.</p>
      </div>
    `;
    return;
  }

  grid.innerHTML = state.categories.map(category => {
    const matchingTransactions = state.transactions.filter(
      transaction =>
        Number(transaction.category?.category_id) ===
        Number(category.category_id)
    );

    const totalAmount = matchingTransactions.reduce(
      (sum, transaction) => sum + Number(transaction.amount),
      0
    );

    const typeClass =
      category.type === 'income' ? 'income' : 'expense';

    return `
      <div class="category-card">
        <div class="category-icon"
             style="background:${escapeHtml(category.color || '#636e72')}22;color:${escapeHtml(category.color || '#636e72')}">
          <i class="${escapeHtml(category.icon || 'fas fa-tag')}"></i>
        </div>

        <div class="category-info">
          <div class="category-name">${escapeHtml(category.name)}</div>
          <div class="category-count">
            ${matchingTransactions.length} transaction${matchingTransactions.length !== 1 ? 's' : ''}
          </div>
        </div>

        <div class="category-amount ${typeClass}">
          ${formatCurrency(totalAmount)}
        </div>

        <div class="category-actions">
          <button class="btn-icon" title="Edit" onclick="openCategoryModal(${category.category_id})">
            <i class="fas fa-pen" style="font-size:11px"></i>
          </button>
          <button class="btn-icon" title="Delete" onclick="deleteCategory(${category.category_id})">
            <i class="fas fa-trash" style="font-size:11px;color:var(--red)"></i>
          </button>
        </div>
      </div>
    `;
  }).join('');
}


// ==================== BUDGET CRUD ====================

function populateBudgetCategorySelect() {
  const select = document.getElementById('budgetCategory');

  select.innerHTML = '<option value="">Select category</option>';

  state.categories
    .filter(category =>
      category.type === 'expense' || category.type === 'both'
    )
    .forEach(category => {
      const option = document.createElement('option');
      option.value = category.category_id;
      option.textContent = category.name;
      select.appendChild(option);
    });
}

function openBudgetModal() {
  populateBudgetCategorySelect();
  document.getElementById('budgetLimit').value = '';
  document.getElementById('budgetModal').classList.add('active');
}

function closeBudgetModal() {
  document.getElementById('budgetModal').classList.remove('active');
}

async function saveBudget() {
  const categoryId = Number(
    document.getElementById('budgetCategory').value
  );

  const amount = Number(
    document.getElementById('budgetLimit').value
  );

  if (!categoryId) {
    return showToast('Please select a category', 'error');
  }

  if (!amount || amount <= 0) {
    return showToast('Please enter a valid limit', 'error');
  }

  const month = currentMonthStart();

  const existing = state.budgets.find(
    budget =>
      Number(budget.category?.category_id) === categoryId &&
      sameMonth(budget.month, month)
  );

  const payload = {
    category_id: categoryId,
    amount,
    month,
  };

  try {
    if (existing) {
      await apiRequest(
        `/api/budgets/${existing.budget_id}`,
        {
          method: 'PUT',
          body: JSON.stringify(payload),
        }
      );
    } else {
      await apiRequest('/api/budgets', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
    }

    await refreshBudgets();

    closeBudgetModal();
    renderAll();
    showToast('Budget saved');
  } catch (error) {
    showToast(error.message, 'error');
  }
}

function deleteBudget(budgetId) {
  showConfirm(
    'Delete Budget?',
    'This will remove the monthly budget.',
    async () => {
      await apiRequest(`/api/budgets/${budgetId}`, {
        method: 'DELETE',
      });

      await refreshBudgets();
      renderAll();
      showToast('Budget removed', 'info');
    }
  );
}

function renderBudgets() {
  const currentMonth = currentMonthStart().slice(0, 7);

  let totalBudget = 0;
  let totalSpent = 0;

  const rows = state.budgets.map(budget => {
    const category = getCategoryInfo(budget.category);
    const limit = Number(budget.amount);

    totalBudget += limit;

    const spent =
      category.category_id == null
        ? 0
        : state.transactions
            .filter(transaction =>
              transaction.type === 'expense' &&
              Number(transaction.category?.category_id) ===
                Number(category.category_id) &&
              String(transaction.occurred_at).startsWith(currentMonth)
            )
            .reduce(
              (sum, transaction) => sum + Number(transaction.amount),
              0
            );

    totalSpent += spent;

    const percentage =
      limit > 0 ? Math.min((spent / limit) * 100, 100) : 0;

    const barColor =
      percentage > 90
        ? 'var(--red)'
        : percentage > 70
          ? 'var(--yellow)'
          : 'var(--green)';

    return {
      budget,
      category,
      spent,
      percentage,
      barColor,
    };
  });

  const remaining = totalBudget - totalSpent;

  document.getElementById('budgetOverview').innerHTML = `
    <div class="budget-card">
      <div class="budget-card-title">Total Budget</div>
      <div class="budget-card-value" style="color:var(--accent-light)">
        ${formatCurrency(totalBudget)}
      </div>
      <div class="progress-bar">
        <div class="progress-fill" style="width:100%;background:var(--accent)"></div>
      </div>
    </div>

    <div class="budget-card">
      <div class="budget-card-title">Total Spent</div>
      <div class="budget-card-value" style="color:var(--red)">
        ${formatCurrency(totalSpent)}
      </div>
      <div class="progress-bar">
        <div class="progress-fill"
             style="width:${totalBudget > 0 ? Math.min(totalSpent / totalBudget * 100, 100) : 0}%;background:var(--red)">
        </div>
      </div>
    </div>

    <div class="budget-card">
      <div class="budget-card-title">Remaining</div>
      <div class="budget-card-value"
           style="color:${remaining >= 0 ? 'var(--green)' : 'var(--red)'}">
        ${formatCurrency(remaining)}
      </div>
      <div class="progress-bar">
        <div class="progress-fill"
             style="width:${totalBudget > 0 ? Math.max(Math.min(remaining / totalBudget * 100, 100), 0) : 0}%;background:var(--green)">
        </div>
      </div>
    </div>
  `;

  const list = document.getElementById('budgetList');

  if (rows.length === 0) {
    list.innerHTML = `
      <div class="empty-state">
        <i class="fas fa-wallet"></i>
        <h3>No budgets set</h3>
        <p>Create a budget to track your spending limits.</p>
      </div>
    `;
    return;
  }

  list.innerHTML = rows.map(
    ({ budget, category, spent, percentage, barColor }) => `
      <div class="budget-item">
        <div class="budget-cat-icon"
             style="background:${escapeHtml(category.color)}22;color:${escapeHtml(category.color)}">
          <i class="${escapeHtml(category.icon)}"></i>
        </div>

        <div class="budget-cat-info">
          <div class="budget-cat-name">${escapeHtml(category.name)}</div>
          <div class="budget-progress-bar">
            <div class="budget-progress-fill"
                 style="width:${percentage}%;background:${barColor}">
            </div>
          </div>
        </div>

        <div class="budget-amounts">
          <div class="budget-spent" style="color:${barColor}">
            ${category.category_id == null ? '—' : formatCurrency(spent)}
          </div>

          <div class="budget-total">
            of ${formatCurrency(budget.amount)}
            <button class="btn-icon"
                    style="margin-left:8px;width:24px;height:24px;font-size:10px;"
                    onclick="deleteBudget(${budget.budget_id})">
              <i class="fas fa-times"></i>
            </button>
          </div>
        </div>
      </div>
    `
  ).join('');
}


// ==================== SAVINGS GOALS ====================

function openGoalModal() {
  document.getElementById('goalName').value = '';
  document.getElementById('goalTarget').value = '';
  document.getElementById('goalScope').value = 'personal';
  document.getElementById('goalIcon').value = 'fas fa-star';
  document.getElementById('goalColor').value = '#6c5ce7';
  document.getElementById('goalModal').classList.add('active');
}

function closeGoalModal() {
  document.getElementById('goalModal').classList.remove('active');
}

async function saveGoal() {
  const payload = {
    name: document.getElementById('goalName').value.trim(),
    target_amount: Number(document.getElementById('goalTarget').value),
    scope: document.getElementById('goalScope').value,
    icon: document.getElementById('goalIcon').value.trim() || null,
    color: document.getElementById('goalColor').value || null,
  };

  if (!payload.name) {
    return showToast('Please enter a goal name', 'error');
  }

  if (!payload.target_amount || payload.target_amount <= 0) {
    return showToast('Please enter a valid target', 'error');
  }

  try {
    await apiRequest('/api/goals', {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    await refreshGoals();

    closeGoalModal();
    renderAll();
    showToast('Goal created');
  } catch (error) {
    showToast(error.message, 'error');
  }
}

function deleteGoal(goalId) {
  showConfirm(
    'Delete Goal?',
    'This will remove the savings goal.',
    async () => {
      await apiRequest(`/api/goals/${goalId}`, {
        method: 'DELETE',
      });

      await refreshGoals();
      renderAll();
      showToast('Goal deleted', 'info');
    }
  );
}

async function addGoalContribution(goalId) {
  const rawAmount = prompt('Enter contribution amount:');

  if (rawAmount === null) return;

  const amount = Number(rawAmount);

  if (!amount || amount <= 0) {
    return showToast('Please enter a valid contribution', 'error');
  }

  try {
    await apiRequest(
      `/api/goals/${goalId}/contributions`,
      {
        method: 'POST',
        body: JSON.stringify({
          amount,
          occurred_at: localDateTimeValue(),
        }),
      }
    );

    await refreshGoals();
    renderAll();

    showToast(`${formatCurrency(amount)} added to goal`);
  } catch (error) {
    showToast(error.message, 'error');
  }
}

function renderGoals() {
  const grid = document.getElementById('goalsGrid');

  if (state.goals.length === 0) {
    grid.innerHTML = `
      <div class="empty-state" style="grid-column:1/-1;">
        <i class="fas fa-bullseye"></i>
        <h3>No savings goals yet</h3>
        <p>Create a goal to start tracking your savings progress.</p>
      </div>
    `;
    return;
  }

  grid.innerHTML = state.goals.map(goal => {
    const current = Number(goal.current_amount) || 0;
    const target = Number(goal.target_amount) || 0;
    const percentage =
      target > 0 ? Math.min((current / target) * 100, 100) : 0;

    const complete = percentage >= 100;
    const isOwner =
      Number(goal.owner_user_id) === Number(state.currentUser?.user_id);

    return `
      <div class="goal-card">
        <div class="goal-header">
          <div class="goal-icon"
               style="background:${escapeHtml(goal.color || '#6c5ce7')}22;color:${escapeHtml(goal.color || '#6c5ce7')}">
            <i class="${escapeHtml(goal.icon || 'fas fa-star')}"></i>
          </div>

          <span class="goal-status ${complete ? 'status-completed' : 'status-active'}">
            ${complete ? 'Completed' : 'Active'}
          </span>
        </div>

        <div class="goal-name">${escapeHtml(goal.name)}</div>
        <div class="goal-target">Target: ${formatCurrency(target)}</div>

        <div class="goal-progress-bar">
          <div class="goal-progress-fill"
               style="width:${percentage}%;background:${escapeHtml(goal.color || '#6c5ce7')}">
          </div>
        </div>

        <div class="goal-stats">
          <span class="goal-current">${formatCurrency(current)}</span>
          <span class="goal-percent">${percentage.toFixed(1)}%</span>
        </div>

        <div style="margin-top:16px;display:flex;gap:8px;">
          <button class="btn btn-secondary btn-sm"
                  onclick="addGoalContribution(${goal.goal_id})">
            <i class="fas fa-plus"></i> Add Funds
          </button>

          ${
            isOwner
              ? `<button class="btn btn-danger btn-sm" onclick="deleteGoal(${goal.goal_id})">
                   <i class="fas fa-trash"></i>
                 </button>`
              : ''
          }
        </div>
      </div>
    `;
  }).join('');
}


// ==================== DASHBOARD ====================
// Temporary calculations from API-loaded data.
// Later these can be replaced directly by a statistics endpoint.

function getAllocatedSavingsForCurrentUser() {
  if (!state.currentUser) return 0;

  return state.goals.reduce((total, goal) => {
    const userContributions = (goal.contributions || [])
      .filter(
        contribution =>
          Number(contribution.user_id) ===
          Number(state.currentUser.user_id)
      )
      .reduce(
        (sum, contribution) => sum + Number(contribution.amount),
        0
      );

    return total + userContributions;
  }, 0);
}

function renderDashboard() {
  const income = state.transactions
    .filter(transaction => transaction.type === 'income')
    .reduce((sum, transaction) => sum + Number(transaction.amount), 0);

  const expense = state.transactions
    .filter(transaction => transaction.type === 'expense')
    .reduce((sum, transaction) => sum + Number(transaction.amount), 0);

  const balance = income - expense;

  const savingsRate =
    income > 0
      ? ((income - expense) / income * 100).toFixed(1)
      : '0.0';

  document.getElementById('totalBalance').textContent =
    formatCurrency(balance);

  document.getElementById('totalIncome').textContent =
    formatCurrency(income);

  document.getElementById('totalExpense').textContent =
    formatCurrency(expense);

  document.getElementById('totalSavings').textContent =
    `${savingsRate}%`;

  // Allocation does not reduce total balance.
  document.getElementById('allocatedSavings').textContent =
    formatCurrency(getAllocatedSavingsForCurrentUser());

  const recent = [...state.transactions]
    .sort(
      (a, b) =>
        new Date(b.occurred_at) - new Date(a.occurred_at)
    )
    .slice(0, 5);

  const tbody = document.getElementById('recentTransactions');

  if (recent.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="5">
          <div class="empty-state">
            <i class="fas fa-inbox"></i>
            <h3>No transactions yet</h3>
            <p>Add a transaction to begin tracking your finances.</p>
          </div>
        </td>
      </tr>
    `;
  } else {
    tbody.innerHTML = recent.map(transaction => {
      const category = getCategoryInfo(transaction.category);

      return `
        <tr>
          <td>${escapeHtml(formatDateTime(transaction.occurred_at))}</td>
          <td><strong>${escapeHtml(transaction.description)}</strong></td>
          <td>
            <span class="tx-category">
              <span class="category-dot"
                    style="background:${escapeHtml(category.color)}"></span>
              ${escapeHtml(category.name)}
            </span>
          </td>
          <td>
            <span class="tx-type-badge type-${escapeHtml(transaction.type)}">
              ${escapeHtml(transaction.type)}
            </span>
          </td>
          <td class="tx-amount ${escapeHtml(transaction.type)}">
            ${transaction.type === 'income' ? '+' : '-'}${formatCurrency(transaction.amount)}
          </td>
        </tr>
      `;
    }).join('');
  }

  renderIncomeExpenseChart();
}

function getTransactionsForChartPeriod() {
  if (state.chartPeriod === 'all') {
    return [...state.transactions];
  }

  const monthsBack = state.chartPeriod === '6m' ? 6 : 12;
  const cutoff = new Date();
  cutoff.setMonth(cutoff.getMonth() - monthsBack + 1);
  cutoff.setDate(1);
  cutoff.setHours(0, 0, 0, 0);

  return state.transactions.filter(
    transaction => new Date(transaction.occurred_at) >= cutoff
  );
}

function renderIncomeExpenseChart() {
  const canvas = document.getElementById('incomeExpenseChart');

  if (!canvas || typeof Chart === 'undefined') return;

  if (incomeExpenseChartInstance) {
    incomeExpenseChartInstance.destroy();
  }

  const months = {};

  getTransactionsForChartPeriod().forEach(transaction => {
    const key = String(transaction.occurred_at).slice(0, 7);

    if (!months[key]) {
      months[key] = { income: 0, expense: 0 };
    }

    months[key][transaction.type] += Number(transaction.amount);
  });

  const sortedKeys = Object.keys(months).sort();

  const labels = sortedKeys.map(key => {
    const date = new Date(`${key}-01T00:00:00`);

    return date.toLocaleDateString('en-US', {
      month: 'short',
      year: '2-digit',
    });
  });

  incomeExpenseChartInstance = new Chart(
    canvas.getContext('2d'),
    {
      type: 'bar',
      data: {
        labels,
        datasets: [
          {
            label: 'Income',
            data: sortedKeys.map(key => months[key].income),
            backgroundColor: 'rgba(0,210,160,0.7)',
            borderRadius: 6,
            borderSkipped: false,
          },
          {
            label: 'Expenses',
            data: sortedKeys.map(key => months[key].expense),
            backgroundColor: 'rgba(255,107,129,0.7)',
            borderRadius: 6,
            borderSkipped: false,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            labels: {
              color: '#8b92a8',
              font: { family: 'Inter', size: 12 },
              usePointStyle: true,
              pointStyle: 'circle',
            },
          },
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: {
              color: '#5c6378',
              font: { family: 'Inter', size: 11 },
            },
          },
          y: {
            grid: { color: 'rgba(45,51,72,0.5)' },
            ticks: {
              color: '#5c6378',
              font: { family: 'Inter', size: 11 },
              callback: value => '$' + (value / 1000).toFixed(0) + 'k',
            },
          },
        },
      },
    }
  );
}


// ==================== REPORTS ====================
// Temporary calculations from API-loaded transaction data.

function renderReports() {
  renderReportBarChart();
  renderReportIncomePieChart();
  renderReportPieChart();
  renderBalanceTrendChart();
}

function monthlyTransactionTotals() {
  const months = {};

  state.transactions.forEach(transaction => {
    const key = String(transaction.occurred_at).slice(0, 7);

    if (!months[key]) {
      months[key] = { income: 0, expense: 0 };
    }

    months[key][transaction.type] += Number(transaction.amount);
  });

  return months;
}

function renderReportBarChart() {
  const canvas = document.getElementById('reportBarChart');

  if (!canvas || typeof Chart === 'undefined') return;

  if (reportBarChartInstance) {
    reportBarChartInstance.destroy();
  }

  const months = monthlyTransactionTotals();
  const keys = Object.keys(months).sort();

  const labels = keys.map(key => {
    const date = new Date(`${key}-01T00:00:00`);

    return date.toLocaleDateString('en-US', {
      month: 'short',
      year: '2-digit',
    });
  });

  reportBarChartInstance = new Chart(
    canvas.getContext('2d'),
    {
      type: 'bar',
      data: {
        labels,
        datasets: [
          {
            label: 'Income',
            data: keys.map(key => months[key].income),
            backgroundColor: 'rgba(0,210,160,0.7)',
            borderRadius: 6,
            borderSkipped: false,
          },
          {
            label: 'Expenses',
            data: keys.map(key => months[key].expense),
            backgroundColor: 'rgba(255,107,129,0.7)',
            borderRadius: 6,
            borderSkipped: false,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            labels: {
              color: '#8b92a8',
              font: { family: 'Inter', size: 12 },
              usePointStyle: true,
              pointStyle: 'circle',
            },
          },
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: {
              color: '#5c6378',
              font: { family: 'Inter', size: 11 },
            },
          },
          y: {
            grid: { color: 'rgba(45,51,72,0.5)' },
            ticks: {
              color: '#5c6378',
              font: { family: 'Inter', size: 11 },
              callback: value => '$' + (value / 1000).toFixed(0) + 'k',
            },
          },
        },
      },
    }
  );
}

function renderReportIncomePieChart() {
  const canvas = document.getElementById('reportIncomePieChart');

  if (!canvas || typeof Chart === 'undefined') return;

  if (reportIncomePieChartInstance) {
    reportIncomePieChartInstance.destroy();
  }

  const currentMonth = currentMonthStart().slice(0, 7);
  const totals = new Map();

  state.transactions
    .filter(
      transaction =>
        transaction.type === 'income' &&
        String(transaction.occurred_at).startsWith(currentMonth)
    )
    .forEach(transaction => {
      const category = getCategoryInfo(transaction.category);
      const key =
        category.category_id ?? `unknown-${category.name}`;

      if (!totals.has(key)) {
        totals.set(key, {
          name: category.name,
          color: category.color,
          amount: 0,
        });
      }

      totals.get(key).amount += Number(transaction.amount);
    });

  const values = [...totals.values()].sort(
    (a, b) => b.amount - a.amount
  );

  reportIncomePieChartInstance = new Chart(
    canvas.getContext('2d'),
    {
      type: 'doughnut',

      data: {
        labels: values.map(value => value.name),

        datasets: [
          {
            data: values.map(value => value.amount),
            backgroundColor: values.map(value => value.color),
            borderWidth: 0,
            hoverOffset: 8,
          },
        ],
      },

      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '60%',

        plugins: {
          legend: {
            position: 'bottom',

            labels: {
              color: '#8b92a8',
              font: {
                family: 'Inter',
                size: 11,
              },
              usePointStyle: true,
              pointStyle: 'circle',
              padding: 12,
            },
          },
        },
      },
    }
  );
}

function renderReportPieChart() {
  const canvas = document.getElementById('reportPieChart');

  if (!canvas || typeof Chart === 'undefined') return;

  if (reportPieChartInstance) {
    reportPieChartInstance.destroy();
  }

  const currentMonth = currentMonthStart().slice(0, 7);
  const totals = new Map();

  state.transactions
    .filter(
      transaction =>
        transaction.type === 'expense' &&
        String(transaction.occurred_at).startsWith(currentMonth)
    )
    .forEach(transaction => {
      const category = getCategoryInfo(transaction.category);
      const key = category.category_id ?? `unknown-${category.name}`;

      if (!totals.has(key)) {
        totals.set(key, {
          name: category.name,
          color: category.color,
          amount: 0,
        });
      }

      totals.get(key).amount += Number(transaction.amount);
    });

  const values = [...totals.values()].sort(
    (a, b) => b.amount - a.amount
  );

  reportPieChartInstance = new Chart(
    canvas.getContext('2d'),
    {
      type: 'doughnut',
      data: {
        labels: values.map(value => value.name),
        datasets: [
          {
            data: values.map(value => value.amount),
            backgroundColor: values.map(value => value.color),
            borderWidth: 0,
            hoverOffset: 8,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '60%',
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              color: '#8b92a8',
              font: { family: 'Inter', size: 11 },
              usePointStyle: true,
              pointStyle: 'circle',
              padding: 12,
            },
          },
        },
      },
    }
  );
}

function renderBalanceTrendChart() {
  const canvas = document.getElementById('balanceTrendChart');

  if (!canvas || typeof Chart === 'undefined') return;

  if (reportBalanceTrendChartInstance) {
    reportBalanceTrendChartInstance.destroy();
  }

  const sorted = [...state.transactions].sort(
    (a, b) =>
      new Date(a.occurred_at) - new Date(b.occurred_at)
  );

  let runningBalance = 0;
  const balances = [];
  const labels = [];

  sorted.forEach(transaction => {
    runningBalance +=
      transaction.type === 'income'
        ? Number(transaction.amount)
        : -Number(transaction.amount);

    balances.push(runningBalance);
    labels.push(formatDateTime(transaction.occurred_at));
  });

  const step = Math.max(1, Math.floor(balances.length / 30));

  const sampledBalances = balances.filter(
    (_, index) =>
      index % step === 0 || index === balances.length - 1
  );

  const sampledLabels = labels.filter(
    (_, index) =>
      index % step === 0 || index === labels.length - 1
  );

  reportBalanceTrendChartInstance = new Chart(
    canvas.getContext('2d'),
    {
      type: 'line',
      data: {
        labels: sampledLabels,
        datasets: [
          {
            label: 'Running Balance',
            data: sampledBalances,
            borderColor: '#6c5ce7',
            backgroundColor: 'rgba(108,92,231,0.1)',
            fill: true,
            tension: 0.4,
            pointRadius: 2,
            pointHoverRadius: 6,
            borderWidth: 2,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            labels: {
              color: '#8b92a8',
              font: { family: 'Inter', size: 12 },
              usePointStyle: true,
            },
          },
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: {
              color: '#5c6378',
              font: { family: 'Inter', size: 10 },
              maxTicksLimit: 12,
            },
          },
          y: {
            grid: { color: 'rgba(45,51,72,0.5)' },
            ticks: {
              color: '#5c6378',
              font: { family: 'Inter', size: 11 },
              callback: value => '$' + (value / 1000).toFixed(1) + 'k',
            },
          },
        },
      },
    }
  );
}


// ==================== PAGE RENDERING ====================

function renderPage(page) {
  switch (page) {
    case 'dashboard':
      renderDashboard();
      break;

    case 'transactions':
      renderTransactions();
      break;

    case 'categories':
      renderCategories();
      break;

    case 'budgets':
      renderBudgets();
      break;

    case 'goals':
      renderGoals();
      break;

    case 'reports':
      renderReports();
      break;
  }
}

function renderAll() {
  renderPage(state.currentPage);
}

function populateFilterCategories() {
  const select = document.getElementById('filterCategory');
  const currentValue = state.filterCategory;

  select.innerHTML = '<option value="">All Categories</option>';

  state.categories.forEach(category => {
    const option = document.createElement('option');
    option.value = category.category_id;
    option.textContent = category.name;
    option.selected =
      String(currentValue) === String(category.category_id);

    select.appendChild(option);
  });
}


// ==================== EVENT HANDLERS ====================

document.querySelectorAll('thead th[data-sort]').forEach(header => {
  header.addEventListener('click', () => {
    const field = header.dataset.sort;

    if (state.sortField === field) {
      state.sortDir = state.sortDir === 'asc' ? 'desc' : 'asc';
    } else {
      state.sortField = field;
      state.sortDir = 'asc';
    }

    state.currentPageNum = 1;
    renderTransactions();
  });
});

document.getElementById('filterType').addEventListener('change', function () {
  state.filterType = this.value;
  state.currentPageNum = 1;
  renderTransactions();
});

document.getElementById('filterCategory').addEventListener('change', function () {
  state.filterCategory = this.value;
  state.currentPageNum = 1;
  renderTransactions();
});

document.getElementById('filterDateFrom').addEventListener('change', function () {
  state.filterDateFrom = this.value;
  state.currentPageNum = 1;
  renderTransactions();
});

document.getElementById('filterDateTo').addEventListener('change', function () {
  state.filterDateTo = this.value;
  state.currentPageNum = 1;
  renderTransactions();
});

document.getElementById('clearFilters').addEventListener('click', () => {
  state.filterType = '';
  state.filterCategory = '';
  state.filterDateFrom = '';
  state.filterDateTo = '';
  state.searchQuery = '';
  state.currentPageNum = 1;

  document.getElementById('filterType').value = '';
  document.getElementById('filterCategory').value = '';
  document.getElementById('filterDateFrom').value = '';
  document.getElementById('filterDateTo').value = '';
  document.getElementById('globalSearch').value = '';

  renderTransactions();
  showToast('Filters cleared', 'info');
});

document.getElementById('globalSearch').addEventListener('input', function () {
  state.searchQuery = this.value.toLowerCase().trim();
  state.currentPageNum = 1;

  if (state.currentPage !== 'transactions') {
    navigateTo('transactions');
  } else {
    renderTransactions();
  }
});

document.querySelectorAll('.period-btn').forEach(button => {
  button.addEventListener('click', function () {
    document.querySelectorAll('.period-btn').forEach(item => {
      item.classList.remove('active');
    });

    this.classList.add('active');
    state.chartPeriod = this.dataset.period;
    renderIncomeExpenseChart();
  });
});

document.querySelectorAll('.modal-overlay').forEach(modalOverlay => {
  modalOverlay.addEventListener('click', function (event) {
    if (event.target === this) {
      this.classList.remove('active');
      state.editingTransactionId = null;
      state.editingCategoryId = null;
    }
  });
});

document.addEventListener('keydown', event => {
  if (event.key === 'Escape') {
    document.querySelectorAll('.modal-overlay.active').forEach(modal => {
      modal.classList.remove('active');
    });

    state.editingTransactionId = null;
    state.editingCategoryId = null;
  }

  if (event.key === 'n' && event.ctrlKey) {
    event.preventDefault();
    openModal();
  }
});


// ==================== INITIALIZATION ====================

async function initializeApp() {
  try {
    const auth = await apiRequest('/auth/status');
    state.currentUser = auth.user;

    updateUserCard();
    await refreshFinanceData();

    renderAll();
  } catch (error) {
    if (window.location.pathname !== '/login') {
      showToast(error.message, 'error');
    }
  }
}

initializeApp();


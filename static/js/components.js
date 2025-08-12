// ===== Reusable Components for Admin Dashboard =====

class ComponentManager {
    constructor() {
        this.modals = new Map();
        this.tables = new Map();
        this.forms = new Map();
    }

    // Modal Component
    createModal(id, title, content, options = {}) {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.id = id;
        
        const defaultOptions = {
            size: 'medium', // small, medium, large, full
            closable: true,
            backdrop: true,
            keyboard: true,
            buttons: []
        };
        
        const config = { ...defaultOptions, ...options };
        
        modal.innerHTML = `
            <div class="modal modal-${config.size}">
                <div class="modal-header">
                    <h3 class="modal-title">${title}</h3>
                    ${config.closable ? '<button class="modal-close" data-dismiss="modal"><i class="fas fa-times"></i></button>' : ''}
                </div>
                <div class="modal-body">
                    ${content}
                </div>
                ${config.buttons.length > 0 ? `
                    <div class="modal-footer">
                        ${config.buttons.map(btn => `
                            <button class="btn btn-${btn.type || 'secondary'}" 
                                    onclick="${btn.onclick || ''}" 
                                    ${btn.dismiss ? 'data-dismiss="modal"' : ''}>
                                ${btn.icon ? `<i class="fas fa-${btn.icon}"></i>` : ''}
                                ${btn.text}
                            </button>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        `;

        // Event listeners
        if (config.closable || config.backdrop) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal || e.target.hasAttribute('data-dismiss')) {
                    this.closeModal(id);
                }
            });
        }

        if (config.keyboard) {
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && modal.style.display !== 'none') {
                    this.closeModal(id);
                }
            });
        }

        this.modals.set(id, { element: modal, config });
        return modal;
    }

    showModal(id) {
        const modal = this.modals.get(id);
        if (modal) {
            document.getElementById('modalContainer').appendChild(modal.element);
            modal.element.style.display = 'flex';
            
            // Animate in
            setTimeout(() => {
                modal.element.classList.add('show');
            }, 10);
            
            // Focus first input
            const firstInput = modal.element.querySelector('input, select, textarea');
            if (firstInput) {
                firstInput.focus();
            }
        }
    }

    closeModal(id) {
        const modal = this.modals.get(id);
        if (modal) {
            modal.element.classList.remove('show');
            
            setTimeout(() => {
                if (modal.element.parentNode) {
                    modal.element.parentNode.removeChild(modal.element);
                }
            }, 300);
        }
    }

    // Data Table Component
    createDataTable(containerId, columns, data, options = {}) {
        const container = document.getElementById(containerId);
        if (!container) return null;

        const defaultOptions = {
            pagination: true,
            pageSize: 10,
            sortable: true,
            searchable: true,
            selectable: false,
            actions: [],
            emptyMessage: 'لا توجد بيانات للعرض'
        };

        const config = { ...defaultOptions, ...options };
        
        const tableId = `table_${containerId}`;
        const table = {
            id: tableId,
            container,
            columns,
            data,
            config,
            currentPage: 1,
            sortColumn: null,
            sortDirection: 'asc',
            searchQuery: '',
            selectedRows: new Set()
        };

        this.tables.set(tableId, table);
        this.renderTable(tableId);
        
        return tableId;
    }

    renderTable(tableId) {
        const table = this.tables.get(tableId);
        if (!table) return;

        const { container, columns, data, config } = table;
        
        // Filter and sort data
        let processedData = this.filterData(data, table.searchQuery);
        processedData = this.sortData(processedData, table.sortColumn, table.sortDirection);
        
        // Pagination
        const totalPages = Math.ceil(processedData.length / config.pageSize);
        const startIndex = (table.currentPage - 1) * config.pageSize;
        const pageData = processedData.slice(startIndex, startIndex + config.pageSize);

        container.innerHTML = `
            ${config.searchable ? `
                <div class="table-controls">
                    <div class="table-search">
                        <input type="text" placeholder="البحث..." 
                               value="${table.searchQuery}"
                               onkeyup="components.handleTableSearch('${tableId}', this.value)">
                        <i class="fas fa-search"></i>
                    </div>
                    ${config.actions.length > 0 ? `
                        <div class="table-actions">
                            ${config.actions.map(action => `
                                <button class="btn btn-${action.type || 'primary'}" 
                                        onclick="${action.onclick}">
                                    ${action.icon ? `<i class="fas fa-${action.icon}"></i>` : ''}
                                    ${action.text}
                                </button>
                            `).join('')}
                        </div>
                    ` : ''}
                </div>
            ` : ''}
            
            <div class="table-wrapper">
                <table class="data-table">
                    <thead>
                        <tr>
                            ${config.selectable ? '<th><input type="checkbox" onchange="components.toggleAllRows(\'${tableId}\', this.checked)"></th>' : ''}
                            ${columns.map(col => `
                                <th ${config.sortable && col.sortable !== false ? `class="sortable" onclick="components.sortTable('${tableId}', '${col.key}')"` : ''}>
                                    ${col.title}
                                    ${table.sortColumn === col.key ? `
                                        <i class="fas fa-sort-${table.sortDirection === 'asc' ? 'up' : 'down'}"></i>
                                    ` : ''}
                                </th>
                            `).join('')}
                        </tr>
                    </thead>
                    <tbody>
                        ${pageData.length > 0 ? pageData.map((row, index) => `
                            <tr ${config.selectable ? `onclick="components.toggleRow('${tableId}', ${startIndex + index})"` : ''}>
                                ${config.selectable ? `<td><input type="checkbox" ${table.selectedRows.has(startIndex + index) ? 'checked' : ''}></td>` : ''}
                                ${columns.map(col => `
                                    <td>${this.formatCellValue(row[col.key], col)}</td>
                                `).join('')}
                            </tr>
                        `).join('') : `
                            <tr>
                                <td colspan="${columns.length + (config.selectable ? 1 : 0)}" class="text-center empty-message">
                                    ${config.emptyMessage}
                                </td>
                            </tr>
                        `}
                    </tbody>
                </table>
            </div>
            
            ${config.pagination && totalPages > 1 ? `
                <div class="table-pagination">
                    <div class="pagination-info">
                        عرض ${startIndex + 1} إلى ${Math.min(startIndex + config.pageSize, processedData.length)} من ${processedData.length}
                    </div>
                    <div class="pagination-controls">
                        <button class="btn btn-sm" 
                                ${table.currentPage === 1 ? 'disabled' : ''}
                                onclick="components.changePage('${tableId}', ${table.currentPage - 1})">
                            <i class="fas fa-chevron-right"></i>
                        </button>
                        ${this.generatePageNumbers(table.currentPage, totalPages, tableId)}
                        <button class="btn btn-sm" 
                                ${table.currentPage === totalPages ? 'disabled' : ''}
                                onclick="components.changePage('${tableId}', ${table.currentPage + 1})">
                            <i class="fas fa-chevron-left"></i>
                        </button>
                    </div>
                </div>
            ` : ''}
        `;
    }

    formatCellValue(value, column) {
        if (column.render) {
            return column.render(value);
        }
        
        if (column.type === 'date') {
            return new Date(value).toLocaleDateString('ar-EG');
        }
        
        if (column.type === 'number') {
            return new Intl.NumberFormat('ar-EG').format(value);
        }
        
        if (column.type === 'currency') {
            return new Intl.NumberFormat('ar-EG', { 
                style: 'currency', 
                currency: 'USD' 
            }).format(value);
        }
        
        if (column.type === 'badge') {
            const badgeClass = column.badgeClass ? column.badgeClass(value) : 'secondary';
            return `<span class="badge badge-${badgeClass}">${value}</span>`;
        }
        
        return value || '';
    }

    generatePageNumbers(currentPage, totalPages, tableId) {
        const pages = [];
        const maxVisible = 5;
        
        let start = Math.max(1, currentPage - Math.floor(maxVisible / 2));
        let end = Math.min(totalPages, start + maxVisible - 1);
        
        if (end - start < maxVisible - 1) {
            start = Math.max(1, end - maxVisible + 1);
        }
        
        for (let i = start; i <= end; i++) {
            pages.push(`
                <button class="btn btn-sm ${i === currentPage ? 'btn-primary' : ''}" 
                        onclick="components.changePage('${tableId}', ${i})">
                    ${i}
                </button>
            `);
        }
        
        return pages.join('');
    }

    filterData(data, query) {
        if (!query) return data;
        
        return data.filter(row => 
            Object.values(row).some(value => 
                String(value).toLowerCase().includes(query.toLowerCase())
            )
        );
    }

    sortData(data, column, direction) {
        if (!column) return data;
        
        return [...data].sort((a, b) => {
            let aVal = a[column];
            let bVal = b[column];
            
            // Handle different data types
            if (typeof aVal === 'string') {
                aVal = aVal.toLowerCase();
                bVal = bVal.toLowerCase();
            }
            
            if (aVal < bVal) return direction === 'asc' ? -1 : 1;
            if (aVal > bVal) return direction === 'asc' ? 1 : -1;
            return 0;
        });
    }

    // Table event handlers
    handleTableSearch(tableId, query) {
        const table = this.tables.get(tableId);
        if (table) {
            table.searchQuery = query;
            table.currentPage = 1;
            this.renderTable(tableId);
        }
    }

    sortTable(tableId, column) {
        const table = this.tables.get(tableId);
        if (table) {
            if (table.sortColumn === column) {
                table.sortDirection = table.sortDirection === 'asc' ? 'desc' : 'asc';
            } else {
                table.sortColumn = column;
                table.sortDirection = 'asc';
            }
            this.renderTable(tableId);
        }
    }

    changePage(tableId, page) {
        const table = this.tables.get(tableId);
        if (table) {
            table.currentPage = page;
            this.renderTable(tableId);
        }
    }

    toggleRow(tableId, rowIndex) {
        const table = this.tables.get(tableId);
        if (table) {
            if (table.selectedRows.has(rowIndex)) {
                table.selectedRows.delete(rowIndex);
            } else {
                table.selectedRows.add(rowIndex);
            }
            this.renderTable(tableId);
        }
    }

    toggleAllRows(tableId, checked) {
        const table = this.tables.get(tableId);
        if (table) {
            if (checked) {
                for (let i = 0; i < table.data.length; i++) {
                    table.selectedRows.add(i);
                }
            } else {
                table.selectedRows.clear();
            }
            this.renderTable(tableId);
        }
    }

    // Form Component
    createForm(containerId, fields, options = {}) {
        const container = document.getElementById(containerId);
        if (!container) return null;

        const defaultOptions = {
            layout: 'vertical', // vertical, horizontal, inline
            validation: true,
            submitButton: true,
            resetButton: false,
            onSubmit: null,
            onReset: null
        };

        const config = { ...defaultOptions, ...options };
        const formId = `form_${containerId}`;
        
        const form = {
            id: formId,
            container,
            fields,
            config,
            values: {},
            errors: {}
        };

        this.forms.set(formId, form);
        this.renderForm(formId);
        
        return formId;
    }

    renderForm(formId) {
        const form = this.forms.get(formId);
        if (!form) return;

        const { container, fields, config } = form;
        
        container.innerHTML = `
            <form class="form form-${config.layout}" onsubmit="components.handleFormSubmit('${formId}', event)">
                ${fields.map(field => this.renderFormField(field, form)).join('')}
                
                ${config.submitButton || config.resetButton ? `
                    <div class="form-actions">
                        ${config.submitButton ? `
                            <button type="submit" class="btn btn-primary">
                                <i class="fas fa-save"></i>
                                ${typeof config.submitButton === 'string' ? config.submitButton : 'حفظ'}
                            </button>
                        ` : ''}
                        ${config.resetButton ? `
                            <button type="reset" class="btn btn-secondary" onclick="components.handleFormReset('${formId}')">
                                <i class="fas fa-undo"></i>
                                ${typeof config.resetButton === 'string' ? config.resetButton : 'إعادة تعيين'}
                            </button>
                        ` : ''}
                    </div>
                ` : ''}
            </form>
        `;
    }

    renderFormField(field, form) {
        const error = form.errors[field.name];
        const value = form.values[field.name] || field.defaultValue || '';
        
        let fieldHtml = '';
        
        switch (field.type) {
            case 'text':
            case 'email':
            case 'password':
            case 'number':
                fieldHtml = `
                    <input type="${field.type}" 
                           name="${field.name}" 
                           id="${field.name}"
                           value="${value}"
                           placeholder="${field.placeholder || ''}"
                           ${field.required ? 'required' : ''}
                           ${field.readonly ? 'readonly' : ''}
                           class="form-control ${error ? 'error' : ''}">
                `;
                break;
                
            case 'textarea':
                fieldHtml = `
                    <textarea name="${field.name}" 
                              id="${field.name}"
                              placeholder="${field.placeholder || ''}"
                              rows="${field.rows || 3}"
                              ${field.required ? 'required' : ''}
                              ${field.readonly ? 'readonly' : ''}
                              class="form-control ${error ? 'error' : ''}">${value}</textarea>
                `;
                break;
                
            case 'select':
                fieldHtml = `
                    <select name="${field.name}" 
                            id="${field.name}"
                            ${field.required ? 'required' : ''}
                            ${field.readonly ? 'readonly' : ''}
                            class="form-control ${error ? 'error' : ''}">
                        ${field.placeholder ? `<option value="">${field.placeholder}</option>` : ''}
                        ${field.options.map(option => `
                            <option value="${option.value}" ${value === option.value ? 'selected' : ''}>
                                ${option.label}
                            </option>
                        `).join('')}
                    </select>
                `;
                break;
                
            case 'checkbox':
                fieldHtml = `
                    <label class="checkbox-label">
                        <input type="checkbox" 
                               name="${field.name}" 
                               id="${field.name}"
                               value="1"
                               ${value ? 'checked' : ''}
                               ${field.readonly ? 'readonly' : ''}>
                        <span class="checkmark"></span>
                        ${field.label}
                    </label>
                `;
                break;
                
            case 'radio':
                fieldHtml = field.options.map(option => `
                    <label class="radio-label">
                        <input type="radio" 
                               name="${field.name}" 
                               value="${option.value}"
                               ${value === option.value ? 'checked' : ''}
                               ${field.readonly ? 'readonly' : ''}>
                        <span class="radiomark"></span>
                        ${option.label}
                    </label>
                `).join('');
                break;
                
            case 'file':
                fieldHtml = `
                    <input type="file" 
                           name="${field.name}" 
                           id="${field.name}"
                           ${field.accept ? `accept="${field.accept}"` : ''}
                           ${field.multiple ? 'multiple' : ''}
                           ${field.required ? 'required' : ''}
                           class="form-control ${error ? 'error' : ''}">
                `;
                break;
        }
        
        return `
            <div class="form-group ${error ? 'has-error' : ''}">
                ${field.type !== 'checkbox' && field.label ? `
                    <label for="${field.name}" class="form-label">
                        ${field.label}
                        ${field.required ? '<span class="required">*</span>' : ''}
                    </label>
                ` : ''}
                ${fieldHtml}
                ${field.help ? `<div class="form-help">${field.help}</div>` : ''}
                ${error ? `<div class="form-error">${error}</div>` : ''}
            </div>
        `;
    }

    handleFormSubmit(formId, event) {
        event.preventDefault();
        
        const form = this.forms.get(formId);
        if (!form) return;

        const formData = new FormData(event.target);
        const values = {};
        
        for (let [key, value] of formData.entries()) {
            values[key] = value;
        }
        
        form.values = values;
        
        if (form.config.validation) {
            const errors = this.validateForm(form);
            if (Object.keys(errors).length > 0) {
                form.errors = errors;
                this.renderForm(formId);
                return;
            }
        }
        
        if (form.config.onSubmit) {
            form.config.onSubmit(values, form);
        }
    }

    handleFormReset(formId) {
        const form = this.forms.get(formId);
        if (!form) return;

        form.values = {};
        form.errors = {};
        
        if (form.config.onReset) {
            form.config.onReset(form);
        }
        
        this.renderForm(formId);
    }

    validateForm(form) {
        const errors = {};
        
        form.fields.forEach(field => {
            const value = form.values[field.name];
            
            if (field.required && (!value || value.trim() === '')) {
                errors[field.name] = 'هذا الحقل مطلوب';
            }
            
            if (value && field.validation) {
                if (field.validation.minLength && value.length < field.validation.minLength) {
                    errors[field.name] = `يجب أن يكون الحد الأدنى ${field.validation.minLength} أحرف`;
                }
                
                if (field.validation.maxLength && value.length > field.validation.maxLength) {
                    errors[field.name] = `يجب أن يكون الحد الأقصى ${field.validation.maxLength} أحرف`;
                }
                
                if (field.validation.pattern && !field.validation.pattern.test(value)) {
                    errors[field.name] = field.validation.message || 'تنسيق غير صحيح';
                }
            }
        });
        
        return errors;
    }

    // Utility methods
    showConfirmDialog(title, message, onConfirm, onCancel = null) {
        const modalId = 'confirmDialog';
        
        this.createModal(modalId, title, `<p>${message}</p>`, {
            size: 'small',
            buttons: [
                {
                    text: 'إلغاء',
                    type: 'secondary',
                    dismiss: true,
                    onclick: onCancel ? `(${onCancel})(); components.closeModal('${modalId}')` : ''
                },
                {
                    text: 'تأكيد',
                    type: 'primary',
                    onclick: `(${onConfirm})(); components.closeModal('${modalId}')`
                }
            ]
        });
        
        this.showModal(modalId);
    }

    showAlert(title, message, type = 'info') {
        const modalId = 'alertDialog';
        
        this.createModal(modalId, title, `<p>${message}</p>`, {
            size: 'small',
            buttons: [
                {
                    text: 'موافق',
                    type: type === 'error' ? 'error' : 'primary',
                    dismiss: true
                }
            ]
        });
        
        this.showModal(modalId);
    }
}

// Create global components instance
window.components = new ComponentManager();


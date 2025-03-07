/**
 * Sistema de paginação para tabelas
 * Este script adiciona funcionalidades de paginação para tabelas de dados
 */

class TablePagination {
    constructor(tableId, options = {}) {
        this.tableId = tableId;
        this.table = document.getElementById(tableId);
        if (!this.table) return;
        
        this.options = {
            itemsPerPage: options.itemsPerPage || 10,
            pageInfoId: options.pageInfoId || 'current-page',
            totalPagesId: options.totalPagesId || 'total-pages',
            prevButtonId: options.prevButtonId || 'prev-page',
            nextButtonId: options.nextButtonId || 'next-page',
            pageSizeSelectId: options.pageSizeSelectId || 'items-per-page',
            itemSelector: options.itemSelector || 'tbody tr',
            ...options
        };
        
        this.currentPage = 1;
        this.items = this.table.querySelectorAll(this.options.itemSelector);
        this.totalItems = this.items.length;
        this.totalPages = Math.ceil(this.totalItems / this.options.itemsPerPage);
        
        this.init();
    }
    
    init() {
        // Configurar elementos de UI
        this.pageInfo = document.getElementById(this.options.pageInfoId);
        this.totalPagesInfo = document.getElementById(this.options.totalPagesId);
        this.prevButton = document.getElementById(this.options.prevButtonId);
        this.nextButton = document.getElementById(this.options.nextButtonId);
        this.pageSizeSelect = document.getElementById(this.options.pageSizeSelectId);
        
        // Inicializar informações
        if (this.totalPagesInfo) {
            this.totalPagesInfo.textContent = this.totalPages;
        }
        
        // Configurar eventos
        if (this.prevButton) {
            this.prevButton.addEventListener('click', () => this.changePage(-1));
        }
        
        if (this.nextButton) {
            this.nextButton.addEventListener('click', () => this.changePage(1));
        }
        
        if (this.pageSizeSelect) {
            this.pageSizeSelect.addEventListener('change', (e) => {
                this.changePageSize(parseInt(e.target.value));
            });
        }
        
        // Aplicar paginação inicial
        this.updateDisplay();
    }
    
    updateDisplay() {
        const startIdx = (this.currentPage - 1) * this.options.itemsPerPage;
        const endIdx = startIdx + this.options.itemsPerPage;
        
        // Atualizar visibilidade dos itens
        Array.from(this.items).forEach((item, index) => {
            if (index >= startIdx && index < endIdx) {
                item.style.display = '';
            } else {
                item.style.display = 'none';
            }
        });
        
        // Atualizar informações da página
        if (this.pageInfo) {
            this.pageInfo.textContent = this.currentPage;
        }
        
        // Atualizar estado dos botões
        this.updateButtonStates();
    }
    
    updateButtonStates() {
        if (this.prevButton) {
            this.prevButton.disabled = this.currentPage === 1;
            this.prevButton.classList.toggle('disabled', this.currentPage === 1);
        }
        
        if (this.nextButton) {
            this.nextButton.disabled = this.currentPage === this.totalPages;
            this.nextButton.classList.toggle('disabled', this.currentPage === this.totalPages);
        }
    }
    
    changePage(delta) {
        const newPage = this.currentPage + delta;
        if (newPage < 1 || newPage > this.totalPages) return;
        
        this.currentPage = newPage;
        this.updateDisplay();
    }
    
    changePageSize(size) {
        this.options.itemsPerPage = size;
        this.totalPages = Math.ceil(this.totalItems / this.options.itemsPerPage);
        
        if (this.totalPagesInfo) {
            this.totalPagesInfo.textContent = this.totalPages;
        }
        
        // Resetar para primeira página ao mudar tamanho
        this.currentPage = 1;
        this.updateDisplay();
    }
    
    goToPage(pageNumber) {
        if (pageNumber >= 1 && pageNumber <= this.totalPages) {
            this.currentPage = pageNumber;
            this.updateDisplay();
        }
    }
}

// Exportar para uso global
window.TablePagination = TablePagination;

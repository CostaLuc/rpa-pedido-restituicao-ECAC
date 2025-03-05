document.addEventListener('DOMContentLoaded', function() {
    // Aplica classe CSS específica para status concluído em tabelas de histórico
    const historyCells = document.querySelectorAll('.history-table td');
    
    historyCells.forEach(cell => {
        const text = cell.textContent.trim().toLowerCase();
        if (text === 'concluído' || text.includes('concluído com sucesso') || text.includes('processado com sucesso')) {
            cell.classList.add('status-concluído');
            cell.style.color = getComputedStyle(document.documentElement).getPropertyValue('--success-color');
        }
    });
    
    // Função para verificar e corrigir status periodicamente
    function checkAndFixStatusColors() {
        const statusCells = document.querySelectorAll('td');
        
        statusCells.forEach(cell => {
            const text = cell.textContent.trim().toLowerCase();
            if (text === 'concluído' || text.includes('concluído com sucesso') || text.includes('processado com sucesso')) {
                cell.classList.add('status-concluído');
                cell.style.color = getComputedStyle(document.documentElement).getPropertyValue('--success-color');
            }
        });
    }
    
    // Executar a verificação inicial e depois a cada segundo
    checkAndFixStatusColors();
    setInterval(checkAndFixStatusColors, 1000);
});

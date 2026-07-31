export function initSidebar() {
  const sidebar = document.querySelector('.sidebar');
  if (!sidebar) return;
  const collapseButton = sidebar.querySelector('[data-sidebar-toggle]');
  if (!collapseButton) return;
  collapseButton.addEventListener('click', () => {
    sidebar.classList.toggle('collapsed');
  });
}

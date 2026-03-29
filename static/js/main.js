/* Main JS - Placeholder for NiceAdmin template scripts */
(function() {
  'use strict';
  // Toggle sidebar
  const toggle = document.querySelector('.toggle-sidebar-btn');
  if (toggle) {
    toggle.addEventListener('click', function() {
      document.querySelector('body').classList.toggle('toggle-sidebar');
    });
  }
})();

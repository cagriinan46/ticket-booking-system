import React from 'react';

function Footer() {
  return (
    <footer className="bg-white border-t border-gray-300 mt-12 py-8">
      <div className="max-w-6xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center text-sm text-gray-600">
        <div className="mb-4 md:mb-0">
          <span className="font-bold text-gray-800 text-lg">BiletSistemi</span>
        </div>
      </div>
      <div className="text-center text-gray-500 text-xs mt-6">
        &copy; 2026 Tüm hakları saklıdır.
      </div>
    </footer>
  );
}

export default Footer;
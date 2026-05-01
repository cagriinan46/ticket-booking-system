import React from 'react';

function Footer() {
  return (
    <footer className="mt-16 py-10 border-t border-orange-200 bg-orange-50/40">
      <div className="max-w-6xl mx-auto px-6 flex flex-col items-center text-center">
        <span className="font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-orange-500 to-amber-500 text-3xl tracking-tight mb-2">PortaBilet</span>
        <p className="text-gray-500 text-sm font-medium mb-6">Eğlencenin en sıcak hali.</p>
        <div className="text-orange-400 text-xs font-semibold">
          &copy; 2026 PortaBilet Tüm hakları saklıdır.
        </div>
      </div>
    </footer>
  );
}

export default Footer;
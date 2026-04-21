import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

function Navbar() {
  const navigate = useNavigate();
  const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
  const isAdmin = localStorage.getItem('isAdmin') === 'true';

  const handleLogout = () => {
    localStorage.removeItem('isLoggedIn');
    localStorage.removeItem('token');
    localStorage.removeItem('isAdmin');
    toast.success('Başarıyla çıkış yapıldı.');
    navigate('/login');
  };

  return (
    <nav className="flex justify-between items-center p-4 bg-blue-800 text-white mb-4 shadow-md">
      <Link to="/" className="text-xl font-bold tracking-wide">BiletSistemi</Link>
      
      <div className="space-x-4 flex items-center">
        <Link to="/" className="hover:underline text-sm">Ana Sayfa</Link>
        <span className="text-gray-400">|</span>
        <Link to="/about" className="hover:underline text-sm">Hakkında</Link>
        
        {(isLoggedIn && isAdmin) && (
          <>
            <span className="text-gray-400">|</span>
            <Link to="/admin" className="bg-red-600 text-white px-3 py-1.5 rounded text-sm font-bold hover:bg-red-700 shadow-sm">
            Yönetim Paneli
            </Link>
          </>
        )}
      </div>

      <div className="flex items-center gap-4">
        {isLoggedIn ? (
          <>
            <Link to="/profile" className="text-sm hover:underline font-semibold">Biletlerim</Link>
            <button 
              onClick={handleLogout}
              className="bg-red-600 text-white border border-red-700 px-4 py-1.5 rounded hover:bg-red-700 text-sm font-semibold transition"
            >
              Çıkış Yap
            </button>
          </>
        ) : (
          <Link to="/login" className="bg-gray-100 text-blue-800 border border-gray-300 px-4 py-1.5 rounded hover:bg-white text-sm font-semibold transition">
            Giriş Yap
          </Link>
        )}
      </div>
    </nav>
  );
}

export default Navbar;
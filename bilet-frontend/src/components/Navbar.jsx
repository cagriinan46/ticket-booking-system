import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

function Navbar() {
  const navigate = useNavigate();
  const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
  const isAdmin = localStorage.getItem('isAdmin') === 'true';

  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleLogout = () => {
    localStorage.clear(); 
    setIsDropdownOpen(false);
    toast.success('Başarıyla çıkış yapıldı.');
    navigate('/login');
  };

  return (
    <nav className="mx-4 mt-4 mb-6 px-6 py-4 flex justify-between items-center bg-gradient-to-r from-orange-500 to-amber-500 text-white rounded-2xl shadow-lg border border-orange-400/30 relative z-50">
      
      {/* LOGO */}
      <Link to="/" className="flex items-center gap-1 group">
        <span className="text-2xl font-extrabold tracking-tight drop-shadow-sm text-white">
          PortaBilet
        </span>
        <div className="relative -top-2.5 group-hover:-translate-y-1 group-hover:rotate-12 transition-all duration-300">
          <svg className="w-7 h-7 drop-shadow-md" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="14" r="8" fill="#FBBF24" stroke="#FFFFFF" strokeWidth="2"/>
            <path d="M7.5 12A4.5 4.5 0 0 1 12 7.5" stroke="#FDE68A" strokeWidth="2" strokeLinecap="round"/>
            <path d="M12 6C14 2 18 2 18 2C18 2 17 7 12 6Z" fill="#4ADE80" stroke="#FFFFFF" strokeWidth="1.5" strokeLinejoin="round"/>
            <path d="M12 6C11.5 4 10 3 10 3" stroke="#FFFFFF" strokeWidth="2" strokeLinecap="round"/>
          </svg>
        </div>
      </Link>
      
      <div className="hidden md:flex space-x-6 items-center font-medium">
        <Link to="/" className="hover:text-orange-100 transition-colors">Ana Sayfa</Link>
        <span className="text-orange-300">•</span>
        <Link to="/about" className="hover:text-orange-100 transition-colors">Hakkında</Link>
        
        {(isLoggedIn && isAdmin) && (
          <>
            <span className="text-orange-300">•</span>
            <Link to="/admin" className="bg-white/20 backdrop-blur-sm border border-white/20 text-white px-4 py-2 rounded-xl text-sm font-bold hover:bg-white/30 shadow-sm transition-all">
              Yönetim Paneli
            </Link>
          </>
        )}
      </div>

      <div className="flex items-center gap-4">
        {isLoggedIn ? (
          <>
            <Link 
              to="/my-tickets" 
              className="flex items-center gap-1.5 bg-white/20 hover:bg-white/30 border border-white/20 backdrop-blur-sm px-3.5 py-1.5 rounded-xl text-sm font-bold transition-all shadow-sm mr-1"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z" /></svg>
              Biletlerim
            </Link>
            
            <div className="relative" ref={dropdownRef}>
              <button 
                onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                className="flex items-center gap-2 bg-white text-orange-600 px-4 py-2 rounded-xl text-sm font-bold hover:bg-orange-50 shadow-md transition-all"
              >
                Hesabım
                <svg className={`w-4 h-4 transition-transform duration-300 ${isDropdownOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {isDropdownOpen && (
                <div className="absolute right-0 mt-3 w-56 bg-white rounded-2xl shadow-xl border border-gray-100 py-2 overflow-hidden origin-top-right animate-fade-in-up">
                  
                  <div className="px-2">
                    <Link to="/profile" onClick={() => setIsDropdownOpen(false)} className="flex items-center gap-3 px-4 py-2.5 text-sm font-bold text-gray-700 hover:bg-orange-50 hover:text-orange-600 rounded-xl transition-colors">
                      <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>
                      Profilim
                    </Link>
                    <Link to="/settings" onClick={() => setIsDropdownOpen(false)} className="flex items-center gap-3 px-4 py-2.5 text-sm font-bold text-gray-700 hover:bg-orange-50 hover:text-orange-600 rounded-xl transition-colors">
                      <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                      Ayarlar
                    </Link>
                  </div>

                  <hr className="my-1.5 border-gray-100" />

                  <div className="px-2">
                    <Link to="/favorites" onClick={() => setIsDropdownOpen(false)} className="flex items-center gap-3 px-4 py-2.5 text-sm font-bold text-gray-700 hover:bg-orange-50 hover:text-orange-600 rounded-xl transition-colors">
                      <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" /></svg>
                      Favorilerim
                    </Link>
                    <Link to="/reviews" onClick={() => setIsDropdownOpen(false)} className="flex items-center gap-3 px-4 py-2.5 text-sm font-bold text-gray-700 hover:bg-orange-50 hover:text-orange-600 rounded-xl transition-colors">
                      <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" /></svg>
                      Değerlendirmelerim
                    </Link>
                  </div>

                  <hr className="my-1.5 border-gray-100" />

                  <div className="px-2">
                    <button 
                      onClick={handleLogout} 
                      className="w-full flex items-center gap-3 px-4 py-2.5 text-sm font-bold text-red-500 hover:bg-red-50 rounded-xl transition-colors"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" /></svg>
                      Çıkış Yap
                    </button>
                  </div>
                </div>
              )}
            </div>
          </>
        ) : (
          <Link to="/login" className="bg-white text-orange-600 px-6 py-2 rounded-xl text-sm font-bold hover:bg-orange-50 shadow-md transition-all">
            Giriş Yap
          </Link>
        )}
      </div>
    </nav>
  );
}

export default Navbar;
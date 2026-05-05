import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import EventCard from './EventCard';

function Navbar() {
  const backendUrl = import.meta.env.VITE_API_URL;
  const navigate = useNavigate();
  const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
  const isAdmin = localStorage.getItem('isAdmin') === 'true';

  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);

  const [isAiModalOpen, setIsAiModalOpen] = useState(false);
  const [aiPrompt, setAiPrompt] = useState('');
  const [isAiSearching, setIsAiSearching] = useState(false);
  const [aiEvents, setAiEvents] = useState([]);
  const [aiFiltersApplied, setAiFiltersApplied] = useState(null);
  const [hasSearched, setHasSearched] = useState(false);
  const [favoriteIds, setFavoriteIds] = useState([]);

  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    if (isAiModalOpen && isLoggedIn) {
      const token = localStorage.getItem('token');
      fetch(`${backendUrl}/api/events/my-favorites`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      .then(res => res.ok ? res.json() : [])
      .then(data => {
        if (Array.isArray(data)) {
          setFavoriteIds(data.map(ev => ev.id));
        }
      })
      .catch(err => console.error("Favoriler çekilemedi:", err));
    }
  }, [isAiModalOpen, isLoggedIn, backendUrl]);

  const handleLogout = () => {
    localStorage.clear(); 
    setIsDropdownOpen(false);
    toast.success('Başarıyla çıkış yapıldı.');
    navigate('/login');
  };

  const handleAiSearch = async () => {
    if (!aiPrompt.trim()) return;
    setIsAiSearching(true);
    setHasSearched(true);
    
    try {
      const response = await fetch(`${backendUrl}/api/events/ai-search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: aiPrompt })
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || "Yapay zeka aramasında bir hata oluştu.");
      }

      setAiEvents(data.events);
      setAiFiltersApplied(data.filters_applied);
      toast.success("Yapay zeka size uygun etkinlikleri buldu!");
      
    } catch (err) {
      toast.error(err.message);
    } finally {
      setIsAiSearching(false);
    }
  };

  const handleToggleFavorite = async (eventId) => {
    const token = localStorage.getItem('token');
    if (!token) {
      toast.error("Favorilere eklemek için önce giriş yapmalısınız!");
      return;
    }

    const isCurrentlyFav = favoriteIds.includes(eventId);
    setFavoriteIds(isCurrentlyFav 
      ? favoriteIds.filter(id => id !== eventId) 
      : [...favoriteIds, eventId]
    );

    try {
      const response = await fetch(`${backendUrl}/api/events/toggle-favorite/${eventId}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail);
      toast.success(data.message);
    } catch (err) {
      toast.error(err.message);
    }
  };

  const closeModal = () => {
    setIsAiModalOpen(false);
  };

  return (
    <>
      <nav className="mx-4 mt-4 mb-6 px-6 py-4 flex justify-between items-center bg-gradient-to-r from-orange-500 to-amber-500 text-white rounded-2xl shadow-lg border border-orange-400/30 relative z-40">
        
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
        
        <div className="flex items-center gap-4">
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

          <div className="hidden md:block w-px h-6 bg-orange-300/50 ml-2"></div>
          <button 
            onClick={() => setIsAiModalOpen(true)}
            className="flex items-center gap-1.5 bg-white/20 hover:bg-white/30 border border-white/20 backdrop-blur-sm px-3.5 py-1.5 rounded-xl text-sm font-bold transition-all shadow-sm"
          >
            <svg className="w-4 h-4 text-white/90 drop-shadow-sm" fill="currentColor" viewBox="0 0 24 24">
              <path d="M21.5 12.5L19.22 17.5L14.22 19.78L19.22 22.06L21.5 27.06L23.78 22.06L28.78 19.78L23.78 17.5L21.5 12.5ZM10.5 2.5L7.28 9.53L0.25 12.75L7.28 15.97L10.5 23L13.72 15.97L20.75 12.75L13.72 9.53L10.5 2.5Z" transform="scale(0.8) translate(3, 3)"/>
            </svg>
            <span className="hidden sm:inline">Yapay Zeka ile Ara</span>
            <span className="sm:hidden">AI ile Ara</span>
          </button>
        </div>

        <div className="flex items-center gap-3">
          {isLoggedIn ? (
            <>
              <Link 
                to="/my-tickets" 
                className="flex items-center gap-1.5 bg-white/20 hover:bg-white/30 border border-white/20 backdrop-blur-sm px-3.5 py-1.5 rounded-xl text-sm font-bold transition-all shadow-sm"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z" /></svg>
                <span className="hidden sm:inline">Biletlerim</span>
              </Link>
              
              <div className="relative" ref={dropdownRef}>
                <button 
                  onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                  className="flex items-center gap-2 bg-white text-orange-600 px-4 py-2 rounded-xl text-sm font-bold hover:bg-orange-50 shadow-md transition-all"
                >
                  <span className="hidden sm:inline">Hesabım</span>
                  <svg className={`w-4 h-4 transition-transform duration-300 ${isDropdownOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                  </svg>
                </button>

                {isDropdownOpen && (
                  <div className="absolute right-0 mt-3 w-56 bg-white rounded-2xl shadow-xl border border-gray-100 py-2 overflow-hidden origin-top-right animate-fade-in-up z-50">
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
                      <button onClick={handleLogout} className="w-full flex items-center gap-3 px-4 py-2.5 text-sm font-bold text-red-500 hover:bg-red-50 rounded-xl transition-colors">
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

      {isAiModalOpen && (
        <div className="fixed inset-0 z-[100] bg-gray-900/60 backdrop-blur-sm flex justify-center items-start pt-10 md:pt-20 px-4 overflow-y-auto">
          
          <div className="bg-white rounded-3xl w-full max-w-5xl shadow-2xl overflow-hidden border border-orange-100 flex flex-col relative mb-10">
            
            <div className="p-6 md:p-8 bg-gradient-to-b from-orange-50 to-white border-b border-orange-100 relative">
              <button 
                onClick={closeModal} 
                className="absolute top-6 right-6 p-2 bg-white text-gray-400 hover:text-red-500 rounded-full shadow-sm hover:shadow-md transition-all border border-gray-100"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"/></svg>
              </button>

              <h2 className="text-2xl md:text-3xl font-extrabold text-gray-800 flex items-center gap-2 mb-6">
                <svg className="w-8 h-8 text-orange-500" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M21.5 12.5L19.22 17.5L14.22 19.78L19.22 22.06L21.5 27.06L23.78 22.06L28.78 19.78L23.78 17.5L21.5 12.5ZM10.5 2.5L7.28 9.53L0.25 12.75L7.28 15.97L10.5 23L13.72 15.97L20.75 12.75L13.72 9.53L10.5 2.5Z" transform="scale(0.8)"/>
                </svg>
                Yapay Zeka ile <span className="text-orange-500">Etkinlik Bul</span>
              </h2>

              <div className="flex flex-col md:flex-row gap-3">
                <div className="flex-grow relative">
                  <svg className="w-6 h-6 text-orange-400 absolute left-4 top-1/2 transform -translate-y-1/2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
                  <input 
                    type="text" 
                    value={aiPrompt}
                    onChange={(e) => setAiPrompt(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleAiSearch()}
                    placeholder="Örn: 20-30 Mayıs arası İstanbul'da tiyatro var mı?" 
                    className="w-full pl-12 pr-4 py-4 bg-white border border-gray-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-orange-400 focus:border-orange-400 transition-all text-gray-700 shadow-sm text-lg"
                  />
                </div>
                <button 
                  onClick={handleAiSearch}
                  disabled={!aiPrompt.trim() || isAiSearching}
                  className="bg-gradient-to-r from-orange-500 to-amber-500 text-white font-bold py-4 px-10 rounded-2xl hover:scale-105 transition-transform disabled:opacity-50 disabled:hover:scale-100 flex items-center justify-center shadow-md text-lg"
                >
                  {isAiSearching ? 'Aranıyor...' : 'Ara'}
                </button>
              </div>

              {hasSearched && !isAiSearching && aiFiltersApplied && (
                <div className="mt-4 flex flex-wrap gap-2 items-center text-sm">
                  <span className="text-gray-500 font-bold mr-1">Filtreler:</span>
                  {aiFiltersApplied.city && <span className="bg-orange-100 text-orange-700 px-3 py-1 rounded-full font-bold">📍 {aiFiltersApplied.city}</span>}
                  {aiFiltersApplied.category && <span className="bg-orange-100 text-orange-700 px-3 py-1 rounded-full font-bold">🎭 {aiFiltersApplied.category}</span>}
                  {(aiFiltersApplied.start_date || aiFiltersApplied.end_date) && (
                    <span className="bg-orange-100 text-orange-700 px-3 py-1 rounded-full font-bold">
                      📅 {aiFiltersApplied.start_date || 'Geçmiş'} - {aiFiltersApplied.end_date || 'Gelecek'}
                    </span>
                  )}
                  {Object.values(aiFiltersApplied).every(v => v === null) && (
                    <span className="bg-gray-100 text-gray-500 px-3 py-1 rounded-full font-bold">Belirli bir filtre bulunamadı.</span>
                  )}
                </div>
              )}
            </div>

            <div className="p-6 md:p-8 bg-gray-50 flex-grow overflow-y-auto max-h-[60vh]">
              {isAiSearching ? (
                <div className="py-20 text-center">
                  <div className="inline-block w-12 h-12 border-4 border-orange-200 border-t-orange-500 rounded-full animate-spin mb-4"></div>
                  <p className="text-orange-500 font-extrabold text-xl animate-pulse">Sizin için en iyi etkinlikler taranıyor...</p>
                </div>
              ) : hasSearched ? (
                aiEvents.length === 0 ? (
                  <div className="text-center py-16 bg-white rounded-2xl border border-gray-100 shadow-sm">
                    <div className="text-6xl mb-4"></div>
                    <p className="text-gray-600 font-bold text-lg">Yapay zeka aramanıza uygun bir etkinlik bulamadı.</p>
                    <p className="text-gray-400 mt-2">Lütfen farklı kelimelerle veya tarihlerle tekrar deneyin.</p>
                  </div>
                ) : (
                  <div>
                    <h3 className="font-extrabold text-gray-800 mb-6 text-xl">{aiEvents.length} Etkinlik Bulundu</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                      {aiEvents.map(event => {
                        const eventWithImage = {
                          ...event,
                          image: event.image || 'https://images.unsplash.com/photo-1459749411175-04bf5292ceea?w=500&q=80'
                        };
                        const isCriticalStock = event.available_tickets > 0 && event.available_tickets <= 10;
                        const isSoldOut = event.available_tickets === 0;

                        return (
                          <div key={event.id} className="relative" onClick={closeModal}>
                            {isSoldOut && (
                              <div className="absolute -top-3 -right-3 z-20 bg-gray-900 text-white font-black text-xs px-4 py-2 rounded-full shadow-lg border-2 border-white transform rotate-3">
                                TÜKENDİ
                              </div>
                            )}
                            {isCriticalStock && (
                              <div className="absolute -top-3 -right-3 z-20 bg-red-500 text-white font-black text-xs px-4 py-2 rounded-full shadow-lg border-2 border-white animate-pulse">
                                Son {event.available_tickets} Bilet!
                              </div>
                            )}
                            <EventCard 
                              event={eventWithImage} 
                              isFavorite={favoriteIds.includes(event.id)} 
                              onToggleFavorite={handleToggleFavorite} 
                            />
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )
              ) : (
                <div className="text-center py-20 text-gray-400">
                  <svg className="w-16 h-16 mx-auto mb-4 text-orange-200" fill="currentColor" viewBox="0 0 24 24"><path d="M21.5 12.5L19.22 17.5L14.22 19.78L19.22 22.06L21.5 27.06L23.78 22.06L28.78 19.78L23.78 17.5L21.5 12.5Z" transform="scale(0.8)"/></svg>
                  <p className="font-bold text-lg text-gray-500">Ne tür bir etkinlik arıyorsunuz?</p>
                  <p className="text-sm mt-1">Yapay zekaya istediğiniz şehri, kategoriyi ve tarihi söylemeniz yeterli.</p>
                </div>
              )}
            </div>
            
          </div>
        </div>
      )}
    </>
  );
}

export default Navbar;
import React, { useState, useEffect } from 'react';
import EventCard from '../components/EventCard';
import toast from 'react-hot-toast';

function Home() {
  const backendUrl = import.meta.env.VITE_API_URL;
  const [events, setEvents] = useState([]);
  const [favoriteIds, setFavoriteIds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCity, setSelectedCity] = useState('Tümü');
  const [selectedCategory, setSelectedCategory] = useState('Tümü');

  const categories = ['Tümü', 'Konser', 'Tiyatro', 'Festival', 'Stand-up', 'Spor'];
  const cities = [
    'Tümü', "İstanbul", "Ankara", "İzmir", "Adana", "Adıyaman", "Afyonkarahisar", "Ağrı", "Aksaray", "Amasya",  "Antalya", "Ardahan", "Artvin", "Aydın", "Balıkesir", "Bartın", "Batman", "Bayburt", "Bilecik", "Bingöl", "Bitlis", "Bolu", "Burdur", "Bursa", "Çanakkale", "Çankırı", "Çorum", "Denizli", "Diyarbakır", "Düzce", "Edirne", "Elazığ", "Erzincan", "Erzurum", "Eskişehir", "Gaziantep", "Giresun", "Gümüşhane", "Hakkari", "Hatay", "Iğdır", "Isparta", "Kahramanmaraş", "Karabük", "Karaman", "Kars", "Kastamonu", "Kayseri", "Kırıkkale", "Kırklareli", "Kırşehir", "Kilis", "Kocaeli", "Konya", "Kütahya", "Malatya", "Manisa", "Mardin", "Mersin", "Muğla", "Muş", "Nevşehir", "Niğde", "Ordu", "Osmaniye", "Rize", "Sakarya", "Samsun", "Siirt", "Sinop", "Sivas", "Şanlıurfa", "Şırnak", "Tekirdağ", "Tokat", "Trabzon", "Tunceli", "Uşak", "Van", "Yalova", "Yozgat", "Zonguldak"
  ];

  const fetchEventsAndFavorites = async () => {
    try {
      const eventsRes = await fetch(`${backendUrl}/api/events`);
      if (!eventsRes.ok) throw new Error("Etkinlikler yüklenemedi.");
      const eventsData = await eventsRes.json();
      setEvents(eventsData);

      const token = localStorage.getItem('token');
      if (token) {
        const favRes = await fetch(`${backendUrl}/api/events/my-favorites`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (favRes.ok) {
          const favData = await favRes.json();
          const favIds = favData.map(ev => ev.id);
          setFavoriteIds(favIds);
        }
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEventsAndFavorites();
  }, []);

  const handleToggleFavorite = async (eventId) => {
    const token = localStorage.getItem('token');
    if (!token) {
      toast.error("Favorilere eklemek için önce giriş yapmalısınız!");
      return;
    }

    const isCurrentlyFav = favoriteIds.includes(eventId);
    if (isCurrentlyFav) {
      setFavoriteIds(favoriteIds.filter(id => id !== eventId));
    } else {
      setFavoriteIds([...favoriteIds, eventId]);
    }

    try {
      const response = await fetch(`${backendUrl}/api/events/toggle-favorite/${eventId}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      
      if (!response.ok) {
        fetchEventsAndFavorites();
        throw new Error(data.detail);
      }
      
      toast.success(data.message);
    } catch (err) {
      toast.error(err.message);
    }
  };

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const filteredEvents = events.filter(event => {
    const matchSearch = event.title.toLowerCase().includes(searchTerm.toLowerCase());
    const matchCity = selectedCity === 'Tümü' || event.city === selectedCity;
    const matchCategory = selectedCategory === 'Tümü' || event.category === selectedCategory;
    
    const eventDate = new Date(event.date);
    const isUpcoming = eventDate >= today;
    
    return matchSearch && matchCity && matchCategory && isUpcoming;
  });

  return (
    <div className="px-2 md:px-0">
      <div className="bg-white border border-orange-100 p-8 rounded-3xl mb-10 shadow-xl shadow-orange-900/5">
        <div className="flex flex-wrap gap-3 justify-center mb-8">
          {categories.map(cat => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-6 py-2.5 rounded-full text-sm font-bold transition-all duration-300 ${
                selectedCategory === cat 
                  ? 'bg-gradient-to-r from-orange-500 to-amber-500 text-white shadow-md shadow-orange-500/30 scale-105' 
                  : 'bg-orange-50 text-orange-800 hover:bg-orange-100 hover:scale-105'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        <div className="flex flex-col md:flex-row justify-center max-w-3xl mx-auto gap-4">
          <input 
            type="text" 
            placeholder="Etkinlik, sanatçı veya mekan ara..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="flex-grow px-5 py-3.5 bg-gray-50 border border-gray-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-orange-400 focus:bg-white transition-all text-gray-700"
          />
          <select 
            value={selectedCity}
            onChange={(e) => setSelectedCity(e.target.value)}
            className="px-5 py-3.5 bg-gray-50 border border-gray-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-orange-400 focus:bg-white transition-all font-medium text-gray-700 min-w-[160px] cursor-pointer"
          >
            {cities.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>
      </div>

      <div className="flex justify-between items-center mb-8 px-2">
        <h2 className="text-2xl font-extrabold text-gray-800 tracking-tight">
          {selectedCategory !== 'Tümü' ? `${selectedCategory} Etkinlikleri` : 'Popüler Etkinlikler'}
        </h2>
        <span className="text-sm font-bold text-orange-700 bg-orange-100 px-4 py-1.5 rounded-full">
          {filteredEvents.length} Sonuç
        </span>
      </div>

      {loading && <p className="text-center text-orange-500 font-medium py-10 animate-pulse">Etkinlikler yükleniyor, lütfen bekleyin...</p>}
      {error && <p className="text-center text-red-500 font-medium py-10">{error}</p>}

      {!loading && !error && filteredEvents.length === 0 ? (
        <div className="text-center py-24 bg-white rounded-3xl border border-gray-100 shadow-sm">
          <div className="text-6xl mb-4">🔍</div>
          <p className="text-gray-500 font-medium text-lg">Aradığınız kriterlere uygun güncel etkinlik bulunamadı.</p>
          <button onClick={() => {setSearchTerm(''); setSelectedCity('Tümü'); setSelectedCategory('Tümü');}} className="mt-6 text-orange-500 font-bold hover:text-orange-600 hover:underline transition-colors">
            Filtreleri Temizle
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {filteredEvents.map(event => {
            const eventWithImage = {
              ...event,
              image: event.image || 'https://images.unsplash.com/photo-1459749411175-04bf5292ceea?w=500&q=80'
            };
            
            const isCriticalStock = event.available_tickets > 0 && event.available_tickets <= 10;
            const isSoldOut = event.available_tickets === 0;

            return (
              <div key={event.id} className="relative">
                {isSoldOut && (
                  <div className="absolute -top-3 -right-3 z-20 bg-gray-900 text-white font-black text-xs px-4 py-2 rounded-full shadow-lg border-2 border-white transform rotate-3">
                    TÜKENDİ
                  </div>
                )}
                
                {isCriticalStock && (
                  <div className="absolute -top-3 -right-3 z-20 bg-red-500 text-white font-black text-xs px-4 py-2 rounded-full shadow-lg border-2 border-white animate-pulse">
                    🔥 Son {event.available_tickets} Bilet!
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
      )}
    </div>
  );
}

export default Home;
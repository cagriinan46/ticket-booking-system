import React, { useState, useEffect } from 'react';
import EventCard from '../components/EventCard';

function Home() {
  const backendUrl = import.meta.env.VITE_API_URL;
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCity, setSelectedCity] = useState('Tümü');
  const [selectedCategory, setSelectedCategory] = useState('Tümü');

  const categories = ['Tümü', 'Konser', 'Tiyatro', 'Festival', 'Stand-up', 'Spor'];
  const cities = [
    'Tümü', "İstanbul", "Ankara", "İzmir", "Adana", "Adıyaman", "Afyonkarahisar", "Ağrı", "Aksaray", "Amasya",  "Antalya", "Ardahan", "Artvin", "Aydın", "Balıkesir", "Bartın", "Batman", "Bayburt", "Bilecik", "Bingöl", "Bitlis", "Bolu", "Burdur", "Bursa", "Çanakkale", "Çankırı", "Çorum", "Denizli", "Diyarbakır", "Düzce", "Edirne", "Elazığ", "Erzincan", "Erzurum", "Eskişehir", "Gaziantep", "Giresun", "Gümüşhane", "Hakkari", "Hatay", "Iğdır", "Isparta", "Kahramanmaraş", "Karabük", "Karaman", "Kars", "Kastamonu", "Kayseri", "Kırıkkale", "Kırklareli", "Kırşehir", "Kilis", "Kocaeli", "Konya", "Kütahya", "Malatya", "Manisa", "Mardin", "Mersin", "Muğla", "Muş", "Nevşehir", "Niğde", "Ordu", "Osmaniye", "Rize", "Sakarya", "Samsun", "Siirt", "Sinop", "Sivas", "Şanlıurfa", "Şırnak", "Tekirdağ", "Tokat", "Trabzon", "Tunceli", "Uşak", "Van", "Yalova", "Yozgat", "Zonguldak"
  ];

  useEffect(() => {
    fetch(`${backendUrl}/api/events`)
      .then(res => {
        if (!res.ok) throw new Error("Etkinlikler yüklenemedi.");
        return res.json();
      })
      .then(data => {
        setEvents(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  const filteredEvents = events.filter(event => {
    const matchSearch = event.title.toLowerCase().includes(searchTerm.toLowerCase());
    const matchCity = selectedCity === 'Tümü' || event.city === selectedCity;
    const matchCategory = selectedCategory === 'Tümü' || event.category === selectedCategory;
    
    return matchSearch && matchCity && matchCategory;
  });

  return (
    <div>
      <div className="bg-white border border-gray-200 p-6 rounded mb-8 shadow-sm">
        <div className="flex flex-wrap gap-2 justify-center mb-6">
          {categories.map(cat => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-5 py-2 rounded text-sm font-bold transition-all ${
                selectedCategory === cat 
                  ? 'bg-blue-600 text-white shadow-sm' 
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        <div className="flex flex-col md:flex-row justify-center max-w-2xl mx-auto gap-3">
          <input 
            type="text" 
            placeholder="Etkinlik, sanatçı veya mekan ara..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="flex-grow px-4 py-3 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <select 
            value={selectedCity}
            onChange={(e) => setSelectedCity(e.target.value)}
            className="px-4 py-3 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white font-medium text-gray-700 min-w-[150px]"
          >
            {cities.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>
      </div>

      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-bold text-gray-800">
          {selectedCategory !== 'Tümü' ? `${selectedCategory} Etkinlikleri` : 'Tüm Etkinlikler'}
        </h2>
        <span className="text-sm font-semibold text-gray-500 bg-gray-100 px-3 py-1 rounded">
          {filteredEvents.length} Sonuç
        </span>
      </div>

      {loading && <p className="text-center text-gray-500 py-10">Etkinlikler yükleniyor...</p>}
      {error && <p className="text-center text-red-500 py-10">{error}</p>}

      {!loading && !error && filteredEvents.length === 0 ? (
        <div className="text-center py-20 bg-white rounded border border-gray-100">
          <p className="text-gray-500 font-medium text-lg">Aradığınız kriterlere uygun etkinlik bulunamadı.</p>
          <button onClick={() => {setSearchTerm(''); setSelectedCity('Tümü'); setSelectedCategory('Tümü');}} className="mt-4 text-blue-600 font-bold hover:underline">
            Filtreleri Temizle
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredEvents.map(event => {
            const eventWithImage = {
              ...event,
              image: event.image || 'https://images.unsplash.com/photo-1459749411175-04bf5292ceea?w=500&q=80'
            };
            return <EventCard key={event.id} event={eventWithImage} />;
          })}
        </div>
      )}
    </div>
  );
}

export default Home;
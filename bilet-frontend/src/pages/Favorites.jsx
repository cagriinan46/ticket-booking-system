import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import EventCard from '../components/EventCard';
import toast from 'react-hot-toast';

function Favorites() {
  const backendUrl = import.meta.env.VITE_API_URL;
  const navigate = useNavigate();
  const [favoriteEvents, setFavoriteEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchFavorites = () => {
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/login');
      return;
    }

    fetch(`${backendUrl}/api/my-favorites`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
      .then(res => {
        if (!res.ok) throw new Error("Favoriler çekilemedi.");
        return res.json();
      })
      .then(data => {
        setFavoriteEvents(data);
        setLoading(false);
      })
      .catch(err => {
        toast.error(err.message);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchFavorites();
  }, [navigate]);

  const handleToggleFavorite = async (eventId) => {
    const token = localStorage.getItem('token');
    try {
      const response = await fetch(`${backendUrl}/api/toggle-favorite/${eventId}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      const data = await response.json();
      
      if (!response.ok) throw new Error("Bir hata oluştu.");
      
      if (data.status === "removed") {
        setFavoriteEvents(prev => prev.filter(event => event.id !== eventId));
        toast.success("Favorilerden çıkarıldı", { icon: '💔' });
      } else {
        toast.success("Favorilere eklendi", { icon: '❤️' });
      }

    } catch (err) {
      toast.error("İşlem başarısız oldu.");
    }
  };

  return (
    <div className="max-w-6xl mx-auto mt-8 mb-20 px-4 md:px-0">
      
      <div className="flex items-center justify-between mb-8 pb-4 border-b border-red-100">
        <h2 className="text-3xl font-extrabold text-gray-900 tracking-tight flex items-center gap-3">
          Favorilerim
        </h2>
        <span className="bg-red-50 text-red-600 px-4 py-1.5 rounded-full text-sm font-bold border border-red-100">
          {favoriteEvents.length} Etkinlik
        </span>
      </div>

      {loading ? (
        <div className="py-20 text-center text-red-500 font-bold animate-pulse">Favorileriniz yükleniyor...</div>
      ) : favoriteEvents.length === 0 ? (
        <div className="bg-white border border-gray-100 py-20 rounded-3xl shadow-sm text-center">
          <h3 className="text-xl font-extrabold text-gray-800 mb-2">Henüz favori etkinliğiniz yok.</h3>
          <p className="text-gray-500 font-medium mb-6">İlginizi çeken etkinliklerdeki kalp ikonuna tıklayarak onları buraya ekleyebilirsiniz.</p>
          <Link to="/" className="bg-red-50 text-red-600 px-6 py-3 rounded-xl font-bold hover:bg-red-100 transition-colors">
            Etkinlikleri Keşfet
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {favoriteEvents.map((event) => (
            <EventCard 
              key={event.id} 
              event={event} 
              isFavorite={true} 
              onToggleFavorite={handleToggleFavorite} 
            />
          ))}
        </div>
      )}

    </div>
  );
}

export default Favorites;
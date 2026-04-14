import React, { useState, useEffect } from 'react';
import EventCard from '../components/EventCard';

function Home() {
  const backendUrl = import.meta.env.VITE_API_URL;
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(`${backendUrl}/api/events/`)
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

  return (
    <div>
      <div className="bg-blue-50 border border-blue-200 p-8 rounded mb-8 text-center">
        <h1 className="text-2xl font-bold mb-2 text-blue-900">Bilet Satış Sistemi</h1>
        <p className="text-gray-600 mb-6 text-sm">Etkinliklere göz at!</p>
        
        <div className="flex justify-center max-w-md mx-auto">
          <input 
            type="text" 
            placeholder="Etkinlik ara..." 
            className="w-full px-3 py-2 border border-gray-300 rounded-l focus:outline-none"
          />
          <button className="bg-blue-600 text-white px-6 py-2 rounded-r hover:bg-blue-700 font-bold">
            Ara
          </button>
        </div>
      </div>

      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-bold text-gray-800">Yaklaşan Etkinlikler</h2>
      </div>

      {loading && <p className="text-center text-gray-500 py-10">Etkinlikler yükleniyor...</p>}
      {error && <p className="text-center text-red-500 py-10">{error}</p>}

      {!loading && !error && events.length === 0 ? (
        <p className="text-center text-gray-500 py-10">Sistemde henüz hiç etkinlik yok.</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {events.map(event => {
            const eventWithImage = {
              ...event,
              image: 'https://images.unsplash.com/photo-1459749411175-04bf5292ceea?w=500&q=80'
            };
            return <EventCard key={event.id} event={eventWithImage} />;
          })}
        </div>
      )}
    </div>
  );
}

export default Home;
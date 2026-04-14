import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

function EventDetail() {
  const backendUrl = import.meta.env.VITE_API_URL;
  const { id } = useParams();
  const navigate = useNavigate();
  const [event, setEvent] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${backendUrl}/api/events/`)
      .then(res => res.json())
      .then(data => {
        const foundEvent = data.find(e => e.id === parseInt(id));
        if (foundEvent) {
          setEvent({
            ...foundEvent,
            image: 'https://images.unsplash.com/photo-1540039155732-6847350357a5?w=500&q=80',
            description: 'Bu muhteşem etkinliği kaçırmamak için hemen biletinizi alın! Yerler sınırlı.'
          });
        }
        setLoading(false);
      });
  }, [id]);

  const handleBuyClick = () => {
    const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
    if (!isLoggedIn) {
      toast.error('Bilet almak için lütfen önce giriş yapın!');
      navigate('/login');
      return;
    }
    navigate('/checkout', { state: { event } });
  };

  if (loading) return <div className="py-20 text-center">Yükleniyor...</div>;
  if (!event) return <div className="py-20 text-center text-red-500">Etkinlik bulunamadı!</div>;

  return (
    <div className="mt-4">
      <Link to="/" className="text-blue-600 hover:underline text-sm mb-6 inline-block">&larr; Listeye Dön</Link>
      
      <div className="flex flex-col md:flex-row gap-8">
        <div className="md:w-1/2">
          <img src={event.image} alt={event.title} className="w-full h-80 object-cover rounded border border-gray-200" />
        </div>
        
        <div className="md:w-1/2 flex flex-col">
          <span className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Etkinlik ID: {event.id}</span>
          <h1 className="text-3xl font-bold text-gray-900 mb-4">{event.title}</h1>
          
          <div className="bg-gray-50 p-4 border border-gray-200 rounded mb-6">
            <p className="text-gray-700 mb-2"><strong>Tarih:</strong> {event.date}</p>
            <p className="text-gray-700"><strong>Mekan:</strong> {event.location}</p>
          </div>
          
          <p className="text-gray-600 mb-8 leading-relaxed">{event.description}</p>
          
          <div className="mt-auto flex items-center justify-between border-t border-gray-200 pt-6">
            <span className="text-2xl font-bold text-gray-900">{event.price} ₺</span>
            <button 
              onClick={handleBuyClick}
              className="bg-green-600 text-white px-8 py-3 rounded font-bold hover:bg-green-700 shadow-sm"
            >
              Bilet Al
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default EventDetail;
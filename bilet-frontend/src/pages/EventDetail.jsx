import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

function EventDetail() {
  const backendUrl = import.meta.env.VITE_API_URL;
  const { id } = useParams();
  const navigate = useNavigate();
  
  const [event, setEvent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [reviews, setReviews] = useState([]);
  const [reviewsLoading, setReviewsLoading] = useState(true);
  
  const [weather, setWeather] = useState(null);
  const [weatherLoading, setWeatherLoading] = useState(true);

  const formatTurkishDate = (dateString) => {
    const date = new Date(dateString);
    if (isNaN(date)) return dateString; 
    
    const day = date.getDate();
    const month = date.toLocaleDateString('tr-TR', { month: 'long' });
    const weekday = date.toLocaleDateString('tr-TR', { weekday: 'long' });

    return `${day} ${month}, ${weekday}`; 
  };

  useEffect(() => {
    fetch(`${backendUrl}/api/events/${id}`)
      .then(res => {
        if (!res.ok) throw new Error("Etkinlik bulunamadı");
        return res.json();
      })
      .then(foundEvent => {
        setEvent({
          ...foundEvent,
          image: foundEvent.image || 'https://images.unsplash.com/photo-1540039155732-6847350357a5?w=500&q=80',
          description: foundEvent.description || 'Bu muhteşem etkinliği kaçırmamak için hemen biletinizi alın! Yerler sınırlı.'
        });
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });

    fetch(`${backendUrl}/api/events/${id}/reviews`)
      .then(res => {
        if (!res.ok) throw new Error("Yorumlar çekilemedi");
        return res.json();
      })
      .then(data => {
        setReviews(data);
        setReviewsLoading(false);
      })
      .catch(err => {
        console.error(err);
        setReviewsLoading(false);
      });

    fetch(`${backendUrl}/api/events/${id}/weather`)
      .then(res => res.json())
      .then(data => {
        setWeather(data);
        setWeatherLoading(false);
      })
      .catch(err => {
        console.error("Hava durumu çekilemedi", err);
        setWeatherLoading(false);
      });
  }, [id, backendUrl]);

  const handleBuyClick = () => {
    const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
    if (!isLoggedIn) {
      toast.error('Bilet almak için lütfen önce giriş yapın!');
      navigate('/login');
      return;
    }
    navigate('/checkout', { state: { event } });
  };

  const renderStars = (rating) => {
    return (
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <svg 
            key={star} 
            className={`w-4 h-4 ${star <= rating ? 'text-amber-400' : 'text-gray-200'}`} 
            fill="currentColor" 
            viewBox="0 0 20 20"
          >
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
          </svg>
        ))}
      </div>
    );
  };

  if (loading) return <div className="py-20 text-center text-orange-500 font-bold animate-pulse">Etkinlik Sahnede Yerini Alıyor...</div>;
  if (!event) return <div className="py-20 text-center text-red-500 font-bold text-xl">Etkinlik bulunamadı!</div>;

  return (
    <div className="max-w-6xl mx-auto mt-4 mb-20 px-4 md:px-0">
      <Link to="/" className="inline-flex items-center text-orange-500 hover:text-orange-600 font-bold text-sm mb-8 transition-colors">
        <span className="mr-2 text-lg">&larr;</span> Vitrine Dön
      </Link>
      
      <div className="flex flex-col lg:flex-row gap-10 bg-white p-6 md:p-8 rounded-3xl border border-orange-50 shadow-xl shadow-orange-900/5 mb-12">
        <div className="lg:w-1/2 relative overflow-hidden bg-gray-900 rounded-2xl shadow-inner h-[400px] md:h-[500px]">
          <img src={event.image} alt="" className="absolute inset-0 w-full h-full object-cover blur-2xl opacity-60 scale-110" />
          <img src={event.image} alt={event.title} className="relative z-10 w-full h-full object-contain drop-shadow-2xl" />
        </div>
        
        <div className="lg:w-1/2 flex flex-col justify-center">
          <div className="flex flex-wrap gap-2 mb-4">
            {event.category && (
              <span className="bg-orange-100 text-orange-700 px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider">
                {event.category}
              </span>
            )}
            {event.city && (
              <span className="bg-gray-100 text-gray-600 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border border-gray-200">
                {event.city}
              </span>
            )}
          </div>

          <h1 className="text-4xl font-extrabold text-gray-900 mb-6 leading-tight tracking-tight">{event.title}</h1>
          
          <div className="bg-orange-50/50 p-6 border border-orange-100 rounded-2xl mb-8 space-y-4">
            
            <div className="flex items-center">
              <div className="bg-white p-2 rounded-lg shadow-sm border border-orange-100 mr-4">
                <svg className="w-6 h-6 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
              </div>
              <div>
                <p className="text-xs text-gray-500 font-bold uppercase tracking-wider">Tarih ve Saat</p>
                <p className="text-gray-800 font-bold text-lg">
                  {formatTurkishDate(event.date)} 
                  {event.time && <span className="text-orange-600 ml-2">• {event.time}</span>}
                </p>
              </div>
            </div>
            
            <div className="flex items-center justify-between w-full">
              <div className="flex items-center">
                <div className="bg-white p-2 rounded-lg shadow-sm border border-orange-100 mr-4">
                  <svg className="w-6 h-6 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                </div>
                <div>
                  <p className="text-xs text-gray-500 font-bold uppercase tracking-wider">Mekan</p>
                  <p className="text-gray-800 font-bold text-lg">{event.location}</p>
                </div>
              </div>
              
              <a 
                href={`https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(event.location + ' ' + (event.city || ''))}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex flex-col items-center gap-1 text-blue-500 hover:text-blue-700 transition-colors bg-blue-50 p-2.5 rounded-xl hover:bg-blue-100 border border-blue-100 group"
              >
                <svg className="w-6 h-6 group-hover:scale-110 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
                </svg>
                <span className="text-[10px] font-extrabold uppercase tracking-widest">YOL TARİFİ</span>
              </a>
            </div>

            <div className="flex items-center justify-between w-full border-t border-orange-100/70 pt-4">
              <div className="flex items-center">
                <div className="bg-white p-2 rounded-lg shadow-sm border border-orange-100 mr-4">
                  <svg className="w-6 h-6 text-sky-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" /></svg>
                </div>
                <div>
                  <p className="text-xs text-gray-500 font-bold uppercase tracking-wider">Hava Durumu</p>
                  
                  {weatherLoading ? (
                    <p className="text-gray-400 font-bold text-sm animate-pulse">Tahmin alınıyor...</p>
                  ) : weather?.status === 'success' ? (
                    (() => {
                      const eventDateStr = event.date;
                      const exactTimeStr = event.time ? `${event.time}:00` : "12:00:00";
                      
                      const forecast = weather.data.list?.find(item => item.dt_txt.includes(eventDateStr) && item.dt_txt.includes(exactTimeStr))
                                    || weather.data.list?.find(item => item.dt_txt.includes(eventDateStr) && item.dt_txt.includes("12:00:00")) 
                                    || weather.data.list?.find(item => item.dt_txt.includes(eventDateStr)) 
                                    || weather.data.list[0];
                      
                      if (!forecast) return <p className="text-gray-500 font-bold text-sm">Tahmin alınamadı.</p>;

                      return (
                        <p className="text-gray-800 font-bold text-lg flex items-center gap-2">
                          {Math.round(forecast.main.temp)}°C 
                          <span className="text-sm font-medium text-gray-500 capitalize">
                            ({forecast.weather[0].description})
                          </span>
                        </p>
                      );
                    })()
                  ) : (
                    <p className="text-gray-500 font-bold text-sm">{weather?.message || "Tahmin için erken 🌤️"}</p>
                  )}
                </div>
              </div>
              
              {weather?.status === 'success' && (() => {
                const eventDateStr = event.date;
                const exactTimeStr = event.time ? `${event.time}:00` : "12:00:00";
                
                const forecast = weather.data.list?.find(item => item.dt_txt.includes(eventDateStr) && item.dt_txt.includes(exactTimeStr))
                              || weather.data.list?.find(item => item.dt_txt.includes(eventDateStr) && item.dt_txt.includes("12:00:00")) 
                              || weather.data.list?.find(item => item.dt_txt.includes(eventDateStr)) 
                              || weather.data.list[0];
                if (!forecast) return null;
                return (
                  <img 
                    src={`https://openweathermap.org/img/wn/${forecast.weather[0].icon}@2x.png`} 
                    alt="weather icon" 
                    className="w-12 h-12 drop-shadow-sm filter contrast-125"
                  />
                );
              })()}
            </div>

          </div>
          
          <div className="prose prose-orange max-w-none mb-10">
            <p className="text-gray-600 leading-relaxed whitespace-pre-wrap font-medium">
              {event.description}
            </p>
          </div>
          
          <div className="mt-auto border-t border-gray-100 pt-8">
            
            {event.available_tickets > 0 && event.available_tickets <= 10 && (
              <div className="mb-4 bg-red-50 border border-red-200 text-red-600 px-4 py-2 rounded-xl text-sm font-bold flex items-center gap-2 animate-pulse">
                <span>🔥</span> Son {event.available_tickets} bilet!
              </div>
            )}

            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-1">BİLET FİYATI</p>
                <span className="text-4xl font-black text-gray-900">{event.price} ₺</span>
              </div>
              
              <button 
                onClick={handleBuyClick}
                disabled={event.available_tickets === 0}
                className={`px-10 py-4 rounded-2xl font-extrabold text-lg transition-all duration-300 ${
                  event.available_tickets === 0 
                    ? 'bg-gray-200 text-gray-400 cursor-not-allowed' 
                    : 'bg-gradient-to-r from-orange-500 to-amber-500 text-white hover:shadow-lg hover:scale-105 hover:from-orange-600 hover:to-amber-600'
                }`}
              >
                {event.available_tickets === 0 ? 'Biletler Tükendi' : 'Hemen Bilet Al'}
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white p-6 md:p-8 rounded-3xl border border-gray-100 shadow-sm">
        <div className="flex items-center justify-between mb-8 pb-4 border-b border-gray-100">
          <h3 className="text-2xl font-extrabold text-gray-900 tracking-tight flex items-center gap-2">
            Değerlendirmeler
          </h3>
          <span className="bg-gray-50 text-gray-600 px-4 py-1.5 rounded-full text-sm font-bold border border-gray-200">
            {reviews.length} Yorum
          </span>
        </div>

        {reviewsLoading ? (
          <p className="text-center text-amber-500 font-bold animate-pulse py-6">Yorumlar yükleniyor...</p>
        ) : reviews.length === 0 ? (
          <div className="text-center py-10 bg-gray-50 rounded-2xl border border-gray-100">
            <p className="text-gray-500 font-bold">Bu etkinlik için henüz bir değerlendirme yapılmamış.</p>
            <p className="text-sm text-gray-400 mt-2">İlk yorumu yapan siz olun!</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {reviews.map((review) => (
              <div key={review.id} className="bg-gray-50 p-5 rounded-2xl border border-gray-100 flex flex-col items-start">
                
                <div className="flex justify-between items-center w-full mb-1">
                  <span className="font-extrabold text-gray-900">{review.user?.name || 'Gizli Kullanıcı'}</span>
                  {renderStars(review.rating)}
                </div>
                
                {review.comment ? (
                  <p className="text-gray-600 text-sm mt-2 leading-relaxed w-full">
                    "{review.comment}"
                  </p>
                ) : (
                  <p className="text-gray-400 text-sm mt-2 italic w-full">Yazılı yorum bırakılmamış.</p>
                )}
                
              </div>
            ))}
          </div>
        )}
      </div>
      
    </div>
  );
}

export default EventDetail;
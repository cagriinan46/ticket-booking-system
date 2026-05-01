import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

function MyTickets() {
  const backendUrl = import.meta.env.VITE_API_URL;
  const [tickets, setTickets] = useState([]);
  const [error, setError] = useState(null);
  
  const [activeTab, setActiveTab] = useState('upcoming');

  const [selectedQR, setSelectedQR] = useState(null);
  const [transferTicket, setTransferTicket] = useState(null); 
  const [targetEmail, setTargetEmail] = useState(''); 
  const [isTransferring, setIsTransferring] = useState(false);
  
  const [reviewTicket, setReviewTicket] = useState(null);
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState('');
  const [isSubmittingReview, setIsSubmittingReview] = useState(false);

  const navigate = useNavigate();

  const formatTurkishDate = (dateString) => {
    const date = new Date(dateString);
    if (isNaN(date)) return dateString; 
    
    const day = date.getDate();
    const month = date.toLocaleDateString('tr-TR', { month: 'long' });
    const weekday = date.toLocaleDateString('tr-TR', { weekday: 'long' });

    return `${day} ${month}, ${weekday}`;
  };

  const fetchTickets = () => {
    const token = localStorage.getItem('token'); 

    if (!token) {
      setError("Biletlerinizi görmek için lütfen giriş yapın.");
      return;
    }

    fetch(`${backendUrl}/api/events/my-tickets`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
      .then(res => {
        if (res.status === 401) {
          localStorage.removeItem('token');
          localStorage.removeItem('isLoggedIn');
          navigate('/login');
          throw new Error("Oturum süreniz dolmuş.");
        }
        if (!res.ok) throw new Error("Biletler çekilirken bir hata oluştu.");
        return res.json();
      })
      .then(data => {
        setTickets(data); 
      })
      .catch(err => {
        setError(err.message);
      });
  };

  useEffect(() => {
    fetchTickets();
  }, [navigate]);

  const handleTransferSubmit = async (e) => {
    e.preventDefault();
    if (!targetEmail) return toast.error("Lütfen bir e-posta adresi girin!");
    
    setIsTransferring(true);
    const token = localStorage.getItem('token');

    try {
      const response = await fetch(`${backendUrl}/api/events/ticket-transfer`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          id: transferTicket.id,
          target_email: targetEmail
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Transfer başarısız oldu.");
      }

      toast.success("Bilet başarıyla transfer edildi! 🚀");
      setTransferTicket(null); 
      setTargetEmail(''); 
      fetchTickets(); 

    } catch (err) {
      toast.error(err.message);
    } finally {
      setIsTransferring(false);
    }
  };

  const handleReviewSubmit = async (e) => {
    e.preventDefault();
    if (rating === 0) return toast.error("Lütfen en az 1 yıldız verin!");

    setIsSubmittingReview(true);
    const token = localStorage.getItem('token');

    try {
      const response = await fetch(`${backendUrl}/api/events/${reviewTicket.event.id}/reviews`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          rating: rating,
          comment: comment
        })
      });

      const data = await response.json();

      if (!response.ok) throw new Error(data.detail || "Değerlendirme kaydedilemedi.");

      toast.success(data.mesaj || "Değerlendirmeniz başarıyla eklendi! 🌟");
      
      setReviewTicket(null);
      setRating(0);
      setComment('');

    } catch (err) {
      toast.error(err.message);
    } finally {
      setIsSubmittingReview(false);
    }
  };

  const now = new Date();
  
  const upcomingTickets = tickets.filter(t => {
    const eventDate = new Date(t.event.date);
    if (isNaN(eventDate)) return true; 
    return eventDate >= now;
  });

  const pastTickets = tickets.filter(t => {
    const eventDate = new Date(t.event.date);
    if (isNaN(eventDate)) return false;
    return eventDate < now;
  });

  const displayTickets = activeTab === 'upcoming' ? upcomingTickets : pastTickets;

  return (
    <div className="max-w-3xl mx-auto mt-8 mb-20 px-4 md:px-0">
      
      <div className="flex items-center justify-between mb-6 pb-4 border-b border-orange-200">
        <h2 className="text-3xl font-extrabold text-gray-900 tracking-tight flex items-center gap-3">
          <span className="text-orange-500"></span> Biletlerim
        </h2>
        <span className="bg-orange-100 text-orange-600 px-4 py-1.5 rounded-full text-sm font-bold shadow-sm">
          {tickets.length} Toplam Bilet
        </span>
      </div>

      <div className="flex gap-4 mb-6 bg-gray-50 p-1.5 rounded-xl border border-gray-100 w-full sm:w-auto overflow-x-auto">
        <button
          onClick={() => setActiveTab('upcoming')}
          className={`flex-1 sm:flex-none px-6 py-2.5 rounded-lg text-sm font-extrabold transition-all duration-300 ${
            activeTab === 'upcoming' 
              ? 'bg-white text-orange-600 shadow-sm border border-gray-200/50' 
              : 'text-gray-500 hover:text-gray-800'
          }`}
        >
          Yaklaşan Etkinlikler ({upcomingTickets.length})
        </button>
        <button
          onClick={() => setActiveTab('past')}
          className={`flex-1 sm:flex-none px-6 py-2.5 rounded-lg text-sm font-extrabold transition-all duration-300 ${
            activeTab === 'past' 
              ? 'bg-white text-orange-600 shadow-sm border border-gray-200/50' 
              : 'text-gray-500 hover:text-gray-800'
          }`}
        >
          Geçmiş Etkinlikler ({pastTickets.length})
        </button>
      </div>
      
      {error && (
        <div className="bg-red-50 text-red-600 p-4 rounded-xl font-bold border border-red-200 shadow-sm mb-6 text-sm">
          {error}
        </div>
      )}

      {displayTickets.length === 0 && !error ? (
        <div className="bg-white border border-orange-100 py-16 rounded-2xl shadow-sm text-center">
          <div className="text-6xl mb-4 opacity-40"></div>
          <p className="text-gray-500 font-bold text-lg">
            {activeTab === 'upcoming' ? "Yaklaşan biletiniz bulunmuyor." : "Geçmiş biletiniz bulunmuyor."}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {displayTickets.map((ticket) => (
            <div key={ticket.id} className="bg-white border border-orange-100 rounded-xl flex flex-col sm:flex-row shadow-md shadow-orange-900/5 overflow-hidden hover:-translate-y-0.5 transition-transform duration-300">
              
              <div className={`w-full sm:w-2 h-2 sm:h-auto ${activeTab === 'past' ? 'bg-gray-300' : 'bg-gradient-to-b from-orange-500 to-amber-500'}`}></div>
              
              <div className="flex-grow p-5 flex flex-col justify-center">
                <div className="flex justify-between items-start mb-2">
                  <h3 className={`text-lg font-extrabold line-clamp-1 ${activeTab === 'past' ? 'text-gray-500' : 'text-gray-900'}`}>
                    {ticket.event.title}
                  </h3>
                  <span className={`font-mono text-sm font-bold px-2 py-0.5 rounded border shrink-0 ml-3 ${activeTab === 'past' ? 'text-gray-500 bg-gray-50 border-gray-200' : 'text-orange-600 bg-orange-50 border-orange-100'}`}>
                    #{ticket.id}
                  </span>
                </div>
                
                <div className={`flex flex-wrap gap-x-4 gap-y-2 text-xs font-bold mt-2 ${activeTab === 'past' ? 'text-gray-400' : 'text-gray-500'}`}>
                  <div className="flex items-center">
                    <svg className={`w-4 h-4 mr-1.5 ${activeTab === 'past' ? 'text-gray-300' : 'text-orange-400'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                    {formatTurkishDate(ticket.event.date)}
                  </div>
                  <div className="flex items-center">
                    <svg className={`w-4 h-4 mr-1.5 ${activeTab === 'past' ? 'text-gray-300' : 'text-orange-400'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                    {ticket.event.location}
                  </div>
                </div>
              </div>

              <div className={`p-4 border-t sm:border-t-0 sm:border-l border-dashed flex flex-row sm:flex-col items-center justify-center gap-6 sm:gap-4 sm:w-32 shrink-0 relative ${activeTab === 'past' ? 'bg-gray-50/50 border-gray-200' : 'bg-orange-50/50 border-orange-200'}`}>
                <div className={`hidden sm:block absolute -left-3 top-1/2 -translate-y-1/2 w-6 h-6 bg-[#FCF9F0] rounded-full border-r ${activeTab === 'past' ? 'border-gray-200' : 'border-orange-100'}`}></div>
                
                {activeTab === 'upcoming' ? (
                  <>
                    <button 
                      onClick={() => setSelectedQR(ticket)}
                      className="flex flex-col items-center gap-1.5 text-gray-500 hover:text-orange-600 transition-colors group"
                    >
                      <svg className="w-7 h-7 group-hover:scale-110 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M3 4a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H4a1 1 0 01-1-1V4zm14 0a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1V4zM3 14a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H4a1 1 0 01-1-1v-4zm14 0h5m-5 4h5m-5-9v2m5-2v2" />
                      </svg>
                      <span className="text-[10px] font-extrabold uppercase tracking-widest">QR Göster</span>
                    </button>

                    <button 
                      onClick={() => setTransferTicket(ticket)}
                      className="flex flex-col items-center gap-1.5 text-gray-500 hover:text-blue-600 transition-colors group"
                    >
                      <svg className="w-7 h-7 group-hover:scale-110 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                      </svg>
                      <span className="text-[10px] font-extrabold uppercase tracking-widest">Transfer Et</span>
                    </button>

                    <button 
                      onClick={() => window.open(`${backendUrl}/api/events/${ticket.event.id}/calendar`, '_blank')}
                      className="flex flex-col items-center gap-1.5 text-gray-500 hover:text-emerald-500 transition-colors group"
                    >
                      <svg className="w-7 h-7 group-hover:scale-110 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                      <span className="text-[10px] font-extrabold uppercase tracking-widest">TAKVİME EKLE</span>
                    </button>
                  </>
                ) : (
                  <button 
                    onClick={() => setReviewTicket(ticket)}
                    className="flex flex-col items-center gap-1.5 text-gray-500 hover:text-amber-500 transition-colors group"
                  >
                    <svg className="w-8 h-8 group-hover:scale-110 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                    </svg>
                    <span className="text-[10px] font-extrabold uppercase tracking-widest">Değerlendir</span>
                  </button>
                )}

              </div>
            </div>
          ))}
        </div>
      )}

      {selectedQR && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/60 backdrop-blur-sm transition-opacity">
          <div className="bg-white rounded-3xl p-8 max-w-sm w-full text-center relative shadow-2xl animate-fade-in-up">
            <button onClick={() => setSelectedQR(null)} className="absolute top-4 right-4 p-2 text-gray-400 hover:text-gray-800 hover:bg-gray-100 rounded-full transition-colors">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" /></svg>
            </button>
            <h3 className="text-xl font-extrabold text-gray-900 mb-2 mt-2">{selectedQR.event.title}</h3>
            <p className="text-sm font-bold text-gray-500 mb-8">Bilet No: <span className="text-orange-500">#{selectedQR.id}</span></p>
            <div className="bg-white p-4 rounded-2xl inline-block border-2 border-gray-100 shadow-sm">
              <img src={`https://api.qrserver.com/v1/create-qr-code/?size=200x200&color=000000&data=TKT_${selectedQR.id}`} alt="QR Code" className="w-48 h-48 mix-blend-multiply" />
            </div>
            <p className="text-xs font-bold text-gray-400 mt-8 uppercase tracking-widest">GİRİŞTE BU KODU OKUTUNUZ!</p>
          </div>
        </div>
      )}

      {transferTicket && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/60 backdrop-blur-sm transition-opacity">
          <div className="bg-white rounded-3xl p-8 max-w-sm w-full relative shadow-2xl animate-fade-in-up">
            <button onClick={() => setTransferTicket(null)} className="absolute top-4 right-4 p-2 text-gray-400 hover:text-gray-800 hover:bg-gray-100 rounded-full transition-colors">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" /></svg>
            </button>
            <div className="text-center mb-6 mt-2">
              <div className="w-16 h-16 bg-orange-50 text-orange-500 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </div>
              <h3 className="text-xl font-extrabold text-gray-900">Bilet Transferi</h3>
              <p className="text-xs font-bold text-gray-500 mt-2 bg-gray-50 p-2 rounded-lg inline-block border border-gray-100">
                {transferTicket.event.title} <br/> <span className="text-orange-500 font-mono">#{transferTicket.id}</span>
              </p>
            </div>
            <form onSubmit={handleTransferSubmit} className="space-y-5">
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2">Alıcının E-posta Adresi</label>
                <input 
                  type="email" 
                  required 
                  value={targetEmail}
                  onChange={(e) => setTargetEmail(e.target.value)}
                  className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-orange-400 focus:bg-white transition-all text-gray-800"
                  placeholder="arkadasin@mail.com"
                />
              </div>
              <button type="submit" disabled={isTransferring} className={`w-full text-white font-extrabold py-3.5 rounded-xl shadow-md transition-all duration-300 ${isTransferring ? 'bg-gray-400 cursor-not-allowed' : 'bg-gradient-to-r from-orange-500 to-amber-500 hover:shadow-lg hover:-translate-y-0.5 hover:from-orange-600 hover:to-amber-600'}`}>
                {isTransferring ? 'Transfer Ediliyor...' : 'Bileti Gönder'}
              </button>
            </form>
          </div>
        </div>
      )}

      {reviewTicket && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/60 backdrop-blur-sm transition-opacity">
          <div className="bg-white rounded-3xl p-8 max-w-sm w-full relative shadow-2xl animate-fade-in-up">
            <button 
              onClick={() => { setReviewTicket(null); setRating(0); setComment(''); }} 
              className="absolute top-4 right-4 p-2 text-gray-400 hover:text-gray-800 hover:bg-gray-100 rounded-full transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" /></svg>
            </button>
            
            <div className="text-center mb-6 mt-2">
              <div className="w-16 h-16 bg-amber-50 text-amber-500 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                </svg>
              </div>
              <h3 className="text-xl font-extrabold text-gray-900">Etkinliği Değerlendir</h3>
              <p className="text-sm font-bold text-gray-500 mt-2 line-clamp-1">{reviewTicket.event.title}</p>
            </div>

            <form onSubmit={handleReviewSubmit} className="space-y-5">
              
              <div className="flex justify-center gap-2 mb-4">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    onClick={() => setRating(star)}
                    className="focus:outline-none transition-transform hover:scale-110"
                  >
                    <svg 
                      className={`w-10 h-10 ${star <= rating ? 'text-amber-400' : 'text-gray-200'}`} 
                      fill="currentColor" 
                      viewBox="0 0 20 20"
                    >
                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                    </svg>
                  </button>
                ))}
              </div>

              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2">Yorumunuz (İsteğe Bağlı)</label>
                <textarea 
                  rows="3"
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-amber-400 focus:bg-white transition-all text-gray-800 resize-none"
                  placeholder="Deneyiminizi diğerleriyle paylaşın..."
                ></textarea>
              </div>
              
              <button 
                type="submit" 
                disabled={isSubmittingReview}
                className={`w-full text-white font-extrabold py-3.5 rounded-xl shadow-md transition-all duration-300 ${
                  isSubmittingReview ? 'bg-gray-400 cursor-not-allowed' : 'bg-gradient-to-r from-amber-400 to-orange-500 hover:shadow-lg hover:-translate-y-0.5'
                }`}
              >
                {isSubmittingReview ? 'Gönderiliyor...' : 'Değerlendirmeyi Gönder'}
              </button>
            </form>
          </div>
        </div>
      )}

    </div>
  );
}

export default MyTickets;
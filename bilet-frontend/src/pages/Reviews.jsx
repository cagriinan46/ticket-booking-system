import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

function Reviews() {
  const backendUrl = import.meta.env.VITE_API_URL;
  const navigate = useNavigate();
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/login');
      return;
    }

    fetch(`${backendUrl}/api/events/my-reviews`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
      .then(res => {
        if (!res.ok) throw new Error("Değerlendirmeler çekilirken bir hata oluştu.");
        return res.json();
      })
      .then(data => {
        setReviews(data);
        setLoading(false);
      })
      .catch(err => {
        toast.error(err.message);
        setLoading(false);
      });
  }, [navigate]);

  const renderStars = (rating) => {
    return (
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <svg 
            key={star} 
            className={`w-5 h-5 ${star <= rating ? 'text-amber-400' : 'text-gray-200'}`} 
            fill="currentColor" 
            viewBox="0 0 20 20"
          >
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
          </svg>
        ))}
      </div>
    );
  };

  return (
    <div className="max-w-4xl mx-auto mt-8 mb-20 px-4 md:px-0">
      
      <div className="flex items-center justify-between mb-8 pb-4 border-b border-amber-200">
        <h2 className="text-3xl font-extrabold text-gray-900 tracking-tight flex items-center gap-3">
          Değerlendirmelerim
        </h2>
        <span className="bg-amber-50 text-amber-600 px-4 py-1.5 rounded-full text-sm font-bold border border-amber-100">
          {reviews.length} Değerlendirme
        </span>
      </div>

      {loading && <p className="text-center text-amber-500 font-bold animate-pulse py-10">Değerlendirmeleriniz yükleniyor...</p>}

      {!loading && reviews.length === 0 && (
        <div className="bg-white border border-gray-100 py-20 rounded-3xl shadow-sm text-center">
          <h3 className="text-xl font-extrabold text-gray-800 mb-2">Henüz hiç değerlendirme yapmadınız.</h3>
          <p className="text-gray-500 font-medium mb-6">Gittiğiniz etkinliklere yıldız vererek diğer kullanıcılara yol gösterebilirsiniz.</p>
          <Link to="/" className="bg-amber-50 text-amber-600 px-6 py-3 rounded-xl font-bold hover:bg-amber-100 transition-colors">
            Etkinlikleri Keşfet
          </Link>
        </div>
      )}

      <div className="space-y-6">
        {!loading && reviews.map((review) => (
          <div key={review.id} className="bg-white border border-gray-100 p-6 rounded-2xl shadow-sm hover:shadow-md transition-shadow relative overflow-hidden group">
            
            <div className="absolute left-0 top-0 bottom-0 w-1.5 bg-gradient-to-b from-amber-400 to-yellow-300"></div>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-between items-start">
              <div className="flex-grow">
                <Link to={`/event/${review.event_id}`} className="inline-block text-lg font-extrabold text-gray-900 hover:text-amber-600 transition-colors mb-2">
                  {review.event?.title || `Etkinlik #${review.event_id}`}
                </Link>
                
                {renderStars(review.rating)}
                
                {review.comment ? (
                  <p className="text-gray-600 mt-3 font-medium leading-relaxed bg-gray-50 p-4 rounded-xl border border-gray-100">
                    "{review.comment}"
                  </p>
                ) : (
                  <p className="text-gray-400 mt-3 italic text-sm">Yazılı bir yorum bırakılmamış.</p>
                )}
              </div>
            </div>

          </div>
        ))}
      </div>

    </div>
  );
}

export default Reviews;
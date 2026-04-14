import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

function Profile() {
  const [tickets, setTickets] = useState([]);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem('token'); 

    if (!token) {
      setError("Biletlerinizi görmek için lütfen giriş yapın.");
      return;
    }

    fetch('http://ticket-app-lb-1559682675.eu-central-1.elb.amazonaws.com/api/events/my-tickets', {
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
  }, [navigate]);

  return (
    <div className="mt-4">
      <h2 className="text-lg font-bold mb-4 text-gray-800 border-b border-gray-300 pb-2">Kayıtlı Biletlerim</h2>
      
      {error && <p className="text-red-500 mb-4">{error}</p>}

      {tickets.length === 0 && !error ? (
        <div className="bg-gray-50 border border-gray-200 text-center py-10 text-gray-500 rounded">
          Henüz hiç bilet almadınız.
        </div>
      ) : (
        <div className="space-y-4">
          {tickets.map((ticket) => (
            <div key={ticket.id} className="bg-white border border-gray-300 rounded flex flex-col md:flex-row p-6">
              <div className="flex-grow flex flex-col justify-center">
                <h3 className="text-xl font-bold text-gray-900 mb-1">{ticket.event.title}</h3>
                <p className="text-gray-600 text-sm mb-4">{ticket.event.location} | {ticket.event.date}</p>
                <p className="text-sm text-gray-500">
                  Bilet No: <span className="font-mono bg-gray-100 px-1 border border-gray-200">#{ticket.id}</span>
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Profile;
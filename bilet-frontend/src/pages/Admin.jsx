import React, { useState } from 'react';
import toast from 'react-hot-toast';

function Admin() {
  const [title, setTitle] = useState('');
  const [date, setDate] = useState('');
  const [location, setLocation] = useState('');
  const [price, setPrice] = useState('');
  const [description, setDescription] = useState('');

  const handleAddEvent = async (e) => {
    e.preventDefault();
    const token = localStorage.getItem('token');

    if (!token || localStorage.getItem('isAdmin') !== 'true') {
      toast.error('Bu işlemi yapmaya yetkiniz yok!');
      return;
    }

    try {
      const response = await fetch('http://ticket-app-lb-1559682675.eu-central-1.elb.amazonaws.com/api/events/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          title: title,
          date: date,
          location: location,
          price: price,
          description: description,
          capacity: 500
        })
      });

      if (!response.ok) throw new Error('Etkinlik eklenirken bir hata oluştu.');

      toast.success('Etkinlik başarıyla eklendi! Ana sayfada görebilirsin.');
      
      setTitle(''); setDate(''); setLocation(''); setPrice(''); setDescription('');
      
    } catch (error) {
      toast.error(error.message);
    }
  };

  return (
    <div className="max-w-2xl mx-auto mt-8">
      <div className="bg-white p-8 rounded border border-gray-300 shadow-sm">
        <h2 className="text-2xl font-bold mb-6 text-gray-800 border-b border-gray-200 pb-2">Yönetim Paneli - Etkinlik Ekle</h2>
        
        <form onSubmit={handleAddEvent} className="space-y-4">
          <div>
            <label className="block text-sm font-bold text-gray-700 mb-1">Etkinlik Adı</label>
            <input type="text" required value={title} onChange={e => setTitle(e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"/>
          </div>
          
          <div className="flex gap-4">
            <div className="w-1/2">
              <label className="block text-sm font-bold text-gray-700 mb-1">Tarih</label>
              <input type="text" required value={date} onChange={e => setDate(e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"/>
            </div>
            <div className="w-1/2">
              <label className="block text-sm font-bold text-gray-700 mb-1">Mekan</label>
              <input type="text" required value={location} onChange={e => setLocation(e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"/>
            </div>
          </div>

          <div>
            <label className="block text-sm font-bold text-gray-700 mb-1">Fiyat (TL)</label>
            <input type="text" required value={price} onChange={e => setPrice(e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"/>
          </div>

          <div>
            <label className="block text-sm font-bold text-gray-700 mb-1">Açıklama</label>
            <textarea required value={description} onChange={e => setDescription(e.target.value)} rows="4" className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"></textarea>
          </div>

          <button type="submit" className="w-full bg-red-600 text-white font-bold py-3 rounded hover:bg-red-700 mt-6 shadow-sm">
            Sisteme Ekle
          </button>
        </form>
      </div>
    </div>
  );
}

export default Admin;
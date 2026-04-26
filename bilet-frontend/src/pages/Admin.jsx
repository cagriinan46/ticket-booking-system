import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';

function Admin() {
  const backendUrl = import.meta.env.VITE_API_URL;
  const [title, setTitle] = useState('');
  const [date, setDate] = useState('');
  const [location, setLocation] = useState('');
  const [price, setPrice] = useState('');
  const [description, setDescription] = useState('');
  const [image, setImage] = useState('');
  const [events, setEvents] = useState([]);
  const [city, setCity] = useState('İstanbul');
  const [category, setCategory] = useState('Konser');

  const cities = [
    "İstanbul", "Ankara", "İzmir", "Adana", "Adıyaman", "Afyonkarahisar", "Ağrı", "Aksaray", "Amasya", "Antalya", "Ardahan", "Artvin", "Aydın", "Balıkesir", "Bartın", "Batman", "Bayburt", "Bilecik", "Bingöl", "Bitlis", "Bolu", "Burdur", "Bursa", "Çanakkale", "Çankırı", "Çorum", "Denizli", "Diyarbakır", "Düzce", "Edirne", "Elazığ", "Erzincan", "Erzurum", "Eskişehir", "Gaziantep", "Giresun", "Gümüşhane", "Hakkari", "Hatay", "Iğdır", "Isparta", "Kahramanmaraş", "Karabük", "Karaman", "Kars", "Kastamonu", "Kayseri", "Kırıkkale", "Kırklareli", "Kırşehir", "Kilis", "Kocaeli", "Konya", "Kütahya", "Malatya", "Manisa", "Mardin", "Mersin", "Muğla", "Muş", "Nevşehir", "Niğde", "Ordu", "Osmaniye", "Rize", "Sakarya", "Samsun", "Siirt", "Sinop", "Sivas", "Şanlıurfa", "Şırnak", "Tekirdağ", "Tokat", "Trabzon", "Tunceli", "Uşak", "Van", "Yalova", "Yozgat", "Zonguldak"
  ];

  const categories = ['Konser', 'Tiyatro', 'Festival', 'Stand-up', 'Spor'];

  useEffect(() => {
    fetchEvents();
  }, []);

  const fetchEvents = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/events`);
      if (response.ok) {
        const data = await response.json();
        setEvents(data);
      }
    } catch (error) {
      toast.error('Etkinlikler yüklenirken hata oluştu.');
    }
  };

  const handleAddEvent = async (e) => {
    e.preventDefault();
    const token = localStorage.getItem('token');

    if (!token || localStorage.getItem('isAdmin') !== 'true') {
      toast.error('Bu işlemi yapmaya yetkiniz yok!');
      return;
    }

    try {
      const response = await fetch(`${backendUrl}/api/events`, {
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
          image: image,
          city: city,
          category: category,
          capacity: 500
        })
      });

      if (!response.ok) throw new Error('Etkinlik eklenirken bir hata oluştu.');

      toast.success('Etkinlik başarıyla eklendi! Ana sayfada görebilirsin.');
      
      setTitle(''); 
      setDate(''); 
      setLocation(''); 
      setPrice(''); 
      setDescription('');
      setImage('');
      setCity('İstanbul');
      setCategory('Konser');
      
      fetchEvents();
      
    } catch (error) {
      toast.error(error.message);
    }
  };

  const handleDelete = async (eventId) => {
    if (!window.confirm("Bu etkinliği silmek istediğinize emin misiniz?")) return;

    const token = localStorage.getItem('token');
    
    try {
      const response = await fetch(`${backendUrl}/api/events/${eventId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        toast.success("Etkinlik başarıyla silindi!");
        setEvents(events.filter(event => event.id !== eventId));
      } else {
        toast.error("Silme işlemi başarısız oldu.");
      }
    } catch (error) {
      toast.error(error.message);
    }
  };

  return (
    <div className="max-w-2xl mx-auto mt-8 space-y-8 mb-12">
      <div className="bg-white p-8 rounded border border-gray-300 shadow-sm">
        <h2 className="text-2xl font-bold mb-6 text-gray-800 border-b border-gray-200 pb-2">Etkinlik Ekle</h2>
        
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

          <div className="flex gap-4">
            <div className="w-1/2">
              <label className="block text-sm font-bold text-gray-700 mb-1">Şehir</label>
              <select value={city} onChange={e => setCity(e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500 bg-white">
                {cities.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div className="w-1/2">
              <label className="block text-sm font-bold text-gray-700 mb-1">Kategori</label>
              <select value={category} onChange={e => setCategory(e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500 bg-white">
                {categories.map(cat => <option key={cat} value={cat}>{cat}</option>)}
              </select>
            </div>
          </div>

          <div className="flex gap-4">
            <div className="w-1/3">
              <label className="block text-sm font-bold text-gray-700 mb-1">Fiyat (TL)</label>
              <input type="text" required value={price} onChange={e => setPrice(e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"/>
            </div>
            <div className="w-2/3">
              <label className="block text-sm font-bold text-gray-700 mb-1">Resim Linki (URL)</label>
              <input type="url" required value={image} onChange={e => setImage(e.target.value)} placeholder="Örn: https://resim-linki.com/foto.jpg" className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"/>
            </div>
          </div>

          <div>
            <label className="block text-sm font-bold text-gray-700 mb-1">Açıklama</label>
            <textarea required value={description} onChange={e => setDescription(e.target.value)} rows="4" className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"></textarea>
          </div>

          <button type="submit" className="w-full bg-red-600 text-white font-bold py-3 rounded hover:bg-red-700 mt-6 shadow-sm transition-colors">
            Sisteme Ekle
          </button>
        </form>
      </div>

      <div className="bg-white p-8 rounded border border-gray-300 shadow-sm">
        <h2 className="text-2xl font-bold mb-6 text-gray-800 border-b border-gray-200 pb-2">Mevcut Etkinlikler</h2>
        {events.length === 0 ? (
          <p className="text-gray-500 font-medium">Sistemde kayıtlı etkinlik bulunmuyor.</p>
        ) : (
          <ul className="divide-y divide-gray-200 border border-gray-200 rounded-md">
            {events.map((event) => (
              <li key={event.id} className="p-4 flex justify-between items-center hover:bg-gray-50 transition-colors">
                <div>
                  <p className="font-bold text-gray-800">{event.title}</p>
                  <p className="text-sm text-gray-600 mt-1">{event.city} | {event.category} | {event.date} | <span className="font-semibold text-blue-600">{event.price} TL</span></p>
                </div>
                <button 
                  onClick={() => handleDelete(event.id)}
                  className="bg-white text-red-600 border border-red-200 hover:bg-red-600 hover:text-white hover:border-red-600 px-4 py-2 rounded font-bold transition-colors text-sm shadow-sm"
                >
                  Sil
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

export default Admin;
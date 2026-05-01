import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';

function Admin() {
  const backendUrl = import.meta.env.VITE_API_URL;
  const [title, setTitle] = useState('');
  const [date, setDate] = useState('');
  const [time, setTime] = useState('');
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
          time: time,
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

      toast.success('Etkinlik başarıyla eklendi!');
      
      setTitle(''); setDate(''); setTime(''); setLocation(''); setPrice(''); setDescription(''); setImage('');
      
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
        toast.success("Etkinlik silindi!");
        setEvents(events.filter(event => event.id !== eventId));
      } else {
        toast.error("Silme işlemi başarısız oldu.");
      }
    } catch (error) {
      toast.error(error.message);
    }
  };

  return (
    <div className="max-w-4xl mx-auto mt-8 space-y-12 mb-20 px-4 md:px-0">
      
      <div className="flex items-center justify-between">
        <h1 className="text-4xl font-extrabold text-gray-900 tracking-tight flex items-center gap-3">
          <span className="text-orange-500"></span> Yönetim Paneli
        </h1>
        <div className="flex gap-3">
          <span className="bg-orange-100 text-orange-700 px-5 py-2 rounded-full font-bold text-sm shadow-sm">
            {events.length} Toplam Etkinlik
          </span>
        </div>
      </div>

      <div className="bg-white p-8 md:p-10 rounded-3xl border border-orange-100 shadow-xl shadow-orange-900/5 relative overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-1.5 bg-gradient-to-r from-orange-500 to-amber-500"></div>
        <h2 className="text-3xl font-extrabold mb-8 text-gray-900 tracking-tight">Yeni Etkinlik Ekle</h2>
        
        <form onSubmit={handleAddEvent} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="md:col-span-2">
              <label className="block text-sm font-bold text-gray-700 mb-2">Etkinlik Adı</label>
              <input type="text" required value={title} onChange={e => setTitle(e.target.value)} className="w-full px-5 py-3.5 bg-gray-50 border border-gray-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-orange-400 focus:bg-white transition-all text-gray-800"/>
            </div>
            
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-2">Tarih</label>
              <input type="text" required value={date} onChange={e => setDate(e.target.value)} className="w-full px-5 py-3.5 bg-gray-50 border border-gray-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-orange-400 focus:bg-white transition-all text-gray-800" placeholder='YYYY-AA-GG'/>
            </div>

            <div>
              <label className="block text-sm font-bold text-gray-700 mb-2">Saat</label>
              <input type="text" required value={time} onChange={e => setTime(e.target.value)} className="w-full px-5 py-3.5 bg-gray-50 border border-gray-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-orange-400 focus:bg-white transition-all text-gray-800" placeholder='14:00' maxLength="5"/>
            </div>

            <div>
              <label className="block text-sm font-bold text-gray-700 mb-2">Mekan</label>
              <input type="text" required value={location} onChange={e => setLocation(e.target.value)} className="w-full px-5 py-3.5 bg-gray-50 border border-gray-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-orange-400 focus:bg-white transition-all text-gray-800"/>
            </div>

            <div>
              <label className="block text-sm font-bold text-gray-700 mb-2">Şehir</label>
              <select value={city} onChange={e => setCity(e.target.value)} className="w-full px-5 py-3.5 bg-gray-50 border border-gray-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-orange-400 focus:bg-white transition-all text-gray-800 cursor-pointer">
                {cities.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-2">Kategori</label>
              <select value={category} onChange={e => setCategory(e.target.value)} className="w-full px-5 py-3.5 bg-gray-50 border border-gray-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-orange-400 focus:bg-white transition-all text-gray-800 cursor-pointer">
                {categories.map(cat => <option key={cat} value={cat}>{cat}</option>)}
              </select>
            </div>

            <div>
              <label className="block text-sm font-bold text-gray-700 mb-2">Bilet Fiyatı (TL)</label>
              <input type="number" required value={price} onChange={e => setPrice(e.target.value)} className="w-full px-5 py-3.5 bg-gray-50 border border-gray-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-orange-400 focus:bg-white transition-all text-gray-800"/>
            </div>
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-2">Görsel URL</label>
              <input type="url" required value={image} onChange={e => setImage(e.target.value)} className="w-full px-5 py-3.5 bg-gray-50 border border-gray-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-orange-400 focus:bg-white transition-all text-gray-800"/>
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-bold text-gray-700 mb-2">Etkinlik Açıklaması</label>
              <textarea required value={description} onChange={e => setDescription(e.target.value)} rows="5" className="w-full px-5 py-4 bg-gray-50 border border-gray-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-orange-400 focus:bg-white transition-all text-gray-800 leading-relaxed"></textarea>
            </div>
          </div>

          <div className="flex justify-end pt-4">
            <button type="submit" className="flex items-center gap-2.5 bg-gradient-to-r from-orange-500 to-amber-500 text-white font-extrabold px-10 py-4 rounded-2xl shadow-md hover:shadow-lg hover:-translate-y-0.5 hover:from-orange-600 hover:to-amber-600 transition-all duration-300 text-lg">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M12 4v16m8-8H4" /></svg>
              Sisteme Kaydet
            </button>
          </div>
        </form>
      </div>

      <div className="bg-white p-8 md:p-10 rounded-3xl border border-orange-100 shadow-xl shadow-orange-900/5 relative overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-1.5 bg-gradient-to-r from-amber-500 to-yellow-400"></div>
        <h2 className="text-3xl font-extrabold mb-8 text-gray-900 tracking-tight">Etkinlikleri Yönet</h2>
        
        {events.length === 0 ? (
          <div className="text-center py-16 bg-orange-50 rounded-2xl border border-orange-100">
            <div className="text-6xl mb-4 opacity-50"></div>
            <p className="text-orange-900 font-bold text-lg">Henüz hiç etkinlik eklenmemiş.</p>
          </div>
        ) : (
          <ul className="divide-y divide-orange-100 border border-orange-100 rounded-2xl overflow-hidden shadow-inner">
            {events.map((event) => (
              <li key={event.id} className="p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-orange-50/50 transition-colors group cursor-default">
                <div className="flex flex-col gap-1.5">
                  <p className="text-xl font-extrabold text-gray-900 group-hover:text-orange-600 transition-colors line-clamp-1">{event.title}</p>
                  <div className="flex flex-wrap items-center gap-2 text-xs font-bold uppercase tracking-wider text-gray-600 mt-1">
                    <span className="bg-orange-100 text-orange-700 px-2.5 py-1 rounded-full font-black text-[11px]">
                      {event.category}
                    </span>
                    <span className="text-gray-400">•</span>
                    <span className="truncate">{event.city}</span>
                    <span className="text-gray-400">•</span>
                    <span className="truncate">{event.date}</span>
                    <span className="text-gray-400">•</span>
                    <span className="truncate font-medium">{event.time}</span>
                    <span className="text-gray-400">•</span>
                    <span className="font-extrabold text-amber-600 text-sm normal-case">{event.price} TL</span>
                  </div>
                </div>
                <div className="shrink-0 flex sm:justify-end pt-3 sm:pt-0">
                  <button 
                    onClick={() => handleDelete(event.id)}
                    className="flex items-center gap-2 bg-rose-50 text-rose-600 border border-rose-100 hover:bg-rose-600 hover:text-white hover:border-rose-600 px-5 py-2.5 rounded-xl font-bold transition-all text-sm shadow-sm"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                    Sil
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

export default Admin;
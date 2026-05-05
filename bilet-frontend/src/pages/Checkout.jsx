import React, { useState } from 'react';
import { useLocation, Navigate, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

function Checkout() {
  const backendUrl = import.meta.env.VITE_API_URL;
  const navigate = useNavigate();
  const location = useLocation();
  const event = location.state?.event;

  const [cardHolderName, setCardHolderName] = useState('');
  const [cardNumber, setCardNumber] = useState('');
  const [expireDate, setExpireDate] = useState('');
  const [cvc, setCvc] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);

  const formatTurkishDate = (dateString) => {
    const date = new Date(dateString);
    if (isNaN(date)) return dateString; 
    
    const day = date.getDate();
    const month = date.toLocaleDateString('tr-TR', { month: 'long' });
    const weekday = date.toLocaleDateString('tr-TR', { weekday: 'long' });

    return `${day} ${month}, ${weekday}`;
  };

  if (!event) return <Navigate to="/" />;

  const handleNameChange = (e) => {
    let value = e.target.value.replace(/[^a-zA-ZçÇğĞıİöÖşŞüÜ\s]/g, '');
    setCardHolderName(value.toLocaleUpperCase('tr-TR'));
  };

  const handleCardNumberChange = (e) => {
    let value = e.target.value.replace(/\D/g, ''); 
    if (value.length > 16) value = value.slice(0, 16);
    const formattedValue = value.replace(/(\d{4})(?=\d)/g, '$1 ').trim();
    setCardNumber(formattedValue);
  };

  const handleExpireDateChange = (e) => {
    let value = e.target.value.replace(/\D/g, ''); 
    if (value.length > 4) value = value.slice(0, 4);
    if (value.length > 2) {
      value = `${value.slice(0, 2)}/${value.slice(2)}`;
    }
    setExpireDate(value);
  };

  const handleCvcChange = (e) => {
    let value = e.target.value.replace(/\D/g, '');
    if (value.length > 3) value = value.slice(0, 3);
    setCvc(value);
  };

  const handlePayment = async (e) => {
    e.preventDefault();
    setIsProcessing(true);
    const token = localStorage.getItem('token');
    
    const [expireMonth, expireYear] = expireDate.split('/');

    try {
      const response = await fetch(`${backendUrl}/api/events/buy/${event.id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          cardHolderName,
          cardNumber: cardNumber.replace(/\s/g, ''), 
          expireMonth,
          expireYear: expireYear?.length === 2 ? `20${expireYear}` : expireYear,
          cvc
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Ödeme reddedildi.');
      }

      toast.success('Ödeme Başarılı! Biletlerinize yönlendiriliyorsunuz...');
      setTimeout(() => navigate('/my-tickets'), 2000);
      
    } catch (error) {
      toast.error(error.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const basePrice = parseInt(event.price) || 0; 
  const serviceFee = 25;
  const totalPrice = basePrice + serviceFee;

  return (
    <div className="max-w-5xl mx-auto mt-8 mb-20 px-4 md:px-0">
      <div className="flex items-center justify-between mb-8 pb-4 border-b border-orange-200">
        <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight flex items-center gap-3">
          <span className="text-orange-500"></span> Güvenli Ödeme
        </h1>
      </div>

      <div className="flex flex-col lg:flex-row gap-8">
        <div className="lg:w-2/3 bg-white p-8 md:p-10 rounded-3xl border border-orange-100 shadow-xl shadow-orange-900/5 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-1.5 bg-gradient-to-r from-orange-500 to-amber-500"></div>
          
          <div className="flex justify-between items-center mb-8">
            <h2 className="text-2xl font-extrabold text-gray-900 tracking-tight">Kart Bilgileri</h2>
            <span className="bg-orange-50 text-orange-600 border border-orange-100 text-[10px] font-black uppercase tracking-widest px-3 py-1.5 rounded-full shadow-sm">
              IYZICO
            </span>
          </div>
          
          <form onSubmit={handlePayment} className="space-y-6">
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-2">Kart Üzerindeki İsim</label>
              <input type="text" required value={cardHolderName} onChange={handleNameChange} className="w-full px-5 py-3.5 bg-gray-50 border border-gray-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-orange-400 focus:bg-white transition-all text-gray-800 font-bold tracking-wide" placeholder="ÖRN: ÇAĞRI İNAN ÇAMLI"/>
            </div>
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-2">Kart Numarası</label>
              <input type="text" required value={cardNumber} onChange={handleCardNumberChange} className="w-full px-5 py-3.5 bg-gray-50 border border-gray-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-orange-400 focus:bg-white transition-all text-gray-800 font-mono tracking-widest" placeholder="5400 3600 0000 0003"/>
            </div>
            
            <div className="flex gap-6">
              <div className="w-1/2">
                <label className="block text-sm font-bold text-gray-700 mb-2">Son Kullanma (AA/YY)</label>
                <input type="text" required value={expireDate} onChange={handleExpireDateChange} className="w-full px-5 py-3.5 bg-gray-50 border border-gray-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-orange-400 focus:bg-white transition-all text-gray-800 font-mono text-center" placeholder="12/30" />
              </div>
              <div className="w-1/2">
                <label className="block text-sm font-bold text-gray-700 mb-2">CVC/CVV</label>
                <input type="text" required value={cvc} onChange={handleCvcChange} className="w-full px-5 py-3.5 bg-gray-50 border border-gray-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-orange-400 focus:bg-white transition-all text-gray-800 font-mono text-center tracking-widest" placeholder="123" />
              </div>
            </div>
            
            <button 
              type="submit" 
              disabled={isProcessing || cardNumber.length < 19 || expireDate.length < 5 || cvc.length < 3 || cardHolderName.length < 3}
              className={`w-full text-white font-extrabold py-4 rounded-2xl mt-8 shadow-md transition-all duration-300 text-lg ${
                isProcessing || cardNumber.length < 19 || expireDate.length < 5 || cvc.length < 3 || cardHolderName.length < 3
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed' 
                  : 'bg-gradient-to-r from-orange-500 to-amber-500 hover:shadow-lg hover:-translate-y-0.5 hover:from-orange-600 hover:to-amber-600'
              }`}
            >
              {isProcessing ? 'Onay Bekleniyor...' : `${totalPrice} TL Ödemeyi Onayla`}
            </button>
          </form>
        </div>

        <div className="lg:w-1/3">
          <div className="bg-orange-50/50 p-8 rounded-3xl border border-orange-100 shadow-sm sticky top-6">
            <h2 className="text-xl font-extrabold mb-6 text-gray-900 tracking-tight">Sipariş Özeti</h2>
            
            <div className="mb-6 pb-6 border-b border-orange-200 border-dashed">
              <h3 className="font-black text-orange-600 text-xl leading-tight mb-4 drop-shadow-sm">
                {event.title}
              </h3>
              
              <p className="text-sm font-bold text-gray-500 flex items-center gap-1.5 mb-3">
                <svg className="w-4 h-4 text-orange-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                {event.location} / {event.city}
              </p>

              <p className="text-sm font-bold text-gray-500 flex items-center gap-1.5">
                <svg className="w-4 h-4 text-orange-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                {formatTurkishDate(event.date)}
                {event.time && ` - ${event.time}`}
              </p>
            </div>
            
            <div className="space-y-4 text-sm font-bold text-gray-600 mb-6">
              <div className="flex justify-between items-center">
                <span>Bilet Bedeli</span>
                <span className="text-gray-900">{basePrice} TL</span>
              </div>
              <div className="flex justify-between items-center">
                <span>Hizmet Bedeli</span>
                <span className="text-gray-900">{serviceFee} TL</span>
              </div>
            </div>
            
            <div className="flex justify-between items-center font-black text-2xl text-orange-600 border-t border-orange-200 pt-6">
              <span className="text-lg text-gray-800">Toplam</span>
              <span>{totalPrice} TL</span>
            </div>
            
            <div className="mt-8 flex items-center justify-center gap-2 text-xs font-bold text-gray-400 uppercase tracking-widest">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              256-BİT SSL Şifreleme
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Checkout;
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

  if (!event) return <Navigate to="/" />;

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
          expireYear: expireYear.length === 2 ? `20${expireYear}` : expireYear,
          cvc
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Ödeme reddedildi.');
      }

      toast.success('Ödeme Alındı, Biletiniz Kesildi!');
      setTimeout(() => navigate('/profile'), 2000);
      
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
    <div className="mt-4">
      <h1 className="text-2xl font-bold mb-6 text-gray-800 border-b border-gray-300 pb-2">Güvenli Ödeme İşlemi (Iyzico Altyapısı)</h1>

      <div className="flex flex-col lg:flex-row gap-6">
        <div className="lg:w-2/3 bg-white p-6 rounded border border-gray-300 shadow-sm">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-bold text-gray-700">Kart Bilgileri</h2>
            <span className="bg-blue-100 text-blue-800 text-xs font-bold px-2 py-1 rounded">IYZICO SANDBOX</span>
          </div>
          
          <form onSubmit={handlePayment} className="space-y-4">
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-1">Kart Üzerindeki İsim</label>
              <input type="text" required value={cardHolderName} onChange={e => setCardHolderName(e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500" placeholder="Test Kullanıcısı"/>
            </div>
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-1">Kart Numarası</label>
              <input type="text" required value={cardNumber} onChange={e => setCardNumber(e.target.value)} maxLength="19" className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500" placeholder="5400 3600 0000 0003"/>
            </div>
            
            <div className="flex gap-4">
              <div className="w-1/2">
                <label className="block text-sm font-bold text-gray-700 mb-1">Son Kullanma (AA/YY)</label>
                <input type="text" required value={expireDate} onChange={e => setExpireDate(e.target.value)} maxLength="5" className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500" placeholder="12/30" />
              </div>
              <div className="w-1/2">
                <label className="block text-sm font-bold text-gray-700 mb-1">CVC/CVV</label>
                <input type="text" required value={cvc} onChange={e => setCvc(e.target.value)} maxLength="3" className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500" placeholder="123" />
              </div>
            </div>
            
            <button 
              type="submit" 
              disabled={isProcessing}
              className={`w-full text-white font-bold py-3 rounded mt-6 shadow-sm ${isProcessing ? 'bg-gray-400 cursor-not-allowed' : 'bg-green-600 hover:bg-green-700'}`}
            >
              {isProcessing ? 'Banka İle İletişim Kuruluyor...' : `${totalPrice} TL Ödemeyi Onayla`}
            </button>
          </form>
        </div>

        <div className="lg:w-1/3">
          <div className="bg-gray-50 p-6 rounded border border-gray-300">
            <h2 className="text-lg font-bold mb-4 text-gray-700">Sipariş Özeti</h2>
            <div className="mb-4 pb-4 border-b border-gray-200">
              <h3 className="font-bold text-gray-800">{event.title}</h3>
              <p className="text-sm text-gray-600">{event.date}</p>
            </div>
            <div className="space-y-2 text-sm text-gray-700 mb-4">
              <div className="flex justify-between"><span>Bilet Bedeli</span><span>{basePrice} TL</span></div>
              <div className="flex justify-between"><span>Hizmet Bedeli</span><span>{serviceFee} TL</span></div>
            </div>
            <div className="flex justify-between font-bold text-lg text-gray-900 border-t border-gray-300 pt-4">
              <span>Toplam</span>
              <span>{totalPrice} TL</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Checkout;
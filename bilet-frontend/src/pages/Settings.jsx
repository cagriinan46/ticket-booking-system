import React, { useState } from 'react';
import toast from 'react-hot-toast';
import { useNavigate } from 'react-router-dom';

function Settings() {
  const backendUrl = import.meta.env.VITE_API_URL;
  const navigate = useNavigate();
  
  const [emailNotif, setEmailNotif] = useState(true);
  
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [confirmEmail, setConfirmEmail] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDeleteAccount = async () => {
    if (!confirmEmail) {
      toast.error("Lütfen e-posta adresinizi girin.");
      return;
    }

    setIsDeleting(true);
    const token = localStorage.getItem('token');

    try {
      const response = await fetch(`${backendUrl}/api/users/delete-account`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ email: confirmEmail })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Hesap silinirken bir hata oluştu.");
      }

      toast.success("Hesabınız kalıcı olarak silindi. Hoşça kalın! 🥺", { duration: 4000 });
      
      localStorage.removeItem('token');
      localStorage.removeItem('isLoggedIn');
      setTimeout(() => {
        navigate('/');
        window.location.reload();
      }, 1500);

    } catch (error) {
      toast.error(error.message);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleToggleEmailNotif = async () => {
    const newValue = !emailNotif;
    setEmailNotif(newValue);

    const token = localStorage.getItem('token');
    try {
      const response = await fetch(`${backendUrl}/api/auth/email-notifications`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ email_notifications: newValue })
      });

      if (!response.ok) {
        setEmailNotif(!newValue);
        toast.error("Ayar güncellenemedi.");
      } else {
        toast.success(newValue ? "E-Posta bildirimleri açıldı!" : "E-Posta bildirimleri kapatıldı.");
      }
    } catch (err) {
      setEmailNotif(!newValue);
      toast.error("Bağlantı hatası.");
    }
  };

  return (
    <div className="max-w-4xl mx-auto mt-10 mb-20 px-4 md:px-0">
      <h1 className="text-4xl font-extrabold text-gray-900 tracking-tight mb-8">Ayarlar</h1>

      <div className="space-y-6">
        
        <div className="bg-white p-8 rounded-3xl border border-orange-100 shadow-lg shadow-orange-900/5 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-1.5 h-full bg-gradient-to-b from-amber-500 to-yellow-400"></div>
          <h2 className="text-xl font-bold text-gray-800 mb-6 flex items-center gap-2">
            <svg className="w-6 h-6 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" /></svg>
            Bildirimler
          </h2>
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="font-bold text-gray-700">E-Posta Bildirimleri</p>
              <p className="text-sm text-gray-500">Biletlerim ve etkinlik güncellemeleri hakkında mail al.</p>
            </div>
            <button 
              onClick={handleToggleEmailNotif}
              className={`w-14 h-7 flex items-center rounded-full p-1 transition-colors duration-300 ease-in-out ${emailNotif ? 'bg-orange-500' : 'bg-gray-300'}`}
            >
              <div className={`bg-white w-5 h-5 rounded-full shadow-md transform transition-transform duration-300 ease-in-out ${emailNotif ? 'translate-x-7' : ''}`}></div>
            </button>
          </div>
        </div>

        <div className="bg-white p-8 rounded-3xl border border-red-100 shadow-lg shadow-red-900/5 relative overflow-hidden mt-8">
          <div className="absolute top-0 left-0 w-1.5 h-full bg-red-500"></div>
          <h2 className="text-xl font-bold text-red-600 mb-2">Tehlikeli Bölge</h2>
          <p className="text-sm text-gray-500 mb-6">Hesabınızı silmek geri alınamaz bir işlemdir. Tüm biletleriniz ve favorileriniz kaybolur.</p>
          
          {!showDeleteConfirm ? (
            <button 
              onClick={() => setShowDeleteConfirm(true)}
              className="bg-red-50 text-red-600 font-bold px-6 py-3 rounded-xl border border-red-200 hover:bg-red-600 hover:text-white transition-all"
            >
              Hesabımı Sil
            </button>
          ) : (
            <div className="bg-red-50 p-6 rounded-2xl border border-red-200 animate-fade-in">
              <p className="text-red-800 font-bold mb-4">Bu işlemi geri alamayacaksınız. Onaylamak için lütfen hesabınıza ait e-posta adresini girin:</p>
              <div className="flex flex-col sm:flex-row gap-4">
                <input 
                  type="email" 
                  value={confirmEmail}
                  onChange={(e) => setConfirmEmail(e.target.value)}
                  placeholder="E-posta adresiniz..." 
                  className="flex-grow px-5 py-3 rounded-xl border border-red-300 focus:outline-none focus:ring-2 focus:ring-red-500 font-medium"
                />
                <button 
                  onClick={handleDeleteAccount}
                  disabled={isDeleting || !confirmEmail}
                  className={`px-6 py-3 rounded-xl font-bold text-white transition-all whitespace-nowrap ${isDeleting || !confirmEmail ? 'bg-red-300 cursor-not-allowed' : 'bg-red-600 hover:bg-red-700 shadow-md'}`}
                >
                  {isDeleting ? 'Siliniyor...' : 'Kalıcı Olarak Sil'}
                </button>
                <button 
                  onClick={() => {
                    setShowDeleteConfirm(false);
                    setConfirmEmail('');
                  }}
                  className="px-6 py-3 rounded-xl font-bold text-gray-600 bg-white border border-gray-300 hover:bg-gray-50 transition-all whitespace-nowrap"
                >
                  İptal
                </button>
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}

export default Settings;
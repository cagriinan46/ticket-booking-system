import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

function Profile() {
  const backendUrl = import.meta.env.VITE_API_URL;
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  
  const [userData, setUserData] = useState({
    name: '',
    email: ''
  });

  const [passwords, setPasswords] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/login');
      return;
    }

    fetch(`${backendUrl}/api/auth/me`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
      .then(res => {
        if (!res.ok) throw new Error("Kullanıcı bilgileri çekilemedi.");
        return res.json();
      })
      .then(data => {
        setUserData({
          name: data.name || '',
          email: data.email || ''
        });
        setLoading(false);
      })
      .catch(err => {
        toast.error(err.message);
        setLoading(false);
      });
  }, [navigate, backendUrl]);

  const handleProfileUpdate = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    
    const token = localStorage.getItem('token');

    try {
      const res = await fetch(`${backendUrl}/api/auth/me/profile`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ name: userData.name })
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Profil güncellenirken bir hata oluştu.");
      }

      toast.success("Profil bilgileriniz başarıyla güncellendi!");
    } catch (err) {
      toast.error(err.message);
    } finally {
      setIsSaving(false);
    }
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    if (passwords.newPassword !== passwords.confirmPassword) {
      return toast.error("Yeni şifreler birbiriyle uyuşmuyor!");
    }
    
    setIsSaving(true);
    const token = localStorage.getItem('token');
    
    try {
      const res = await fetch(`${backendUrl}/api/auth/me/password`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          current_password: passwords.currentPassword,
          new_password: passwords.newPassword
        })
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Şifre güncellenemedi.");
      }

      toast.success("Şifreniz güvenle değiştirildi! 🔒");
      setPasswords({ currentPassword: '', newPassword: '', confirmPassword: '' });
    } catch (err) {
      toast.error(err.message);
    } finally {
      setIsSaving(false);
    }
  };

  if (loading) {
    return <div className="py-20 text-center text-orange-500 font-bold animate-pulse">Profiliniz yükleniyor...</div>;
  }

  return (
    <div className="max-w-4xl mx-auto mt-8 mb-20 px-4 md:px-0">
      
      <div className="flex items-center justify-between mb-8 pb-4 border-b border-orange-200">
        <h2 className="text-3xl font-extrabold text-gray-900 tracking-tight flex items-center gap-3">
          <span className="bg-orange-50 text-orange-500 p-2 rounded-xl">
            <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>
          </span> 
          Profilim
        </h2>
      </div>

      <div className="space-y-8">
        
        <div className="bg-white border border-gray-100 p-6 sm:p-8 rounded-3xl shadow-sm relative overflow-hidden">
          <div className="absolute left-0 top-0 bottom-0 w-1.5 bg-gradient-to-b from-orange-400 to-amber-300"></div>
          
          <h3 className="text-xl font-extrabold text-gray-900 mb-6 flex items-center gap-2">
            Kişisel Bilgiler
          </h3>
          
          <form onSubmit={handleProfileUpdate} className="space-y-5">
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-2">Ad Soyad</label>
              <input 
                type="text" 
                value={userData.name}
                onChange={(e) => setUserData({...userData, name: e.target.value})}
                className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-orange-400 focus:bg-white transition-all text-gray-800 font-medium"
              />
            </div>
            
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-2">E-posta Adresi</label>
              <input 
                type="email" 
                value={userData.email}
                disabled
                className="w-full px-4 py-3 bg-gray-100 border border-gray-200 rounded-xl text-gray-500 font-medium cursor-not-allowed"
                title="E-posta adresi değiştirilemez"
              />
              <p className="text-xs text-gray-400 mt-1.5 font-bold">* E-posta adresiniz hesabınıza kalıcı olarak bağlıdır.</p>
            </div>

            <div className="pt-2">
              <button 
                type="submit" 
                disabled={isSaving}
                className="bg-orange-50 text-orange-600 px-8 py-3 rounded-xl font-extrabold hover:bg-orange-100 transition-colors duration-300 w-full sm:w-auto"
              >
                {isSaving ? 'Kaydediliyor...' : 'Değişiklikleri Kaydet'}
              </button>
            </div>
          </form>
        </div>

        <div className="bg-white border border-gray-100 p-6 sm:p-8 rounded-3xl shadow-sm relative overflow-hidden">
          <div className="absolute left-0 top-0 bottom-0 w-1.5 bg-gray-200"></div>
          
          <h3 className="text-xl font-extrabold text-gray-900 mb-6 flex items-center gap-2">
            <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
            Şifre Değiştir
          </h3>
          
          <form onSubmit={handlePasswordChange} className="space-y-5">
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-2">Mevcut Şifreniz</label>
              <input 
                type="password" 
                required
                value={passwords.currentPassword}
                onChange={(e) => setPasswords({...passwords, currentPassword: e.target.value})}
                className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-400 focus:bg-white transition-all text-gray-800"
                placeholder="••••••••"
              />
            </div>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2">Yeni Şifre</label>
                <input 
                  type="password" 
                  required
                  value={passwords.newPassword}
                  onChange={(e) => setPasswords({...passwords, newPassword: e.target.value})}
                  className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-400 focus:bg-white transition-all text-gray-800"
                  placeholder="••••••••"
                />
              </div>
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2">Yeni Şifre (Tekrar)</label>
                <input 
                  type="password" 
                  required
                  value={passwords.confirmPassword}
                  onChange={(e) => setPasswords({...passwords, confirmPassword: e.target.value})}
                  className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-400 focus:bg-white transition-all text-gray-800"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <div className="pt-2">
              <button 
                type="submit" 
                disabled={isSaving}
                className="bg-gray-800 text-white px-8 py-3 rounded-xl font-extrabold hover:bg-gray-900 transition-colors duration-300 w-full sm:w-auto shadow-sm"
              >
                Şifreyi Güncelle
              </button>
            </div>
          </form>
        </div>

      </div>
    </div>
  );
}

export default Profile;
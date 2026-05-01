import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

function Login() {
  const backendUrl = import.meta.env.VITE_API_URL;
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  const handleAuth = async () => {
    if (isLogin) {
      try {
        const formData = new URLSearchParams();
        formData.append('username', email); 
        formData.append('password', password); 

        const response = await fetch(`${backendUrl}/api/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: formData.toString()
        });

        if (!response.ok) throw new Error('Bilgiler hatalı. Lütfen e-posta ve şifrenizi kontrol edin.');
        
        const data = await response.json();
        
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('isLoggedIn', 'true');
        localStorage.setItem('isAdmin', data.is_admin ? 'true' : 'false');
        
        toast.success('Başarıyla giriş yapıldı!');
        navigate('/');
      } catch (error) {
        toast.error(error.message);
      }
    } else {
        try {
            const response = await fetch(`${backendUrl}/api/auth/register`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ name: name, email: email, password: password }) 
            });

            if (!response.ok) throw new Error('Kayıt işlemi başarısız oldu.');
            
            toast.success('Kayıt başarılı! Şimdi giriş yapabilirsiniz.');
            setIsLogin(true);
        } catch (error) {
            toast.error(error.message);
        }
    }
  };

  return (
    <div className="flex items-center justify-center mt-12 mb-20 px-4">
      <div className="bg-white p-8 md:p-10 rounded-3xl border border-orange-100 shadow-xl shadow-orange-900/5 w-full max-w-md relative overflow-hidden">
        
        <div className="absolute top-0 left-0 w-full h-1.5 bg-gradient-to-r from-orange-400 to-amber-400"></div>

        <h2 className="text-3xl font-extrabold mb-8 text-gray-900 text-center tracking-tight">
          {isLogin ? 'Hoş Geldiniz' : 'Aramıza Katılın'}
        </h2>
        
        <form className="space-y-5">
          {!isLogin && (
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-2">Ad Soyad</label>
              <input 
                type="text" 
                className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-orange-400 focus:bg-white transition-all text-gray-800" 
              />
            </div>
          )}
          <div>
            <label className="block text-sm font-bold text-gray-700 mb-2">E-posta</label>
            <input 
              type="email" 
              value={email}
              onChange={(e) => setEmail(e.target.value)} 
              className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-orange-400 focus:bg-white transition-all text-gray-800"
            />
          </div>
          <div>
            <label className="block text-sm font-bold text-gray-700 mb-2">Şifre</label>
            <input 
              type="password" 
              value={password}
              onChange={(e) => setPassword(e.target.value)} 
              className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-orange-400 focus:bg-white transition-all text-gray-800" 
            />
          </div>

          <button 
            type="button" 
            onClick={handleAuth}
            className="w-full bg-gradient-to-r from-orange-500 to-amber-500 text-white font-extrabold py-3.5 rounded-xl hover:shadow-lg hover:-translate-y-0.5 hover:from-orange-600 hover:to-amber-600 transition-all duration-300 mt-6 text-lg"
          >
            {isLogin ? 'Giriş Yap' : 'Kayıt Ol'}
          </button>
        </form>

        <div className="mt-8 pt-6 border-t border-gray-100 text-center">
          <p className="text-sm text-gray-500 mb-2">
            {isLogin ? 'Henüz biletini almadın mı?' : 'Zaten bir hesabın var mı?'}
          </p>
          <button 
            type="button" 
            onClick={() => setIsLogin(!isLogin)} 
            className="text-orange-600 hover:text-orange-700 font-extrabold text-sm hover:underline transition-colors"
          >
            {isLogin ? 'Hemen Ücretsiz Kayıt Ol' : 'Buradan Giriş Yap'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default Login;
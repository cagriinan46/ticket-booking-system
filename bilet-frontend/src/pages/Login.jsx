import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

function Login() {
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

        const response = await fetch('http://ticket-app-lb-1559682675.eu-central-1.elb.amazonaws.com/api/auth/login', {
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
            const response = await fetch('http://ticket-app-lb-1559682675.eu-central-1.elb.amazonaws.com/api/auth/register', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ email: email, password: password }) 
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
    <div className="flex items-center justify-center mt-12">
      <div className="bg-white p-8 rounded border border-gray-300 shadow-sm w-full max-w-md">
        <h2 className="text-2xl font-bold mb-6 text-gray-800 text-center border-b border-gray-200 pb-4">
          {isLogin ? 'Sisteme Giriş' : 'Yeni Kayıt'}
        </h2>
        
        <form className="space-y-4">
          {!isLogin && (
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-1">Ad Soyad</label>
              <input type="text" className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500" />
            </div>
          )}
          <div>
            <label className="block text-sm font-bold text-gray-700 mb-1">E-posta</label>
            <input 
              type="email" 
              value={email}
              onChange={(e) => setEmail(e.target.value)} 
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500" 
            />
          </div>
          <div>
            <label className="block text-sm font-bold text-gray-700 mb-1">Şifre</label>
            <input 
              type="password" 
              value={password}
              onChange={(e) => setPassword(e.target.value)} 
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500" 
            />
          </div>

          <button 
            type="button" 
            onClick={handleAuth}
            className="w-full bg-blue-600 text-white font-bold py-2 rounded hover:bg-blue-700 mt-4"
          >
            {isLogin ? 'Giriş Yap' : 'Kayıt Ol'}
          </button>
        </form>

        <div className="mt-6 text-center text-sm text-gray-600">
          <button 
            type="button" 
            onClick={() => setIsLogin(!isLogin)} 
            className="text-blue-600 hover:underline font-bold"
          >
            {isLogin ? 'Hesabınız yok mu? Kayıt olun' : 'Zaten hesabınız var mı? Giriş yapın'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default Login;
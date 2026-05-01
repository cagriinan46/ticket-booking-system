import React from 'react';
import { Outlet } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Navbar from './Navbar';
import Footer from './Footer';

function Layout() {
  return (
    <div className="min-h-screen bg-[#FCF9F0] text-gray-900 font-sans flex flex-col selection:bg-orange-200 selection:text-orange-900">
      <Navbar />
      <main className="flex-grow max-w-7xl mx-auto w-full p-4 md:p-6">
        <Outlet />
      </main>
      <Footer />
      <Toaster position="bottom-right" toastOptions={{
        style: {
          background: '#fff',
          color: '#333',
          borderRadius: '16px',
        }
      }} />
    </div>
  );
}

export default Layout;
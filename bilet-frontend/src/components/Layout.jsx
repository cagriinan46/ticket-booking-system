import React from 'react';
import { Outlet } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Navbar from './Navbar';
import Footer from './Footer';

function Layout() {
  return (
    <div className="min-h-screen bg-gray-100 text-gray-900 font-sans flex flex-col">
      <Navbar />
      <main className="flex-grow max-w-6xl mx-auto w-full p-6">
        <Outlet />
      </main>
      <Footer />
      <Toaster position="bottom-right" />
    </div>
  );
}

export default Layout;
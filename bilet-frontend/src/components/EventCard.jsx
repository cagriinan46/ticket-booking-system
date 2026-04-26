import React from 'react';
import { Link } from 'react-router-dom';

function EventCard({ event }) {
  return (
    <div className="border border-gray-300 bg-white p-4 flex flex-col h-full">
      
      <div className="w-full h-48 relative overflow-hidden bg-gray-900 mb-4 border border-gray-200">
        <img 
          src={event.image} 
          alt="" 
          className="absolute inset-0 w-full h-full object-cover blur-md opacity-60 scale-110" 
        />
        <img 
          src={event.image} 
          alt={event.title} 
          className="relative z-10 w-full h-full object-contain drop-shadow-2xl" 
        />
      </div>

      <h3 className="text-lg font-bold text-gray-800">{event.title}</h3>
      <p className="text-sm text-gray-500 mb-4">{event.date} - {event.location}</p>
      
      <div className="mt-auto flex justify-between items-center border-t border-gray-200 pt-3">
        <span className="font-bold text-gray-700">{event.price} ₺</span>
        <Link 
          to={`/event/${event.id}`} 
          className="bg-blue-600 text-white px-3 py-1 text-sm hover:bg-blue-700 transition-colors"
        >
          İncele
        </Link>
      </div>
    </div>
  );
}

export default EventCard;
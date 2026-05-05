import React from 'react';
import { Link } from 'react-router-dom';

function EventCard({ event, isFavorite, onToggleFavorite }) {
  
  const formatTurkishDate = (dateString) => {
    const date = new Date(dateString);
    if (isNaN(date)) return dateString; 
    
    const day = date.getDate();
    const month = date.toLocaleDateString('tr-TR', { month: 'long' });
    const weekday = date.toLocaleDateString('tr-TR', { weekday: 'long' });

    return `${day} ${month}, ${weekday}`;
  };

  return (
    <div className="group bg-white rounded-2xl p-4 flex flex-col h-full shadow-md hover:shadow-xl hover:-translate-y-1 transition-all duration-300 border border-orange-50 cursor-default relative">
      
      <button 
        onClick={(e) => {
          e.preventDefault(); 
          onToggleFavorite(event.id);
        }}
        className="absolute top-6 right-6 z-20 p-2.5 bg-white/80 backdrop-blur-md rounded-full shadow-md hover:scale-110 transition-transform group/btn"
      >
        <svg 
          className={`w-6 h-6 transition-colors ${isFavorite ? 'text-red-500' : 'text-gray-400 group-hover/btn:text-red-400'}`} 
          fill={isFavorite ? 'currentColor' : 'none'}
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
        </svg>
      </button>

      <div className="w-full h-52 relative overflow-hidden bg-gray-900 mb-5 rounded-xl">
        <img 
          src={event.image} 
          alt="" 
          className="absolute inset-0 w-full h-full object-cover blur-md opacity-50 scale-110 group-hover:scale-125 transition-transform duration-700" 
        />
        <img 
          src={event.image} 
          alt={event.title} 
          className="relative z-10 w-full h-full object-contain drop-shadow-2xl group-hover:scale-105 transition-transform duration-500" 
        />
      </div>

      <div className="px-1 flex flex-col flex-grow">
        <h3 className="text-[19px] font-extrabold text-gray-800 mb-1.5 line-clamp-2 group-hover:text-orange-600 transition-colors">
          {event.title}
        </h3>
        
        <div className="flex items-center text-sm text-gray-500 mb-4 font-medium">
          <svg className="w-4 h-4 mr-1.5 text-orange-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <span className="truncate">
            {formatTurkishDate(event.date)} 
            {event.time && ` - ${event.time}`}
          </span>
          <span className="mx-2 text-gray-300">|</span> 
          <span className="truncate">{event.location}</span>
        </div>
        
        <div className="mt-auto flex justify-between items-center border-t border-gray-100 pt-4">
          <span className="font-black text-xl text-orange-500">{event.price} ₺</span>
          <Link 
            to={`/event/${event.id}`} 
            className="bg-orange-50 text-orange-600 px-5 py-2 rounded-xl text-sm font-bold hover:bg-gradient-to-r hover:from-orange-500 hover:to-amber-500 hover:text-white transition-all duration-300 shadow-sm"
          >
            Bilet Al
          </Link>
        </div>
      </div>
    </div>
  );
}

export default EventCard;
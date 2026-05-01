import React from 'react';

function About() {
  return (
    <div className="max-w-4xl mx-auto mt-12 mb-20 px-4">
      <div className="bg-white p-8 md:p-16 rounded-3xl border border-orange-100 shadow-xl shadow-orange-900/5 text-center relative overflow-hidden">
        
        <div className="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-orange-500 to-amber-500"></div>
        
        <h1 className="text-4xl font-extrabold text-gray-900 mb-8 tracking-tight">Hakkımızda</h1>
        
        <div className="space-y-6 text-gray-600 leading-relaxed text-lg font-medium">
          <p>
            PortaBilet, en sevdiğiniz etkinliklere ulaşmanın en hızlı ve güvenilir yoludur. Konserlerden tiyatrolara, spor müsabakalarından festivallere kadar binlerce etkinliği tek bir çatı altında topluyor, kesintisiz ve güvenli bir bilet alma deneyimi sunuyoruz.
          </p>
          <p>
            Bu platform, sadece bir bilet satış sitesi değil; modern web mimarisi standartlarını sergilemek amacıyla sıfırdan geliştirilmiş kapsamlı bir vizyon projesidir. Ön yüzde en güncel teknolojilerle pürüzsüz bir kullanıcı deneyimi sağlarken, arka planda yüksek performanslı sunucular ve AWS bulut altyapısı ile binlerce işlemi aynı anda kaldırabilecek kusursuz bir ekosistem inşa edilmiştir.
          </p>
          <p className="font-black text-transparent bg-clip-text bg-gradient-to-r from-orange-500 to-amber-500 mt-8 text-2xl">
            Teknoloji ve eğlencenin buluştuğu yere hoş geldiniz!
          </p>
        </div>

        <div className="mt-14 pt-10 border-t border-orange-100 flex flex-wrap justify-center gap-12 text-sm text-gray-500">
          <div className="flex flex-col items-center group">
            <span className="font-black text-transparent bg-clip-text bg-gradient-to-r from-orange-500 to-amber-500 text-5xl mb-2 group-hover:scale-110 transition-transform">%100</span>
            <span className="font-bold text-gray-700 uppercase tracking-wider text-xs">GÜVENLİ ALTYAPI</span>
          </div>
          <div className="flex flex-col items-center group">
            <span className="font-black text-transparent bg-clip-text bg-gradient-to-r from-orange-500 to-amber-500 text-5xl mb-2 group-hover:scale-110 transition-transform">7/24</span>
            <span className="font-bold text-gray-700 uppercase tracking-wider text-xs">KESİNTİSİZ ERİŞİM</span>
          </div>
          <div className="flex flex-col items-center group">
            <span className="font-black text-transparent bg-clip-text bg-gradient-to-r from-orange-500 to-amber-500 text-5xl mb-2 group-hover:scale-110 transition-transform">Modern</span>
            <span className="font-bold text-gray-700 uppercase tracking-wider text-xs">AWS BULUT MİMARİSİ</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default About;
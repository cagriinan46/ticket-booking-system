import React from 'react';

function About() {
  return (
    <div className="max-w-4xl mx-auto mt-12 mb-20 px-4">
      <div className="bg-white p-8 md:p-12 rounded-lg border border-gray-200 shadow-sm text-center">
        <h1 className="text-3xl font-bold text-gray-800 mb-6">Hakkımızda</h1>
        
        <div className="space-y-6 text-gray-600 leading-relaxed text-lg">
          <p>
            BiletSistemi, en sevdiğiniz etkinliklere ulaşmanın en hızlı ve güvenilir yoludur. Konserlerden tiyatrolara, spor müsabakalarından festivallere kadar binlerce etkinliği tek bir çatı altında topluyor, kesintisiz ve güvenli bir bilet alma deneyimi sunuyoruz.
          </p>
          
          <p>
            Bu platform, sadece bir bilet satış sitesi değil; modern web mimarisi standartlarını sergilemek amacıyla sıfırdan geliştirilmiş kapsamlı bir vizyon projesidir. Ön yüzde en güncel teknolojilerle pürüzsüz bir kullanıcı deneyimi sağlarken, arka planda yüksek performanslı sunucular ve AWS bulut altyapısı ile binlerce işlemi aynı anda kaldırabilecek kusursuz bir ekosistem inşa edilmiştir.
          </p>

          <p className="font-semibold text-gray-800 mt-8 text-xl">
            Teknoloji ve eğlencenin buluştuğu yere hoş geldiniz!
          </p>
        </div>

        <div className="mt-12 pt-8 border-t border-gray-100 flex justify-center gap-12 text-sm text-gray-500">
          <div className="flex flex-col items-center">
            <span className="font-bold text-blue-600 text-2xl mb-1">%100</span>
            <span className="font-medium">Güvenli Altyapı</span>
          </div>
          <div className="flex flex-col items-center">
            <span className="font-bold text-blue-600 text-2xl mb-1">7/24</span>
            <span className="font-medium">Kesintisiz Erişim</span>
          </div>
          <div className="flex flex-col items-center">
            <span className="font-bold text-blue-600 text-2xl mb-1">Modern</span>
            <span className="font-medium">Bulut Mimarisi</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default About;
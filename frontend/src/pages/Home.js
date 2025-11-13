import React from 'react';
import { Search, Car, Wrench } from 'lucide-react';

const Home = ({ navigateTo, cartItemsCount, userData }) => {
  const ADMIN_ID = parseInt(process.env.REACT_APP_ADMIN_ID);
  const isAdmin = userData && userData.telegram_id === ADMIN_ID;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white p-6">
      <div className="max-w-md mx-auto">
        {/* Header */}
        <div className="text-center mb-8 pt-8">
          <h1 className="text-4xl font-bold mb-2">🚗 Market Auto Parts</h1>
          <p className="text-gray-300">Автозапчасти и обслуживание</p>
          {isAdmin && (
            <button
              onClick={() => navigateTo('admin')}
              className="mt-2 bg-purple-600 text-white px-3 py-1 rounded-full text-xs hover:bg-purple-700 transition"
            >
              👨‍💼 Админ-панель
            </button>
          )}
        </div>

        {/* Main Actions */}
        <div className="space-y-4 mb-24">
          {/* Поиск по артикулу */}
          <button
            onClick={() => navigateTo('search-article')}
            className="w-full bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl p-6 flex items-center justify-between hover:from-blue-700 hover:to-blue-800 transition shadow-lg border-2 border-blue-500"
            data-testid="search-article-button"
          >
            <div className="flex items-center space-x-4">
              <div className="bg-blue-500 p-3 rounded-lg">
                <Search size={24} />
              </div>
              <div className="text-left">
                <h3 className="font-bold text-lg">🔍 Поиск по артикулу</h3>
                <p className="text-sm text-blue-100">Введите номер запчасти</p>
              </div>
            </div>
            <div className="text-white text-2xl">→</div>
          </button>

          {/* Поиск по VIN */}
          <button
            onClick={() => navigateTo('search-vin')}
            className="w-full bg-gradient-to-r from-green-600 to-green-700 text-white rounded-xl p-6 flex items-center justify-between hover:from-green-700 hover:to-green-800 transition shadow-lg border-2 border-green-500"
            data-testid="search-vin-button"
          >
            <div className="flex items-center space-x-4">
              <div className="bg-green-500 p-3 rounded-lg">
                <Car size={24} />
              </div>
              <div className="text-left">
                <h3 className="font-bold text-lg">🚙 Поиск по VIN</h3>
                <p className="text-sm text-green-100">AI поиск для вашего авто</p>
              </div>
            </div>
            <div className="text-white text-2xl">→</div>
          </button>

          {/* Мой гараж */}
          <button
            onClick={() => navigateTo('garage')}
            className="w-full bg-gradient-to-r from-gray-800 to-gray-900 text-white rounded-xl p-6 flex items-center justify-between hover:from-gray-700 hover:to-gray-800 transition shadow-lg border-2 border-yellow-500"
            data-testid="garage-button-main"
          >
            <div className="flex items-center space-x-4">
              <div className="bg-yellow-500 p-3 rounded-lg">
                <Wrench size={24} className="text-gray-900" />
              </div>
              <div className="text-left">
                <h3 className="font-bold text-lg">🔧 Мой Гараж</h3>
                <p className="text-sm text-gray-300">Автомобили и обслуживание</p>
              </div>
            </div>
            <div className="text-yellow-500 text-2xl">→</div>
          </button>

          {/* Корзина */}
          <button
            onClick={() => navigateTo('cart')}
            className="w-full bg-gradient-to-r from-orange-600 to-orange-700 text-white rounded-xl p-6 flex items-center justify-between hover:from-orange-700 hover:to-orange-800 transition shadow-lg border-2 border-orange-500"
          >
            <div className="flex items-center space-x-4">
              <div className="bg-orange-500 p-3 rounded-lg">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
              </div>
              <div className="text-left">
                <h3 className="font-bold text-lg">🛒 Корзина</h3>
                <p className="text-sm text-orange-100">Товары в корзине</p>
              </div>
            </div>
            <div className="text-orange-300 text-2xl">→</div>
          </button>

          {/* Мои заказы */}
          <button
            onClick={() => navigateTo('orders')}
            className="w-full bg-gradient-to-r from-purple-600 to-purple-700 text-white rounded-xl p-6 flex items-center justify-between hover:from-purple-700 hover:to-purple-800 transition shadow-lg border-2 border-purple-500"
          >
            <div className="flex items-center space-x-4">
              <div className="bg-purple-500 p-3 rounded-lg">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div className="text-left">
                <h3 className="font-bold text-lg">📋 Мои заказы</h3>
                <p className="text-sm text-purple-100">История заказов</p>
              </div>
            </div>
            <div className="text-purple-300 text-2xl">→</div>
          </button>
        </div>

        {/* Info */}
        <div className="mt-8 text-center text-gray-300 text-sm">
          <p>💡 Более 1000+ запчастей в наличии</p>
          <p className="mt-2">🚚 Доставка от 1 дня в Тюмени</p>
        </div>
      </div>
    </div>
  );
};

export default Home;

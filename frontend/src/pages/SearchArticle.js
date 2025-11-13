import React, { useState } from 'react';
import axios from 'axios';
import { Search, Loader2, ShoppingCart, Package, ArrowLeft } from 'lucide-react';
import { showAlert } from '../utils/telegram';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const SearchArticle = ({ userData, onAddToCart, navigateTo, initialArticle }) => {
  const [article, setArticle] = useState(initialArticle || '');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [searchPerformed, setSearchPerformed] = useState(false);
  
  // Фильтры и сортировка
  const [availabilityFilter, setAvailabilityFilter] = useState(''); // '', 'in_stock_tyumen', 'on_order'
  const [sortBy, setSortBy] = useState(''); // '', 'price_asc', 'price_desc'

  // Автоматический поиск при initialArticle
  React.useEffect(() => {
    if (initialArticle && initialArticle.trim()) {
      handleSearch();
    }
  }, [initialArticle]);

  const handleSearch = async () => {
    if (!article.trim()) {
      showAlert('Введите артикул запчасти');
      return;
    }

    setLoading(true);
    setSearchPerformed(true);

    try {
      const response = await axios.post(`${API}/search/article`, {
        article: article.trim(),
        telegram_id: userData.telegram_id,
        availability_filter: availabilityFilter || null,
        sort_by: sortBy || null
      });

      setResults(response.data.results || []);
      
      if (response.data.results.length === 0) {
        showAlert('Запчасти не найдены');
      }
    } catch (error) {
      console.error('Error searching:', error);
      showAlert('Ошибка при поиске');
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleAddToCart = (part) => {
    const item = {
      article: part.article,
      name: part.name,
      brand: part.brand,
      price: part.price,
      quantity: 1,
      delivery_days: part.delivery_days,
      supplier: part.supplier
    };

    onAddToCart(item);
  };

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-6">
        <button
          onClick={() => navigateTo('home')}
          className="flex items-center text-white mb-4 hover:text-blue-100"
        >
          <ArrowLeft size={20} className="mr-2" />
          Назад
        </button>
        <h1 className="text-2xl font-bold mb-4">🔍 Поиск по артикулу</h1>
        
        {/* Search Input */}
        <div className="flex space-x-2 mb-4">
          <input
            type="text"
            value={article}
            onChange={(e) => setArticle(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Введите артикул"
            className="flex-1 px-4 py-3 rounded-lg text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-300"
            data-testid="article-input"
          />
          <button
            onClick={handleSearch}
            disabled={loading}
            className="bg-white text-blue-600 px-6 py-3 rounded-lg font-semibold hover:bg-blue-50 transition disabled:opacity-50"
            data-testid="search-button"
          >
            {loading ? <Loader2 className="animate-spin" size={20} /> : <Search size={20} />}
          </button>
        </div>

        {/* Filters */}
        <div className="grid grid-cols-2 gap-2">
          {/* Availability Filter */}
          <select
            value={availabilityFilter}
            onChange={(e) => setAvailabilityFilter(e.target.value)}
            className="px-3 py-2 rounded-lg text-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
          >
            <option value="">Все товары</option>
            <option value="in_stock_tyumen">В наличии (Тюмень)</option>
            <option value="on_order">Под заказ</option>
          </select>

          {/* Sort */}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="px-3 py-2 rounded-lg text-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
          >
            <option value="">По умолчанию</option>
            <option value="price_asc">Сначала дешёвые</option>
            <option value="price_desc">Сначала дорогие</option>
          </select>
        </div>
      </div>

      {/* Results */}
      <div className="p-4">
        {loading ? (
          <div className="text-center py-12">
            <Loader2 className="animate-spin mx-auto mb-4 text-blue-600" size={48} />
            <p className="text-gray-600">Поиск запчастей...</p>
          </div>
        ) : results.length > 0 ? (
          <div className="space-y-3">
            <h2 className="text-lg font-semibold text-gray-800 mb-3">
              Найдено: {results.length} запчастей
            </h2>
            {results.map((part, index) => (
              <div
                key={index}
                className="bg-white rounded-lg shadow p-4 hover:shadow-md transition"
                data-testid={`part-item-${index}`}
              >
                <div className="flex justify-between items-start mb-3">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      <Package size={16} className="text-blue-600" />
                      <span className="font-mono text-sm text-gray-600">{part.article}</span>
                    </div>
                    <h3 className="font-semibold text-gray-800">{part.name}</h3>
                    <p className="text-sm text-gray-600">{part.brand}</p>
                  </div>
                </div>

                <div className="flex justify-between items-center">
                  <div>
                    <p className="text-2xl font-bold text-green-600">
                      {Math.ceil(part.price).toLocaleString('ru-RU')} ₽
                    </p>
                    <p className="text-sm text-gray-500">
                      🚚 Доставка: {
                        part.delivery_days === 0 ? 'Сегодня' : 
                        part.delivery_days === 1 || part.delivery_display === 'Завтра' ? 'Завтра' : 
                        `${part.delivery_days} дн.`
                      }
                    </p>
                    <p className={`text-sm font-semibold ${part.delivery_days === 0 ? 'text-green-600' : 'text-orange-600'}`}>
                      {part.quantity > 0 ? `✅ В наличии: ${part.quantity} шт.` : '📦 Под заказ'}
                    </p>
                    {part.warehouse && (
                      <p className="text-xs text-gray-500">
                        📍 {part.warehouse}
                      </p>
                    )}
                    {part.is_cross && (
                      <p className="text-xs text-blue-500 font-semibold">
                        🔄 Аналог
                      </p>
                    )}
                    {part.stock_description && (
                      <p className="text-xs text-gray-400">
                        📍 {part.stock_description}
                      </p>
                    )}
                  </div>

                  <button
                    onClick={() => handleAddToCart(part)}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition flex items-center space-x-2"
                    data-testid={`add-to-cart-${index}`}
                  >
                    <ShoppingCart size={18} />
                    <span>В корзину</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : searchPerformed ? (
          <div className="text-center py-12">
            <p className="text-gray-600 mb-4">Запчасти не найдены</p>
            <p className="text-sm text-gray-500">Попробуйте изменить запрос</p>
          </div>
        ) : (
          <div className="text-center py-12">
            <Search size={48} className="mx-auto mb-4 text-gray-400" />
            <p className="text-gray-600">Введите артикул для поиска</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default SearchArticle;

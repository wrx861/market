import React, { useState, useEffect } from 'react';

const Expenses = ({ vehicleId, onBack, backendUrl }) => {
  const [expenses, setExpenses] = useState(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState('all');

  useEffect(() => {
    loadExpenses();
  }, [period]);

  const loadExpenses = async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `${backendUrl}/api/garage/vehicle/${vehicleId}/expenses?period=${period}`
      );
      const data = await response.json();
      
      if (data.status === 'success') {
        setExpenses(data);
      }
    } catch (error) {
      console.error('Error loading expenses:', error);
    } finally {
      setLoading(false);
    }
  };

  const getCategoryEmoji = (key) => {
    const emojis = {
      service: '🔧',
      fuel: '⛽',
      parts: '🔩',
      wash: '💧',
      parking: '🅿️',
      fines: '🚨',
      insurance: '🛡️',
      other: '📝'
    };
    return emojis[key] || '📝';
  };

  const formatAmount = (amount) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  const getPeriodLabel = () => {
    const labels = {
      'month': 'За месяц',
      '3months': 'За 3 месяца',
      'year': 'За год',
      'all': 'За все время'
    };
    return labels[period] || 'За все время';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900 text-white pb-20">
        <div className="bg-gradient-to-r from-purple-900 to-purple-800 p-6 shadow-2xl border-b-4 border-purple-500">
          <button onClick={onBack} className="flex items-center text-purple-300 mb-4 hover:text-purple-200">
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Назад
          </button>
        </div>
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Загрузка...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900 text-white pb-20">
      <div className="bg-gradient-to-r from-purple-900 to-purple-800 p-6 shadow-2xl border-b-4 border-purple-500">
        <button onClick={onBack} className="flex items-center text-purple-300 mb-4 hover:text-purple-200">
          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Назад
        </button>
        <h1 className="text-2xl font-bold flex items-center">
          💰 Аналитика расходов
        </h1>
      </div>

      <div className="p-4">

        {/* Фильтр по периоду */}
        <select 
          value={period} 
          onChange={(e) => setPeriod(e.target.value)}
          className="w-full bg-gray-800 border border-gray-700 text-white rounded-xl p-3 mb-4"
        >
          <option value="month">За месяц</option>
          <option value="3months">За 3 месяца</option>
          <option value="year">За год</option>
          <option value="all">За все время</option>
        </select>

        {/* Общая сумма */}
        <div className="bg-gradient-to-r from-purple-600 to-purple-700 rounded-xl p-6 mb-6 shadow-lg">
          <div className="text-purple-200 text-sm mb-2">{getPeriodLabel()}</div>
          <div className="text-4xl font-bold text-white">{formatAmount(expenses?.total || 0)}</div>
        </div>

        {/* Категории */}
        {expenses?.categories && expenses.categories.length > 0 ? (
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-300">По категориям</h3>
            <div className="space-y-3">
              {expenses.categories.map((cat) => (
                <div key={cat.key} className="bg-gray-800 rounded-xl p-4 border-l-4 border-purple-500">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-3 flex-1">
                      <span className="text-2xl">{getCategoryEmoji(cat.key)}</span>
                      <div className="flex-1">
                        <div className="text-white font-semibold">{cat.name}</div>
                        <div className="text-gray-400 text-sm">{cat.count} записей</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-white font-bold text-lg">{formatAmount(cat.total)}</div>
                      <div className="text-purple-400 text-sm">{cat.percentage}%</div>
                    </div>
                  </div>
                  <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-purple-500 to-purple-600 rounded-full" 
                      style={{ width: `${cat.percentage}%` }}
                    />
                  </div>
                </div>
              ))}
          </div>
        </div>
        ) : (
          <div className="bg-gray-800 rounded-xl p-8 text-center border-2 border-dashed border-gray-600">
            <p className="text-gray-400">Нет данных о расходах за выбранный период</p>
          </div>
        )}

        {/* Последние расходы */}
        {expenses?.expenses && expenses.expenses.length > 0 && (
          <div className="mt-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-300">Последние расходы</h3>
            <div className="space-y-2">
              {expenses.expenses.slice(0, 20).map((exp, index) => (
                <div key={index} className="bg-gray-800 rounded-lg p-3 flex items-center gap-3">
                  <div className="text-2xl">
                    {getCategoryEmoji(exp.category)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-white font-medium truncate">{exp.title}</div>
                    <div className="text-gray-400 text-sm">{formatDate(exp.date)}</div>
                  </div>
                  <div className="text-white font-bold">
                    {formatAmount(exp.amount)}
                  </div>
                </div>
              ))}
            </div>
            {expenses.expenses_count > 20 && (
              <div className="text-center mt-4 text-gray-400 text-sm">
                Показано 20 из {expenses.expenses_count} записей
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Expenses;

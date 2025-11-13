import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { FileText, Loader2, Package } from 'lucide-react';
import { showAlert } from '../utils/telegram';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Orders = ({ userData }) => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadOrders();
  }, []);

  const loadOrders = async () => {
    try {
      const response = await axios.get(`${API}/orders/${userData.telegram_id}`);
      setOrders(response.data.orders || []);
    } catch (error) {
      console.error('Error loading orders:', error);
      showAlert('Ошибка при загрузке заказов');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      new: { label: 'Новый', color: 'bg-blue-100 text-blue-800' },
      processing: { label: 'В обработке', color: 'bg-yellow-100 text-yellow-800' },
      completed: { label: 'Выполнен', color: 'bg-green-100 text-green-800' },
      cancelled: { label: 'Отменен', color: 'bg-red-100 text-red-800' }
    };

    const config = statusConfig[status] || statusConfig.new;

    return (
      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${config.color}`}>
        {config.label}
      </span>
    );
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="animate-spin mx-auto mb-4 text-blue-600" size={48} />
          <p className="text-gray-600">Загрузка заказов...</p>
        </div>
      </div>
    );
  }

  if (orders.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center p-6">
          <FileText size={64} className="mx-auto mb-4 text-gray-400" />
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Нет заказов</h2>
          <p className="text-gray-600">Вы еще не сделали ни одного заказа</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      <div className="bg-blue-600 text-white p-6">
        <h1 className="text-2xl font-bold">📋 Мои заказы</h1>
        <p className="text-sm text-blue-100">Всего: {orders.length}</p>
      </div>

      <div className="p-4 space-y-4">
        {orders.map((order, index) => (
          <div
            key={order.id}
            className="bg-white rounded-lg shadow-md p-4"
            data-testid={`order-item-${index}`}
          >
            {/* Order Header */}
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="font-semibold text-gray-800">
                  Заказ №{order.id.slice(0, 8)}
                </h3>
                <p className="text-xs text-gray-500">
                  {formatDate(order.created_at)}
                </p>
              </div>
              {getStatusBadge(order.status)}
            </div>

            {/* Order Items */}
            <div className="space-y-2 mb-4">
              {order.items.map((item, idx) => (
                <div key={idx} className="flex justify-between items-center text-sm">
                  <div className="flex-1">
                    <p className="font-medium text-gray-800">{item.name}</p>
                    <p className="text-xs text-gray-500">
                      {item.brand} • {item.article}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-gray-800">
                      {(item.price * item.quantity).toLocaleString('ru-RU')} ₽
                    </p>
                    <p className="text-xs text-gray-500">{item.quantity} шт.</p>
                  </div>
                </div>
              ))}
            </div>

            {/* Order Total */}
            <div className="border-t pt-3 flex justify-between items-center">
              <span className="font-semibold text-gray-700">Итого:</span>
              <span className="text-xl font-bold text-green-600">
                {order.total.toLocaleString('ru-RU')} ₽
              </span>
            </div>

            {/* Contact Info */}
            {order.user_info && (
              <div className="mt-3 pt-3 border-t text-sm text-gray-600">
                <p>👤 {order.user_info.name}</p>
                <p>📞 {order.user_info.phone}</p>
                {order.user_info.address && (
                  <p>📍 {order.user_info.address}</p>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default Orders;

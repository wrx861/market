import React, { useState } from 'react';
import axios from 'axios';
import { ShoppingCart, Trash2, Plus, Minus, Loader2 } from 'lucide-react';
import { showAlert, showConfirm } from '../utils/telegram';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Cart = ({ userData, cart, onUpdate, onRemove, navigateTo }) => {
  const [loading, setLoading] = useState(false);
  const [orderLoading, setOrderLoading] = useState(false);
  const [showOrderForm, setShowOrderForm] = useState(false);
  const [orderForm, setOrderForm] = useState({
    name: userData?.name || '',
    phone: '',
    address: ''
  });

  const total = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);

  const updateQuantity = (article, newQuantity) => {
    if (newQuantity < 1) return;
    onUpdate(article, newQuantity);
  };

  const removeItem = (article) => {
    showConfirm('Удалить товар из корзины?', (confirmed) => {
      if (confirmed) {
        onRemove(article);
      }
    });
  };

  const handleOrderSubmit = async () => {
    if (!orderForm.name || !orderForm.phone) {
      showAlert('Заполните все обязательные поля');
      return;
    }

    setOrderLoading(true);

    try {
      const response = await axios.post(`${API}/orders`, {
        telegram_id: userData.telegram_id,
        user_info: orderForm
      });

      showAlert(
        `✅ Заказ №${response.data.order_id.slice(0, 8)} создан!\n\nСумма: ${response.data.total} ₽\n\nМы свяжемся с вами в ближайшее время!`,
        () => {
          navigateTo('orders');
        }
      );
    } catch (error) {
      console.error('Error creating order:', error);
      showAlert('Ошибка при создании заказа');
    } finally {
      setOrderLoading(false);
    }
  };

  if (cart.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center p-6">
          <ShoppingCart size={64} className="mx-auto mb-4 text-gray-400" />
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Корзина пуста</h2>
          <p className="text-gray-600 mb-6">Добавьте товары для оформления заказа</p>
          <button
            onClick={() => navigateTo('home')}
            className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition"
          >
            Перейти к поиску
          </button>
        </div>
      </div>
    );
  }

  if (showOrderForm) {
    return (
      <div className="min-h-screen bg-gray-50 pb-32">
        <div className="bg-blue-600 text-white p-6">
          <h1 className="text-2xl font-bold">📝 Оформление заказа</h1>
        </div>

        <div className="p-4">
          <div className="bg-white rounded-lg shadow-md p-6 mb-4">
            <h3 className="font-semibold text-gray-800 mb-4">Контактные данные</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Имя *
                </label>
                <input
                  type="text"
                  value={orderForm.name}
                  onChange={(e) => setOrderForm({...orderForm, name: e.target.value})}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  data-testid="order-name-input"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Телефон *
                </label>
                <input
                  type="tel"
                  value={orderForm.phone}
                  onChange={(e) => setOrderForm({...orderForm, phone: e.target.value})}
                  placeholder="+7 (___) ___-__-__"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  data-testid="order-phone-input"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Адрес доставки (опционально)
                </label>
                <textarea
                  value={orderForm.address}
                  onChange={(e) => setOrderForm({...orderForm, address: e.target.value})}
                  rows={3}
                  placeholder="Улица, дом, квартира"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  data-testid="order-address-input"
                />
              </div>
            </div>

            <div className="mt-6 pt-6 border-t">
              <div className="flex justify-between text-lg font-semibold mb-4">
                <span>Итого:</span>
                <span className="text-green-600">{total.toLocaleString('ru-RU')} ₽</span>
              </div>

              <button
                onClick={handleOrderSubmit}
                disabled={orderLoading}
                className="w-full bg-green-600 text-white px-6 py-4 rounded-lg font-semibold hover:bg-green-700 transition disabled:opacity-50 flex items-center justify-center"
                data-testid="confirm-order-button"
              >
                {orderLoading ? (
                  <>
                    <Loader2 className="animate-spin mr-2" size={20} />
                    Оформляем...
                  </>
                ) : (
                  'Подтвердить заказ'
                )}
              </button>

              <button
                onClick={() => setShowOrderForm(false)}
                className="w-full mt-3 text-gray-600 px-6 py-3 rounded-lg hover:bg-gray-100 transition"
              >
                Назад к корзине
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-32">
      <div className="bg-blue-600 text-white p-6">
        <h1 className="text-2xl font-bold">🛒 Корзина</h1>
        <p className="text-sm text-blue-100">Товаров: {cart.length}</p>
      </div>

      <div className="p-4 space-y-3">
        {cart.map((item, index) => (
          <div
            key={index}
            className="bg-white rounded-lg shadow p-4"
            data-testid={`cart-item-${index}`}
          >
            <div className="flex justify-between items-start mb-3">
              <div className="flex-1">
                <span className="font-mono text-xs text-gray-500">{item.article}</span>
                <h3 className="font-semibold text-gray-800">{item.name}</h3>
                <p className="text-sm text-gray-600">{item.brand}</p>
                <p className="text-sm text-gray-500">🚚 {item.delivery_days} дн.</p>
              </div>
              <button
                onClick={() => removeItem(item.article)}
                className="text-red-500 hover:text-red-700 transition"
                data-testid={`remove-item-${index}`}
              >
                <Trash2 size={20} />
              </button>
            </div>

            <div className="flex justify-between items-center">
              <div className="flex items-center space-x-3">
                <button
                  onClick={() => updateQuantity(item.article, item.quantity - 1)}
                  disabled={item.quantity <= 1}
                  className="bg-gray-200 p-2 rounded hover:bg-gray-300 transition disabled:opacity-50"
                  data-testid={`decrease-${index}`}
                >
                  <Minus size={16} />
                </button>
                <span className="font-semibold text-lg w-8 text-center">{item.quantity}</span>
                <button
                  onClick={() => updateQuantity(item.article, item.quantity + 1)}
                  className="bg-gray-200 p-2 rounded hover:bg-gray-300 transition"
                  data-testid={`increase-${index}`}
                >
                  <Plus size={16} />
                </button>
              </div>

              <div className="text-right">
                <p className="text-xl font-bold text-green-600">
                  {(item.price * item.quantity).toLocaleString('ru-RU')} ₽
                </p>
                <p className="text-xs text-gray-500">
                  {item.price.toLocaleString('ru-RU')} ₽ / шт.
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Footer with Total */}
      <div className="fixed bottom-0 left-0 right-0 bg-white shadow-lg p-4 border-t">
        <div className="max-w-md mx-auto">
          <div className="flex justify-between items-center mb-4">
            <span className="text-lg font-semibold text-gray-800">Итого:</span>
            <span className="text-2xl font-bold text-green-600">
              {total.toLocaleString('ru-RU')} ₽
            </span>
          </div>
          <button
            onClick={() => setShowOrderForm(true)}
            className="w-full bg-green-600 text-white px-6 py-4 rounded-lg font-semibold hover:bg-green-700 transition"
            data-testid="proceed-to-checkout-button"
          >
            Оформить заказ
          </button>
        </div>
      </div>
    </div>
  );
};

export default Cart;

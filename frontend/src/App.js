import React, { useState, useEffect } from 'react';
import axios from 'axios';
import '@/App.css';

// Import components
import Home from './pages/Home';
import SearchArticle from './pages/SearchArticle';
import SearchVIN from './pages/SearchVIN';
import Cart from './pages/Cart';
import Orders from './pages/Orders';
import Admin from './pages/Admin';
import Garage from './pages/Garage';
import AddVehicle from './pages/AddVehicle';
import VehicleDetail from './pages/VehicleDetail';
import ServiceLog from './pages/ServiceLog';
import BoardJournal from './pages/BoardJournal';
import Diagnostics from './pages/Diagnostics';
import Reminders from './pages/Reminders';
import AddService from './pages/AddService';
import AddLog from './pages/AddLog';
import AddReminder from './pages/AddReminder';
import Expenses from './pages/Expenses';

// Import Telegram utils
import { initWebApp, getUserData, BackButton, showAlert } from './utils/telegram';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [currentPage, setCurrentPage] = useState('home');
  const [pageParams, setPageParams] = useState(null);
  const [editData, setEditData] = useState(null);
  const [userData, setUserData] = useState(null);
  const [cart, setCart] = useState([]);
  const [searchResults, setSearchResults] = useState([]);
  const [carInfo, setCarInfo] = useState(null);

  useEffect(() => {
    // Инициализация Telegram WebApp
    initWebApp();

    // Получаем данные пользователя
    const user = getUserData();
    setUserData(user);

    // Создаем/обновляем пользователя в базе
    createOrUpdateUser(user);
    
    // Загружаем корзину
    loadCart(user.telegram_id);

    // Настраиваем кнопку "Назад"
    BackButton.onClick(() => {
      handleBackButton();
    });

    // Проверяем URL параметры для VIN
    const urlParams = new URLSearchParams(window.location.search);
    const vin = urlParams.get('vin');
    if (vin) {
      setCurrentPage('search-vin');
    }
  }, []);

  useEffect(() => {
    // Показываем/скрываем кнопку "Назад"
    if (currentPage === 'home') {
      BackButton.hide();
    } else {
      BackButton.show();
    }
  }, [currentPage]);

  const createOrUpdateUser = async (user) => {
    try {
      await axios.post(`${API}/users`, user);
    } catch (error) {
      console.error('Error creating/updating user:', error);
    }
  };

  const loadCart = async (telegramId) => {
    try {
      const response = await axios.get(`${API}/cart/${telegramId}`);
      setCart(response.data.items || []);
    } catch (error) {
      console.error('Error loading cart:', error);
    }
  };

  const handleBackButton = () => {
    if (currentPage === 'home') {
      return;
    }
    if (currentPage === 'cart' || currentPage === 'orders') {
      setCurrentPage('home');
    } else if (currentPage === 'search-results') {
      // Вернуться к поиску
      const prevPage = searchResults.length > 0 ? 'search-article' : 'home';
      setCurrentPage(prevPage);
    } else {
      setCurrentPage('home');
    }
  };

  const addToCart = async (item) => {
    try {
      await axios.post(`${API}/cart/add`, {
        telegram_id: userData.telegram_id,
        item: item
      });
      
      // Обновляем локальную корзину
      setCart(prevCart => {
        const existing = prevCart.find(i => i.article === item.article);
        if (existing) {
          return prevCart.map(i => 
            i.article === item.article 
              ? { ...i, quantity: i.quantity + item.quantity }
              : i
          );
        }
        return [...prevCart, item];
      });

      showAlert('Товар добавлен в корзину!');
    } catch (error) {
      console.error('Error adding to cart:', error);
      showAlert('Ошибка при добавлении в корзину');
    }
  };

  const updateCartItem = async (article, quantity) => {
    try {
      await axios.post(`${API}/cart/update`, {
        telegram_id: userData.telegram_id,
        article,
        quantity
      });
      
      setCart(prevCart => 
        prevCart.map(item => 
          item.article === article ? { ...item, quantity } : item
        )
      );
    } catch (error) {
      console.error('Error updating cart:', error);
    }
  };

  const removeFromCart = async (article) => {
    try {
      await axios.post(`${API}/cart/remove`, {
        telegram_id: userData.telegram_id,
        article
      });
      
      setCart(prevCart => prevCart.filter(item => item.article !== article));
      showAlert('Товар удален из корзины');
    } catch (error) {
      console.error('Error removing from cart:', error);
    }
  };

  const navigateTo = (page, params = null, editDataParam = null) => {
    setCurrentPage(page);
    setPageParams(params);
    setEditData(editDataParam);
  };

  // Render current page
  const renderPage = () => {
    switch (currentPage) {
      case 'home':
        return <Home navigateTo={navigateTo} cartItemsCount={cart.length} userData={userData} />;
      
      case 'search-article':
        return (
          <SearchArticle 
            userData={userData}
            onSearch={setSearchResults}
            onAddToCart={addToCart}
            navigateTo={navigateTo}
            initialArticle={pageParams?.article}
          />
        );
      
      case 'search-vin':
        return (
          <SearchVIN 
            userData={userData}
            onSearch={setSearchResults}
            onCarInfo={setCarInfo}
            onAddToCart={addToCart}
            navigateTo={navigateTo}
          />
        );
      
      case 'cart':
        return (
          <Cart 
            userData={userData}
            cart={cart}
            onUpdate={updateCartItem}
            onRemove={removeFromCart}
            navigateTo={navigateTo}
          />
        );
      
      case 'orders':
        return (
          <Orders 
            userData={userData}
            navigateTo={navigateTo}
          />
        );
      
      case 'admin':
        // Проверяем что это админ
        const ADMIN_ID = parseInt(process.env.REACT_APP_ADMIN_ID);
        if (userData && userData.telegram_id === ADMIN_ID) {
          return <Admin navigateTo={navigateTo} />;
        } else {
          return <Home navigateTo={navigateTo} cartItemsCount={cart.length} userData={userData} />;
        }
      
      case 'garage':
        return <Garage userData={userData} navigateTo={navigateTo} />;
      
      case 'add-vehicle':
        return <AddVehicle userData={userData} navigateTo={navigateTo} />;
      
      case 'vehicle-detail':
        return <VehicleDetail userData={userData} navigateTo={navigateTo} vehicleId={pageParams} />;
      
      case 'service-log':
        return <ServiceLog userData={userData} navigateTo={navigateTo} vehicleId={pageParams} />;
      
      case 'board-journal':
        return <BoardJournal userData={userData} navigateTo={navigateTo} vehicleId={pageParams} />;
      
      case 'diagnostics':
        return <Diagnostics userData={userData} navigateTo={navigateTo} />;
      
      case 'reminders':
        return <Reminders userData={userData} navigateTo={navigateTo} vehicleId={pageParams} />;
      
      case 'expenses':
        return (
          <Expenses 
            vehicleId={pageParams} 
            onBack={() => navigateTo('vehicle-detail', pageParams)}
            backendUrl={BACKEND_URL}
          />
        );
      
      case 'add-service':
        return <AddService userData={userData} navigateTo={navigateTo} vehicleId={pageParams} editData={editData} />;
      
      case 'add-log':
        return <AddLog userData={userData} navigateTo={navigateTo} vehicleId={pageParams} editData={editData} />;
      
      case 'add-reminder':
        return <AddReminder userData={userData} navigateTo={navigateTo} vehicleId={pageParams} editData={editData} />;
      
      default:
        return <Home navigateTo={navigateTo} cartItemsCount={cart.length} userData={userData} />;
    }
  };

  return (
    <div className="App min-h-screen bg-gray-50">
      {renderPage()}
    </div>
  );
}

export default App;

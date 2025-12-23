import React from 'react';
import ReactDOM from 'react-dom/client';
import './src/index.css';
import App from './App';
import { LanguageProvider } from './contexts/LanguageContext';

const rootElement = document.getElementById('root');
if (!rootElement) {
  console.error("Failed to find root element");
  throw new Error("Could not find root element to mount to");
}

try {
  const root = ReactDOM.createRoot(rootElement);
  root.render(
    <LanguageProvider>
      <App />
    </LanguageProvider>
  );
  console.log("App mounted successfully");
} catch (error) {
  console.error("Error mounting React app:", error);
}
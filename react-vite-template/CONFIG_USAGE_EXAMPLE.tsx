/**
 * 配置使用示例
 * 展示如何在 React 組件中使用 config.ts 中的配置
 */

import React from 'react';
import { siteConfig, getTelegramUrl, getWhatsAppUrl, getEmailAddress, getLogoPath } from './src/config';

// 示例 1: Footer 組件中使用配置
export function Footer() {
  return (
    <footer className="footer">
      <div className="container">
        {/* 使用 Logo */}
        <img src={getLogoPath()} alt={siteConfig.projectName} />
        
        <div className="contact-info">
          <h3>聯繫我們</h3>
          
          {/* Telegram */}
          <a 
            href={getTelegramUrl()} 
            target="_blank" 
            rel="noopener noreferrer"
          >
            {siteConfig.contact.telegram.displayName}
          </a>
          
          {/* WhatsApp */}
          <a 
            href={getWhatsAppUrl()} 
            target="_blank" 
            rel="noopener noreferrer"
          >
            {siteConfig.contact.whatsapp.displayName}
          </a>
          
          {/* Email */}
          <a href={`mailto:${getEmailAddress()}`}>
            {siteConfig.contact.email.displayName}
          </a>
        </div>
      </div>
    </footer>
  );
}

// 示例 2: Header 組件中使用配置
export function Header() {
  return (
    <header className="header">
      <img src={getLogoPath()} alt={siteConfig.projectName} />
      <h1>{siteConfig.projectName}</h1>
      <p>{siteConfig.projectDescription}</p>
    </header>
  );
}

// 示例 3: 聯繫方式卡片組件
export function ContactCard() {
  return (
    <div className="contact-card">
      <h2>聯繫我們</h2>
      <ul>
        <li>
          <strong>Telegram:</strong>{' '}
          <a href={siteConfig.contact.telegram.url}>
            {siteConfig.contact.telegram.username}
          </a>
        </li>
        <li>
          <strong>WhatsApp:</strong>{' '}
          <a href={siteConfig.contact.whatsapp.url}>
            {siteConfig.contact.whatsapp.number}
          </a>
        </li>
        <li>
          <strong>Email:</strong>{' '}
          <a href={`mailto:${siteConfig.contact.email.address}`}>
            {siteConfig.contact.email.address}
          </a>
        </li>
        {siteConfig.contact.phone && (
          <li>
            <strong>電話:</strong> {siteConfig.contact.phone.number}
          </li>
        )}
      </ul>
    </div>
  );
}

// 示例 4: 在頁面組件中使用
export function HomePage() {
  return (
    <div className="home-page">
      <Header />
      <main>
        <h2>歡迎使用 {siteConfig.projectName}</h2>
        <p>{siteConfig.projectDescription}</p>
        <ContactCard />
      </main>
      <Footer />
    </div>
  );
}

import React, { useState, useMemo, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Users, Server, BrainCircuit, Check, Plus, Minus, Zap, Globe, Cpu, ChevronDown, Info, ShieldCheck, Database, Rocket, X, Code, Lock, HelpCircle, Phone, MessageSquare, CreditCard } from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';
import { useAIChat } from '../contexts/AIChatContext';
import { Button } from './ui/Button';

// Data Structure for Service Modules
type PricingCategory = 'traffic' | 'dev' | 'ai' | 'data';

interface SubOption {
  labelKey: string; // Translation key for the label (e.g., 'label_region')
  type: 'select' | 'radio';
  choices: {
    labelKey: string; // Changed from label to labelKey for translation
    value: string;
    priceMod: number; // Price modifier (added to base price)
  }[];
}

interface ServiceItem {
  id: string;
  category: PricingCategory;
  translationKey: string;
  descKey: string;
  featKey: string; // New: Detailed Features
  outKey: string; // New: Outcome
  basePrice: number; // Base price in USDT
  unit: string;
  popular?: boolean;
  options?: SubOption[]; // Configurable options
}

interface CartItem {
  quantity: number;
  selectedOptions: Record<string, string>;
}

// Market-aligned pricing data (USDT Standard) - 17 Items (Updated with Payment, SMS, Voice)
const PRICING_DATA: ServiceItem[] = [
  // --- Pillar 1: Global Traffic & Resources ---
  { 
    id: 'cloud_phone', 
    category: 'traffic', 
    translationKey: 'item_cloud_phone', 
    descKey: 'item_cloud_desc',
    featKey: 'item_cloud_feat',
    outKey: 'item_cloud_out',
    basePrice: 20, 
    unit: 'device/mo',
    popular: true,
    options: [
      {
        labelKey: 'label_region',
        type: 'select',
        choices: [
            { labelKey: 'opt_sea', value: 'sea', priceMod: 0 },
            { labelKey: 'opt_us', value: 'us', priceMod: 10 },
            { labelKey: 'opt_eu', value: 'eu', priceMod: 5 }
        ]
      }
    ]
  },
  { 
    id: 'wa_api', 
    category: 'traffic', 
    translationKey: 'item_wa_api', 
    descKey: 'item_wa_desc',
    featKey: 'item_wa_feat',
    outKey: 'item_wa_out',
    basePrice: 100, 
    unit: 'mo',
    options: [
        {
            labelKey: 'label_throughput',
            type: 'radio',
            choices: [
                { labelKey: 'opt_10k', value: '10k', priceMod: 0 },
                { labelKey: 'opt_unl', value: 'unl', priceMod: 150 }
            ]
        }
    ]
  },
  { 
    id: 'sms_blast', 
    category: 'traffic', 
    translationKey: 'c8_title', // Reusing capabilities key or creating new? Let's use new translation key pattern
    descKey: 'c8_desc', // Using capability description
    featKey: 'c8_desc', // Simplified for pricing view
    outKey: 'c8_desc',
    basePrice: 500, 
    unit: '10k SMS',
    popular: true
  },
  { 
    id: 'voice_command', 
    category: 'traffic', 
    translationKey: 'c9_title', 
    descKey: 'c9_desc',
    featKey: 'c9_desc',
    outKey: 'c9_desc',
    basePrice: 300, 
    unit: 'campaign' 
  },
  { 
    id: 'res_proxy', 
    category: 'traffic', 
    translationKey: 'item_res_proxy', 
    descKey: 'item_res_desc',
    featKey: 'item_res_feat',
    outKey: 'item_res_out',
    basePrice: 5, 
    unit: 'IP/mo'
  },
  {
    id: 'account_trade',
    category: 'traffic', 
    translationKey: 'item_account_trade',
    descKey: 'item_account_trade_desc',
    featKey: 'item_account_trade_feat',
    outKey: 'item_account_trade_out',
    basePrice: 50,
    unit: 'account',
    popular: true,
    options: [
      {
        labelKey: 'label_platform',
        type: 'select',
        choices: [
          { labelKey: 'opt_fb', value: 'fb', priceMod: 50 },
          { labelKey: 'opt_google', value: 'google', priceMod: 100 },
          { labelKey: 'opt_tg', value: 'tg', priceMod: 0 }
        ]
      }
    ]
  },

  // --- Pillar 2: Agile Dev & Ecosystem ---
  { 
    id: 'tg_miniapp', 
    category: 'dev', 
    translationKey: 'item_tg_miniapp', 
    descKey: 'item_tg_miniapp_desc',
    featKey: 'item_tg_miniapp_feat',
    outKey: 'item_tg_miniapp_out',
    basePrice: 1500, 
    unit: 'setup',
    popular: true,
    options: [
        {
            labelKey: 'label_features',
            type: 'radio',
            choices: [
                { labelKey: 'opt_ton', value: 'ton', priceMod: 0 },
                { labelKey: 'opt_fiat', value: 'fiat', priceMod: 500 }
            ]
        }
    ]
  },
  { 
    id: 'global_payment', 
    category: 'dev', 
    translationKey: 'c7_title', 
    descKey: 'c7_desc',
    featKey: 'c7_desc',
    outKey: 'c7_desc',
    basePrice: 1000, 
    unit: 'setup' 
  },
  { 
    id: 'crypto_pay', 
    category: 'dev', 
    translationKey: 'item_crypto_pay', 
    descKey: 'item_crypto_pay_desc',
    featKey: 'item_crypto_pay_feat',
    outKey: 'item_crypto_pay_out',
    basePrice: 500, 
    unit: 'setup' 
  },
  { 
    id: 'white_label', 
    category: 'dev', 
    translationKey: 'item_white_label', 
    descKey: 'item_white_label_desc',
    featKey: 'item_white_label_feat',
    outKey: 'item_white_label_out',
    basePrice: 3000, 
    unit: 'license' 
  },

  // --- Pillar 3: Cognitive AI ---
  { 
    id: 'voice_clone', 
    category: 'ai', 
    translationKey: 'item_voice_clone', 
    descKey: 'item_voice_clone_desc',
    featKey: 'item_voice_clone_feat',
    outKey: 'item_voice_clone_out',
    basePrice: 200, 
    unit: 'model' 
  },
  { 
    id: 'sales_bot', 
    category: 'ai', 
    translationKey: 'item_sales_bot', 
    descKey: 'item_sales_bot_desc',
    featKey: 'item_sales_bot_feat',
    outKey: 'item_sales_bot_out',
    basePrice: 800, 
    unit: 'agent/mo',
    popular: true 
  },
  {
    id: 'voice_setup',
    category: 'ai',
    translationKey: 'item_voice_setup',
    descKey: 'item_voice_setup_desc',
    featKey: 'item_voice_setup_feat',
    outKey: 'item_voice_setup_out',
    basePrice: 5000, 
    unit: 'node',
  },
  { 
    id: 'video_remix', 
    category: 'ai', 
    translationKey: 'item_video_remix', 
    descKey: 'item_video_remix_desc',
    featKey: 'item_video_remix_feat',
    outKey: 'item_video_remix_out',
    basePrice: 150, 
    unit: 'mo' 
  },
  { 
    id: 'rednote_matrix', 
    category: 'ai', 
    translationKey: 'item_rednote_matrix', 
    descKey: 'item_rednote_matrix_desc',
    featKey: 'item_rednote_matrix_feat',
    outKey: 'item_rednote_matrix_out',
    basePrice: 120, 
    unit: 'node/mo' 
  },

  // --- Pillar 4: Data & Risk ---
  { 
    id: 'risk_ctrl', 
    category: 'data', 
    translationKey: 'item_risk_ctrl', 
    descKey: 'item_risk_ctrl_desc',
    featKey: 'item_risk_ctrl_feat',
    outKey: 'item_risk_ctrl_out',
    basePrice: 50, 
    unit: 'license/mo' 
  },
  { 
    id: 'competitor', 
    category: 'data', 
    translationKey: 'item_competitor', 
    descKey: 'item_competitor_desc',
    featKey: 'item_competitor_feat',
    outKey: 'item_competitor_out',
    basePrice: 200, 
    unit: 'report' 
  },
  { 
    id: 'roi_dash', 
    category: 'data', 
    translationKey: 'item_roi_dash', 
    descKey: 'item_roi_dash_desc',
    featKey: 'item_roi_dash_feat',
    outKey: 'item_roi_dash_out',
    basePrice: 300, 
    unit: 'mo' 
  },
];

export const PricingSection: React.FC = () => {
  const { t } = useLanguage();
  const { openChat } = useAIChat();
  
  const [cart, setCart] = useState<Record<string, CartItem>>({});
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const toggleExpand = (id: string) => {
    setExpandedId(prev => prev === id ? null : id);
  };

  const handleAddToCart = (id: string) => {
    setCart(prev => {
        if (prev[id]) return prev;
        
        const item = PRICING_DATA.find(i => i.id === id);
        const defaults: Record<string, string> = {};
        if (item?.options) {
            item.options.forEach(opt => {
                defaults[opt.labelKey] = opt.choices[0].value;
            });
        }
        
        return { ...prev, [id]: { quantity: 1, selectedOptions: defaults } };
    });
    if (!expandedId) setExpandedId(id);
  };

  const handleRemoveFromCart = (id: string) => {
      setCart(prev => {
          const next = { ...prev };
          delete next[id];
          return next;
      });
  };

  const updateQuantity = (id: string, delta: number) => {
    setCart(prev => {
        if (!prev[id]) return prev;
        const newQty = Math.max(1, prev[id].quantity + delta);
        return { ...prev, [id]: { ...prev[id], quantity: newQty } };
    });
  };

  const updateOption = (itemId: string, optionKey: string, value: string) => {
      setCart(prev => {
          if (!prev[itemId]) return prev;
          return {
              ...prev,
              [itemId]: {
                  ...prev[itemId],
                  selectedOptions: {
                      ...prev[itemId].selectedOptions,
                      [optionKey]: value
                  }
              }
          }
      });
  };

  const getUnitPrice = (itemId: string) => {
      const item = PRICING_DATA.find(i => i.id === itemId);
      if (!item) return 0;
      
      let price = item.basePrice;
      const cartItem = cart[itemId];
      
      if (cartItem && item.options) {
          item.options.forEach(opt => {
              const selectedValue = cartItem.selectedOptions[opt.labelKey];
              const choice = opt.choices.find(c => c.value === selectedValue);
              if (choice) {
                  price += choice.priceMod;
              }
          });
      }
      return price;
  };

  const calculateTotal = useMemo(() => {
    let total = 0;
    (Object.entries(cart) as [string, CartItem][]).forEach(([id, data]) => {
      total += getUnitPrice(id) * data.quantity;
    });
    return total.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  }, [cart]);

  const handleConsultAI = (e: React.MouseEvent) => {
    const selectedModules = (Object.entries(cart) as [string, CartItem][])
      .map(([id, data]) => {
        const item = PRICING_DATA.find(i => i.id === id);
        if (!item) return '';
        
        const optionsStr = item.options?.map(opt => {
            const val = data.selectedOptions[opt.labelKey];
            const choice = opt.choices.find(c => c.value === val);
            return choice ? t(`pricing.${choice.labelKey}`) : '';
        }).join(', ');

        // Handle inconsistent key structure for new items vs old
        const name = item.translationKey.startsWith('c') 
            ? t(`capabilities.${item.translationKey}`) 
            : t(`pricing.${item.translationKey}`);

        return `${name} (x${data.quantity}) ${optionsStr ? `[${optionsStr}]` : ''}`;
      })
      .join('; ');

    const prompt = t('pricing.consult_prompt')
      .replace('{modules}', selectedModules || 'None')
      .replace('{total}', calculateTotal);

    openChat(
      `User requesting strategy analysis for: ${selectedModules}`,
      prompt,
      e.currentTarget as HTMLElement
    );
  };

  // 4 New Pillars Definition
  const categories: { key: PricingCategory; icon: any; label: string; color: string; bg: string; border: string }[] = [
    { key: 'traffic', icon: Globe, label: 'pricing.cat_traffic', color: 'text-cyan-400', bg: 'bg-cyan-500/5', border: 'border-cyan-500/30' },
    { key: 'dev', icon: Code, label: 'pricing.cat_dev', color: 'text-purple-400', bg: 'bg-purple-500/5', border: 'border-purple-500/30' },
    { key: 'ai', icon: BrainCircuit, label: 'pricing.cat_ai', color: 'text-orange-400', bg: 'bg-orange-500/5', border: 'border-orange-500/30' },
    { key: 'data', icon: Lock, label: 'pricing.cat_data', color: 'text-emerald-400', bg: 'bg-emerald-500/5', border: 'border-emerald-500/30' },
  ];

  return (
    <div className="relative">
      <div className="grid lg:grid-cols-3 gap-8">
        
        {/* Left Column: Product Catalog */}
        <div className="lg:col-span-2 space-y-12">
          {categories.map((cat) => (
            <div key={cat.key} className="space-y-4">
              <div className="flex items-center gap-3 mb-6 pb-2 border-b border-white/5">
                <div className={`p-2 rounded bg-white/5 ${cat.color} bg-opacity-10`}>
                    <cat.icon className={`w-5 h-5 ${cat.color}`} />
                </div>
                <h3 className="text-xl font-mono font-bold text-white uppercase tracking-wider">{t(cat.label)}</h3>
                <button 
                    onClick={(e) => openChat(`User requesting general info about pricing category: ${t(cat.label)}`, `Analyzing category: ${t(cat.label)}...\n\nThis module suite is designed to maximize ${cat.key === 'traffic' ? 'user acquisition' : cat.key === 'dev' ? 'conversion rates' : cat.key === 'ai' ? 'operational efficiency' : 'security and insights'}.\n\nDo you have specific volume requirements?`, e.currentTarget)}
                    className="ml-auto p-1 text-zinc-600 hover:text-cyan-400 transition-colors"
                >
                    <HelpCircle className="w-4 h-4" />
                </button>
              </div>
              
              <div className="grid grid-cols-1 gap-4">
                {PRICING_DATA.filter(item => item.category === cat.key).map(item => {
                  const cartItem = cart[item.id];
                  const isInCart = !!cartItem;
                  const isExpanded = expandedId === item.id;
                  const unitPrice = getUnitPrice(item.id);

                  // Dynamic Styles based on Category
                  const catConfig = categories.find(c => c.key === item.category);
                  const textClass = isInCart ? catConfig?.color : 'text-zinc-200';

                  // Handle key prefix for translation fallback (capabilities vs pricing)
                  const name = item.translationKey.startsWith('c') 
                    ? t(`capabilities.${item.translationKey}`) 
                    : t(`pricing.${item.translationKey}`);
                  
                  const desc = item.descKey.startsWith('c')
                    ? t(`capabilities.${item.descKey}`)
                    : t(`pricing.${item.descKey}`);

                  const featureText = item.featKey.startsWith('c')
                    ? t(`capabilities.${item.featKey}`)
                    : t(`pricing.${item.featKey}`);

                  const outcomeText = item.outKey.startsWith('c')
                    ? t(`capabilities.${item.outKey}`)
                    : t(`pricing.${item.outKey}`);

                  return (
                    <motion.div
                      key={item.id}
                      layout
                      initial={{ opacity: 0, y: 10 }}
                      whileInView={{ opacity: 1, y: 0 }}
                      viewport={{ once: true }}
                      className={`relative rounded-xl border transition-all duration-300 overflow-hidden ${
                        isInCart 
                          ? `bg-zinc-900/80 ${catConfig?.border} shadow-[0_0_15px_-5px_rgba(255,255,255,0.1)]` 
                          : 'bg-zinc-900/40 border-white/5 hover:border-white/20'
                      }`}
                    >
                        {/* Card Header */}
                        <div 
                            className="p-5 cursor-pointer flex justify-between items-start gap-4"
                            onClick={() => toggleExpand(item.id)}
                        >
                            {item.popular && (
                                <div className={`absolute top-0 right-0 px-2 py-1 bg-white/10 text-[10px] font-bold text-white uppercase rounded-bl-lg backdrop-blur-sm border-l border-b border-white/10`}>
                                    HOT
                                </div>
                            )}
                            
                            <div className="flex items-start gap-4">
                                <div className={`mt-1 w-5 h-5 rounded border flex items-center justify-center transition-colors ${
                                    isInCart ? `${catConfig?.bg.replace('/5', '/20')} ${catConfig?.border}` : 'border-zinc-600 group-hover:border-zinc-400'
                                }`}>
                                    {isInCart && <Check className="w-3.5 h-3.5 text-white" />}
                                </div>
                                <div>
                                    <h4 className={`font-bold font-mono text-base ${textClass}`}>
                                        {name}
                                    </h4>
                                    <p className="text-xs text-zinc-500 mt-1 line-clamp-1">
                                        {desc}
                                    </p>
                                </div>
                            </div>

                            <div className="text-right shrink-0">
                                <div className={`font-mono font-bold text-lg ${textClass}`}>
                                    {unitPrice.toLocaleString()} <span className="text-[10px] text-zinc-600 font-normal">USDT</span>
                                </div>
                                <div className="text-[10px] text-zinc-600 uppercase">/{item.unit}</div>
                                <ChevronDown className={`w-4 h-4 text-zinc-500 mx-auto mt-2 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
                            </div>
                        </div>

                        {/* Expanded Details Panel */}
                        <AnimatePresence>
                            {isExpanded && (
                                <motion.div
                                    initial={{ height: 0, opacity: 0 }}
                                    animate={{ height: 'auto', opacity: 1 }}
                                    exit={{ height: 0, opacity: 0 }}
                                    className={`border-t border-white/5 ${catConfig?.bg}`}
                                >
                                    <div className="p-5 space-y-6">
                                        {/* Action: Add to Cart / Quantity */}
                                        <div className="flex items-center justify-between">
                                            {!isInCart ? (
                                                <Button 
                                                    variant="secondary" 
                                                    className="w-full py-2 text-xs"
                                                    onClick={(e) => { e.stopPropagation(); handleAddToCart(item.id); }}
                                                >
                                                    {t('pricing.btn_select')}
                                                </Button>
                                            ) : (
                                                <div className="flex items-center gap-4 bg-zinc-900 border border-white/10 rounded-lg p-1">
                                                    <button 
                                                        onClick={() => updateQuantity(item.id, -1)}
                                                        className="p-2 rounded hover:bg-white/10 text-zinc-400 hover:text-white transition-colors"
                                                    >
                                                        <Minus className="w-4 h-4" />
                                                    </button>
                                                    <span className="font-mono font-bold text-white min-w-[30px] text-center">
                                                        {cartItem?.quantity}
                                                    </span>
                                                    <button 
                                                        onClick={() => updateQuantity(item.id, 1)}
                                                        className="p-2 rounded hover:bg-white/10 text-zinc-400 hover:text-white transition-colors"
                                                    >
                                                        <Plus className="w-4 h-4" />
                                                    </button>
                                                    <button 
                                                        onClick={() => handleRemoveFromCart(item.id)}
                                                        className="ml-2 text-[10px] text-red-500 hover:text-red-400 underline px-2"
                                                    >
                                                        Remove
                                                    </button>
                                                </div>
                                            )}
                                        </div>

                                        {/* Config Options */}
                                        {isInCart && item.options && (
                                            <div className={`space-y-4 p-4 bg-black/40 rounded-lg border ${catConfig?.border}`}>
                                                <h5 className={`text-xs font-mono uppercase tracking-widest mb-3 border-b border-white/5 pb-1 ${textClass}`}>Configuration</h5>
                                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                    {item.options.map((opt, idx) => (
                                                        <div key={idx}>
                                                            <label className="text-[10px] text-zinc-400 uppercase mb-1.5 block">{t(`pricing.${opt.labelKey}`)}</label>
                                                            <div className="relative">
                                                                <select 
                                                                    className="w-full bg-zinc-900 border border-zinc-700 rounded px-3 py-2 text-xs text-white focus:border-cyan-500 focus:outline-none appearance-none"
                                                                    value={cartItem?.selectedOptions[opt.labelKey]}
                                                                    onChange={(e) => updateOption(item.id, opt.labelKey, e.target.value)}
                                                                >
                                                                    {opt.choices.map((choice) => (
                                                                        <option key={choice.value} value={choice.value}>
                                                                            {t(`pricing.${choice.labelKey}`)} {choice.priceMod > 0 ? `(+${choice.priceMod} USDT)` : ''}
                                                                        </option>
                                                                    ))}
                                                                </select>
                                                                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-3 h-3 text-zinc-500 pointer-events-none" />
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}

                                        {/* Detailed Info Grid */}
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
                                            <div>
                                                <div className="flex items-center gap-2 text-zinc-200 font-bold mb-2">
                                                    <Info className={`w-4 h-4 ${catConfig?.color}`} />
                                                    {t('pricing.label_features')}
                                                </div>
                                                <p className="text-zinc-300 text-xs leading-relaxed">
                                                    {featureText}
                                                </p>
                                            </div>
                                            <div>
                                                <div className="flex items-center gap-2 text-zinc-200 font-bold mb-2">
                                                    <ShieldCheck className={`w-4 h-4 ${catConfig?.color}`} />
                                                    {t('pricing.label_outcome')}
                                                </div>
                                                <p className="text-zinc-300 text-xs leading-relaxed">
                                                    {outcomeText}
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </motion.div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        {/* Right Column: Sticky Calculator */}
        <div className="lg:col-span-1 relative">
          <div className="sticky top-24 max-h-[85vh] flex flex-col">
             <div className="p-6 rounded-2xl bg-gradient-to-b from-zinc-900 to-black border border-cyan-500/30 shadow-[0_0_50px_-20px_rgba(0,255,255,0.2)] backdrop-blur-xl relative overflow-hidden flex flex-col h-full">
                {/* Background FX */}
                <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-10 pointer-events-none"></div>
                <div className="absolute top-0 right-0 w-32 h-32 bg-cyan-500/10 rounded-full blur-2xl -mr-10 -mt-10 pointer-events-none"></div>

                <div className="flex items-center gap-2 mb-6 border-b border-white/10 pb-4 shrink-0">
                    <Cpu className="w-5 h-5 text-cyan-400" />
                    <h3 className="text-xl font-bold text-white font-mono">{t('pricing.selected')}</h3>
                </div>

                {/* Cart Items List */}
                <div className="flex-1 overflow-y-auto custom-scrollbar pr-2 min-h-[150px]">
                   {Object.keys(cart).length === 0 ? (
                      <div className="h-full flex flex-col items-center justify-center text-zinc-600 space-y-4 py-8 border-2 border-dashed border-zinc-800 rounded-xl">
                         <Database className="w-10 h-10 opacity-20" />
                         <span className="text-xs font-mono text-center opacity-50">INITIATE_MODULE_SELECTION</span>
                      </div>
                   ) : (
                      <div className="space-y-4">
                          {(Object.entries(cart) as [string, CartItem][]).map(([id, data]) => {
                              const item = PRICING_DATA.find(i => i.id === id);
                              if (!item) return null;
                              const unitPrice = getUnitPrice(id);
                              const catConfig = categories.find(c => c.key === item.category);
                              
                              const name = item.translationKey.startsWith('c') 
                                ? t(`capabilities.${item.translationKey}`) 
                                : t(`pricing.${item.translationKey}`);

                              return (
                                  <motion.div 
                                    key={id} 
                                    layout
                                    initial={{ opacity: 0, x: -10 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    className={`group relative pl-3 border-l-2 ${catConfig?.border.replace('/30', '/60')} hover:border-white transition-colors`}
                                  >
                                      <div className="flex justify-between items-start">
                                          <div className="text-sm font-bold text-zinc-300">
                                              <span className={`${catConfig?.color} mr-2`}>x{data.quantity}</span>
                                              {name}
                                          </div>
                                          <button 
                                            onClick={() => handleRemoveFromCart(id)}
                                            className="opacity-0 group-hover:opacity-100 text-zinc-500 hover:text-red-500 transition-opacity absolute right-0 top-0"
                                          >
                                              <X className="w-4 h-4" />
                                          </button>
                                      </div>
                                      
                                      {item.options && (
                                          <div className="flex flex-wrap gap-1 mt-1">
                                              {item.options.map(opt => {
                                                  const val = data.selectedOptions[opt.labelKey];
                                                  const choice = opt.choices.find(c => c.value === val);
                                                  return choice ? (
                                                      <span key={opt.labelKey} className="text-[9px] text-zinc-500 bg-white/5 px-1.5 rounded">
                                                          {t(`pricing.${choice.labelKey}`)}
                                                      </span>
                                                  ) : null;
                                              })}
                                          </div>
                                      )}

                                      <div className="flex justify-end mt-1">
                                          <div className="font-mono text-xs text-zinc-400">
                                             {(unitPrice * data.quantity).toLocaleString()} USDT
                                          </div>
                                      </div>
                                  </motion.div>
                              )
                          })}
                      </div>
                   )}
                </div>

                {/* Total & Action */}
                <div className="border-t border-white/10 pt-4 mt-4 shrink-0 bg-black/20 -mx-6 px-6 -mb-6 pb-6">
                   <div className="flex justify-between items-end mb-4">
                      <span className="text-zinc-400 text-xs uppercase tracking-widest">{t('pricing.total_est')}</span>
                   </div>
                   <div className="text-4xl font-mono font-bold text-white text-right mb-6 text-transparent bg-clip-text bg-gradient-to-r from-white to-cyan-400 drop-shadow-[0_0_10px_rgba(0,255,255,0.3)]">
                      {calculateTotal} <span className="text-sm text-zinc-600 font-normal">USDT</span>
                   </div>

                   <Button 
                      onClick={handleConsultAI}
                      disabled={Object.keys(cart).length === 0}
                      className="w-full justify-center"
                   >
                      <Zap className="w-4 h-4 mr-2 fill-current" />
                      {t('pricing.btn_consult')}
                   </Button>

                   <div className="mt-4 text-center">
                      <p className="text-[9px] text-zinc-600">
                        *AI Analysis Required for Final Deployment
                      </p>
                   </div>
                </div>
             </div>
          </div>
        </div>
      </div>
    </div>
  );
};
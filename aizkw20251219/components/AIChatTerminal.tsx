import React, { useEffect, useRef, useState, useLayoutEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Send, Bot, Cpu, Activity, ChevronRight, Sparkles, Command, Terminal } from 'lucide-react';
import { useAIChat, Message } from '../contexts/AIChatContext';

// --- Helper: Inline Text Parser ---
const parseInline = (text: string) => {
  const elements: (string | React.ReactNode)[] = [];
  // Regex to match **bold**, *italic*, `code`
  const regex = /(\*\*.*?\*\*|\*.*?\*|`.*?`)/g;
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      elements.push(text.substring(lastIndex, match.index));
    }
    
    const raw = match[0];
    const key = `inline-${lastIndex}`;

    if (raw.startsWith('**')) {
      elements.push(<strong key={key} className="text-cyan-200 font-bold">{raw.slice(2, -2)}</strong>);
    } else if (raw.startsWith('`')) {
      elements.push(<code key={key} className="bg-zinc-800/80 text-cyan-300 px-1.5 py-0.5 rounded text-[10px] font-mono border border-zinc-700/50">{raw.slice(1, -1)}</code>);
    } else if (raw.startsWith('*')) {
      elements.push(<em key={key} className="text-purple-300 not-italic">{raw.slice(1, -1)}</em>);
    }
    
    lastIndex = regex.lastIndex;
  }
  
  if (lastIndex < text.length) {
    elements.push(text.substring(lastIndex));
  }

  return elements.length > 0 ? elements : text;
};

// --- Markdown Renderer Component ---
const MarkdownRenderer: React.FC<{ content: string }> = React.memo(({ content }) => {
  // Split by code blocks first
  const parts = content.split(/(```[\s\S]*?```)/g);

  return (
    <div className="space-y-2 text-sm">
      {parts.map((part, index) => {
        // Handle Code Blocks
        if (part.startsWith('```') && part.endsWith('```')) {
          // Extract content and optional language
          const lines = part.slice(3, -3).split('\n');
          let codeContent = lines.join('\n');
          let lang = 'Code';
          
          if (lines.length > 0 && /^[a-z]+$/.test(lines[0].trim())) {
             lang = lines[0].trim();
             codeContent = lines.slice(1).join('\n');
          } else if (codeContent.startsWith('\n')) {
             codeContent = codeContent.slice(1);
          }

          return (
            <div key={index} className="my-3 rounded-md bg-zinc-950 border border-zinc-800/80 overflow-hidden shadow-lg group/code">
               <div className="flex items-center justify-between px-3 py-1.5 bg-zinc-900 border-b border-zinc-800">
                  <span className="text-[10px] text-zinc-500 uppercase font-mono tracking-wider">{lang}</span>
                  <div className="flex gap-1.5">
                     <div className="w-2 h-2 rounded-full bg-red-500/20 group-hover/code:bg-red-500/50 transition-colors" />
                     <div className="w-2 h-2 rounded-full bg-yellow-500/20 group-hover/code:bg-yellow-500/50 transition-colors" />
                     <div className="w-2 h-2 rounded-full bg-green-500/20 group-hover/code:bg-green-500/50 transition-colors" />
                  </div>
               </div>
               <div className="p-3 overflow-x-auto custom-scrollbar bg-black/50">
                  <pre className="font-mono text-xs text-cyan-300/90 whitespace-pre-wrap break-all leading-relaxed">
                    {codeContent.trim()}
                  </pre>
               </div>
            </div>
          );
        }

        // Handle Text Formatting (Headers, Lists, Paragraphs)
        return (
          <div key={index} className="space-y-1">
            {part.split('\n').map((line, i) => {
                const trimmed = line.trim();
                if (!trimmed) return <div key={i} className="h-1" />;
                
                // Headers
                if (line.startsWith('### ')) return <h3 key={i} className="text-cyan-400 font-bold text-sm mt-3 mb-1 tracking-wide">{parseInline(line.slice(4))}</h3>;
                if (line.startsWith('## ')) return <h2 key={i} className="text-white font-bold text-base mt-4 mb-2 border-b border-white/10 pb-1">{parseInline(line.slice(3))}</h2>;

                // Lists
                if (trimmed.startsWith('- ') || trimmed.startsWith('• ') || trimmed.startsWith('* ')) {
                    return (
                        <div key={i} className="flex gap-2 ml-1 relative pl-2">
                             <span className="absolute left-0 top-2 w-1 h-1 rounded-full bg-cyan-500/80 shrink-0" />
                             <span className="text-zinc-300 leading-relaxed">{parseInline(trimmed.slice(2))}</span>
                        </div>
                    );
                }
                
                // Ordered Lists
                 const orderedMatch = trimmed.match(/^(\d+)\.\s/);
                 if (orderedMatch) {
                   return (
                      <div key={i} className="flex gap-2 ml-1">
                          <span className="text-cyan-500/80 font-mono text-xs mt-0.5 select-none">{orderedMatch[1]}.</span>
                          <span className="text-zinc-300 leading-relaxed">{parseInline(trimmed.slice(orderedMatch[0].length))}</span>
                      </div>
                  );
                 }

                // Standard paragraph
                return <div key={i} className="text-zinc-300 leading-relaxed">{parseInline(line)}</div>;
            })}
          </div>
        );
      })}
    </div>
  );
});

// --- Memoized Message Item ---
const ChatMessageItem = React.memo(({ msg }: { msg: Message }) => {
  const messageVariants = {
    userInitial: { opacity: 0, scale: 1.1, x: 20 },
    aiInitial: { opacity: 0, scale: 0.9, x: -20 },
    visible: { 
      opacity: 1, 
      scale: 1, 
      x: 0,
      transition: { type: "spring" as const, stiffness: 300, damping: 24 }
    }
  };

  return (
    <motion.div 
      variants={messageVariants}
      initial={msg.role === 'user' ? 'userInitial' : 'aiInitial'}
      animate="visible"
      className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
    >
        <div className={`max-w-[85%] rounded-lg p-3 relative group shadow-sm ${
          msg.role === 'user' 
            ? 'bg-cyan-950/40 border border-cyan-500/30 text-cyan-100 rounded-tr-none' 
            : 'bg-zinc-900/90 border border-zinc-700 text-zinc-300 rounded-tl-none'
        }`}>
          {msg.role === 'ai' && (
            <div className="absolute -top-3 -left-3 p-1 bg-zinc-950 border border-zinc-700 rounded-full z-10">
                <Bot className="w-3 h-3 text-cyan-500" />
            </div>
          )}
          
          <div className="leading-relaxed">
            <MarkdownRenderer content={msg.content} />
          </div>

          <div className={`text-[9px] mt-1 opacity-0 group-hover:opacity-100 transition-opacity ${msg.role === 'user' ? 'text-cyan-500/50 text-right' : 'text-zinc-600'}`}>
              {new Date(msg.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
          </div>
        </div>
    </motion.div>
  );
});

export const AIChatTerminal: React.FC = () => {
  const { isOpen, closeChat, messages, sendMessage, isTyping, triggerRect, clearChat, suggestions } = useAIChat();
  const [input, setInput] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [activeSuggestionIndex, setActiveSuggestionIndex] = useState(-1);
  
  const scrollRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  
  // Dynamic Styles State
  const [chatStyle, setChatStyle] = useState<React.CSSProperties>({});
  const [beakStyle, setBeakStyle] = useState<React.CSSProperties>({});
  const [isFixed, setIsFixed] = useState(false);
  const [isMobileLayout, setIsMobileLayout] = useState(false);

  // Filter suggestions based on input
  const filteredSuggestions = useMemo(() => {
    // If input is empty, show all suggestions
    if (!input.trim()) return suggestions;

    // Filter by case-insensitive match
    const lowerInput = input.trim().toLowerCase();
    return suggestions.filter(s => s.toLowerCase().includes(lowerInput));
  }, [input, suggestions]);

  // Reset active index when suggestions change
  useEffect(() => {
    setActiveSuggestionIndex(-1);
  }, [filteredSuggestions]);

  // --- Advanced Positioning Logic ---
  useLayoutEffect(() => {
    if (!isOpen) return;

    const viewportW = window.innerWidth;
    const viewportH = window.innerHeight;
    const mobileBreakpoint = 768;
    const isMobile = viewportW < mobileBreakpoint;
    setIsMobileLayout(isMobile);

    if (isMobile) {
        // Mobile Layout: Bottom Sheet
        setChatStyle({
            position: 'fixed',
            bottom: 0,
            left: 0,
            right: 0,
            width: '100%',
            height: '80vh',
            maxHeight: '80vh',
            zIndex: 60,
            borderBottomLeftRadius: 0,
            borderBottomRightRadius: 0,
            borderTop: '1px solid rgba(6,182,212,0.4)',
            boxShadow: '0 -10px 40px rgba(0,0,0,0.8)'
        });
        setBeakStyle({ display: 'none' });
        setIsFixed(true); 
        return;
    }

    if (!triggerRect) {
      // Desktop: Default Center
      setIsFixed(false);
      setChatStyle({});
      return;
    }

    // Desktop: Trigger-based positioning
    setIsFixed(true);
    const GAP = 16;
    const PADDING = 10;
    const IDEAL_W = 400;
    const IDEAL_H = 500;
    const MIN_H = 300;
    const MIN_W = 300;

    const spaceBottom = viewportH - (triggerRect.top + triggerRect.height) - GAP - PADDING;
    const spaceTop = triggerRect.top - GAP - PADDING;
    const spaceRight = viewportW - (triggerRect.left + triggerRect.width) - GAP - PADDING;
    const spaceLeft = triggerRect.left - GAP - PADDING;

    let placement = 'bottom';
    const isWideScreen = viewportW > 800;

    if (spaceBottom >= MIN_H) placement = 'bottom';
    else if (spaceTop >= MIN_H) placement = 'top';
    else if (isWideScreen && spaceRight >= MIN_W) placement = 'right';
    else if (isWideScreen && spaceLeft >= MIN_W) placement = 'left';
    else placement = spaceBottom > spaceTop ? 'bottom' : 'top';

    let top = 0, left = 0, width = IDEAL_W, height = IDEAL_H;
    let beakS: React.CSSProperties = {};
    const triggerCenterX = triggerRect.left + triggerRect.width / 2;
    const triggerCenterY = triggerRect.top + triggerRect.height / 2;

    const clampHorizontal = () => {
        left = triggerCenterX - (width / 2);
        if (left < PADDING) left = PADDING;
        if (left + width > viewportW - PADDING) left = viewportW - PADDING - width;
    }

    if (placement === 'bottom') {
      height = Math.min(IDEAL_H, Math.max(MIN_H, spaceBottom));
      top = triggerRect.top + triggerRect.height + GAP;
      width = Math.min(IDEAL_W, viewportW - PADDING * 2);
      clampHorizontal();
      const beakX = triggerCenterX - left;
      beakS = { top: -24, left: Math.max(12, Math.min(width - 12, beakX)) - 12, transform: 'rotate(0deg)' };

    } else if (placement === 'top') {
      height = Math.min(IDEAL_H, Math.max(MIN_H, spaceTop));
      top = triggerRect.top - GAP - height;
      width = Math.min(IDEAL_W, viewportW - PADDING * 2);
      clampHorizontal();
      const beakX = triggerCenterX - left;
      beakS = { bottom: -24, left: Math.max(12, Math.min(width - 12, beakX)) - 12, transform: 'rotate(180deg)' };

    } else if (placement === 'right') {
      width = Math.min(IDEAL_W, Math.max(MIN_W, spaceRight));
      left = triggerRect.left + triggerRect.width + GAP;
      height = Math.min(IDEAL_H, viewportH - PADDING * 2);
      top = triggerCenterY - (height / 2);
      if (top < PADDING) top = PADDING;
      if (top + height > viewportH - PADDING) top = viewportH - PADDING - height;
      const beakY = triggerCenterY - top;
      beakS = { left: -24, top: Math.max(12, Math.min(height - 12, beakY)) - 12, transform: 'rotate(-90deg)' };

    } else if (placement === 'left') {
      width = Math.min(IDEAL_W, Math.max(MIN_W, spaceLeft));
      left = triggerRect.left - GAP - width;
      height = Math.min(IDEAL_H, viewportH - PADDING * 2);
      top = triggerCenterY - (height / 2);
      if (top < PADDING) top = PADDING;
      if (top + height > viewportH - PADDING) top = viewportH - PADDING - height;
      const beakY = triggerCenterY - top;
      beakS = { right: -24, top: Math.max(12, Math.min(height - 12, beakY)) - 12, transform: 'rotate(90deg)' };
    }

    setChatStyle({
      position: 'fixed',
      top,
      left,
      width,
      height,
      maxHeight: 'none',
      zIndex: 60
    });
    setBeakStyle(beakS);

  }, [isOpen, triggerRect]);

  useEffect(() => {
    if (scrollRef.current) {
        scrollRef.current.scrollTo({
            top: scrollRef.current.scrollHeight,
            behavior: 'smooth' 
        });
    }
  }, [messages, isTyping, isOpen]);

  const handleSend = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!input.trim()) return;

    if (input === '/clear') {
        clearChat();
        setInput('');
        setShowSuggestions(false);
        return;
    }

    sendMessage(input);
    setInput('');
    setShowSuggestions(false);
  };

  const handleCommandClick = (cmd: string) => {
    if (cmd.startsWith('/')) {
        setInput(cmd);
        inputRef.current?.focus();
    } else {
        sendMessage(cmd);
        setInput('');
        setShowSuggestions(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showSuggestions || filteredSuggestions.length === 0) return;

    if (e.key === 'ArrowDown') {
        e.preventDefault();
        setActiveSuggestionIndex(prev => (prev + 1) % filteredSuggestions.length);
    } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setActiveSuggestionIndex(prev => (prev - 1 + filteredSuggestions.length) % filteredSuggestions.length);
    } else if (e.key === 'Enter') {
        if (activeSuggestionIndex >= 0) {
            e.preventDefault();
            handleCommandClick(filteredSuggestions[activeSuggestionIndex]);
        }
    } else if (e.key === 'Escape') {
        setShowSuggestions(false);
    }
  };

  const containerVariants = useMemo(() => {
     if (isMobileLayout) {
        return {
            hidden: { y: "100%", opacity: 0 },
            visible: { 
                y: 0, 
                opacity: 1, 
                transition: { type: "spring" as const, damping: 25, stiffness: 300 } 
            },
            exit: { y: "100%", opacity: 0, transition: { duration: 0.3 } }
        };
     }
     return {
        hidden: { opacity: 0, scale: 0.9 },
        visible: { 
          opacity: 1, 
          scale: 1,
          transition: { type: "spring" as const, duration: 0.4, bounce: 0.2 }
        },
        exit: { opacity: 0, scale: 0.9, transition: { duration: 0.2 } }
     };
  }, [isMobileLayout]);

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      {isOpen && (
        <>
        <div className="fixed inset-0 z-[50] bg-black/20 backdrop-blur-sm" onClick={closeChat} />

        <div className={!isFixed ? "fixed inset-0 z-[60] flex items-center justify-center p-4 pointer-events-none" : ""} >
          <motion.div
            ref={containerRef}
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            style={isFixed ? chatStyle : { pointerEvents: 'auto', width: '100%', maxWidth: '400px', height: '500px' }}
            className={`flex flex-col bg-zinc-950/95 border border-cyan-500/40 rounded-xl shadow-[0_0_80px_-20px_rgba(0,255,255,0.3)] backdrop-blur-xl overflow-visible relative ${!isFixed ? 'pointer-events-auto' : ''}`}
          >
            {isFixed && !isMobileLayout && (
                <svg 
                    className="absolute w-6 h-6 text-cyan-500/40 fill-zinc-950 z-50 pointer-events-none drop-shadow-[0_0_5px_rgba(0,255,255,0.5)]"
                    style={beakStyle}
                    viewBox="0 0 24 24"
                >
                    <path d="M12 0L24 24H0L12 0Z" fill="currentColor" stroke="rgb(6,182,212)" strokeWidth="1" />
                    <path d="M12 2L22 22H2L12 2Z" fill="#09090b" stroke="none" /> 
                </svg>
            )}

            <div className="absolute inset-0 bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] bg-[length:100%_2px,3px_100%] pointer-events-none z-10 opacity-20 rounded-xl overflow-hidden"></div>

            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-cyan-500/20 bg-zinc-900/50 rounded-t-xl shrink-0 cursor-move">
              <div className="flex items-center gap-3">
                <div className="relative w-8 h-8 flex items-center justify-center">
                    <div className="absolute inset-0 border border-cyan-500/50 rounded-full animate-[spin_4s_linear_infinite]" />
                    <img 
                      src="/logo.png" 
                      alt="Logo"
                      className="w-6 h-6 object-contain relative z-10"
                      onError={(e) => { e.currentTarget.style.display = 'none'; }}
                    />
                    <Bot className="absolute w-4 h-4 text-cyan-500 z-0" />
                </div>
                <div>
                   <h3 className="text-xs font-mono font-bold text-cyan-400 tracking-widest uppercase flex items-center gap-2">
                       AI 智控王 <span className="text-zinc-500 text-[10px]">// CORE</span>
                   </h3>
                   <div className="flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></span>
                      <span className="text-[10px] text-zinc-500 font-mono">NEURAL CONNECTION</span>
                   </div>
                </div>
              </div>
              <button 
                onClick={closeChat}
                className="p-2 hover:bg-white/10 rounded text-zinc-400 hover:text-white transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Chat Body */}
            <div 
              ref={scrollRef}
              className="flex-1 overflow-y-auto p-4 space-y-4 font-mono text-sm custom-scrollbar bg-black/40 scroll-smooth"
            >
              <AnimatePresence initial={false}>
              {messages.map((msg) => (
                <ChatMessageItem key={msg.id} msg={msg} />
              ))}
              </AnimatePresence>

              {isTyping && (
                <motion.div 
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 5 }}
                  className="flex justify-start w-full"
                >
                   <div className="flex items-center gap-3 px-3 py-2 bg-zinc-900/50 border-l-2 border-cyan-500 rounded-r-md">
                      <div className="flex items-end gap-0.5 h-3">
                        {[...Array(5)].map((_, i) => (
                           <motion.div 
                             key={i}
                             className="w-1 bg-cyan-500"
                             animate={{ 
                               height: ["20%", "100%", "20%"],
                               opacity: [0.3, 1, 0.3]
                             }}
                             transition={{
                               duration: 0.8,
                               repeat: Infinity,
                               delay: i * 0.1,
                               ease: "linear"
                             }}
                           />
                        ))}
                      </div>
                      <span className="text-xs font-mono text-cyan-400 tracking-wider">
                        PROCESSING_REQUEST<span className="animate-pulse">_</span>
                      </span>
                   </div>
                </motion.div>
              )}
            </div>

            {/* Suggestions Overlay - Filtered & Keyboard Navigable */}
            <AnimatePresence>
                {showSuggestions && filteredSuggestions.length > 0 && (
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 10 }}
                        className="absolute bottom-[60px] left-4 right-4 bg-zinc-900/95 border border-cyan-500/30 rounded-lg shadow-xl backdrop-blur-md overflow-hidden z-20"
                    >
                        <div className="flex items-center gap-2 px-3 py-2 border-b border-white/5 bg-white/5">
                            <Sparkles className="w-3 h-3 text-cyan-400" />
                            <span className="text-[10px] text-zinc-400 font-mono uppercase">Suggested Actions {input && '(Filtered)'}</span>
                        </div>
                        <div className="max-h-32 overflow-y-auto custom-scrollbar p-1">
                            {filteredSuggestions.map((cmd, idx) => (
                                <button
                                    key={idx}
                                    onClick={() => handleCommandClick(cmd)}
                                    className={`w-full flex items-center justify-between px-3 py-2 rounded border transition-all group text-left ${
                                        idx === activeSuggestionIndex 
                                            ? 'bg-cyan-500/20 border-cyan-500/40 text-cyan-300' 
                                            : 'hover:bg-cyan-500/10 hover:border-cyan-500/20 border-transparent'
                                    }`}
                                >
                                    <div className="flex items-center gap-2">
                                        {cmd.startsWith('/') && <Terminal className="w-3 h-3 text-cyan-500/50" />}
                                        <span className={`font-mono text-xs font-bold ${idx === activeSuggestionIndex ? 'text-cyan-200' : 'text-cyan-400'}`}>
                                            {cmd}
                                        </span>
                                    </div>
                                    <ChevronRight className={`w-3 h-3 transition-opacity ${
                                        idx === activeSuggestionIndex ? 'opacity-100 text-cyan-400' : 'opacity-0 group-hover:opacity-100 text-zinc-600'
                                    }`} />
                                </button>
                            ))}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Input Area */}
            <div className="p-3 bg-zinc-900/80 border-t border-cyan-500/20 rounded-b-xl shrink-0 relative z-30">
               <form onSubmit={handleSend} className="relative flex items-center gap-2">
                  <div className="absolute left-3 top-1/2 -translate-y-1/2 flex items-center gap-1">
                    <Activity className="w-4 h-4 text-cyan-500/50" />
                    {input === '' && <span className="w-1.5 h-4 bg-cyan-500/50 animate-pulse ml-0.5" />}
                  </div>
                  <input
                    ref={inputRef}
                    type="text"
                    value={input}
                    onFocus={() => setShowSuggestions(true)}
                    onBlur={() => setTimeout(() => setShowSuggestions(false), 200)} 
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="请输入指令..."
                    className="w-full bg-black/50 border border-white/10 rounded-md py-2.5 pl-10 pr-10 text-zinc-200 placeholder:text-zinc-600 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/20 font-mono text-sm transition-all"
                    autoFocus
                    autoComplete="off"
                  />
                  <button 
                    type="submit"
                    disabled={!input.trim() || isTyping}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 bg-cyan-500/10 rounded hover:bg-cyan-500/20 text-cyan-500 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                  >
                    <Send className="w-3.5 h-3.5" />
                  </button>
               </form>
            </div>
          </motion.div>
        </div>
        </>
      )}
    </AnimatePresence>
  );
};
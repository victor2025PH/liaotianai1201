import React, { useEffect, useState, useRef } from 'react';
import { motion, useSpring, useVelocity, useAnimationFrame, useTransform, useScroll, useMotionTemplate, useMotionValue, AnimatePresence } from 'framer-motion';
import { useAIChat } from '../contexts/AIChatContext';
import { Sparkles, Activity, Radio, Zap } from 'lucide-react';

// --- Visual Assets ---

const NeuralNeck = ({ active, color }: { active: boolean; color: string }) => (
  <motion.div 
    className="absolute left-1/2 top-[25%] -translate-x-1/2 w-3 h-10 z-10 overflow-hidden pointer-events-none"
    animate={{ opacity: 1, height: 28 }} // Always active now
    transition={{ duration: 0.4 }}
  >
     <div className="w-full h-full flex flex-col items-center justify-center">
        <div 
            className="w-[1px] h-full transition-colors duration-1000" 
            style={{ backgroundColor: `${color}4D`, boxShadow: `0 0 5px ${color}` }} 
        />
     </div>
  </motion.div>
);

// New: Holographic Projection for "News/Updates"
const NewsHologram = ({ active, text, color }: { active: boolean; text: string; color: string }) => (
    <AnimatePresence>
        {active && (
            <motion.div
                className="absolute bottom-[105%] left-1/2 -translate-x-1/2 w-48 z-50 pointer-events-none"
                initial={{ opacity: 0, scale: 0.8, y: 10, rotateX: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0, rotateX: 0 }}
                exit={{ opacity: 0, scale: 0.8, y: 5 }}
            >
                <div 
                    className="bg-black/80 border backdrop-blur-md rounded-lg p-3 relative overflow-hidden"
                    style={{ borderColor: `${color}60`, boxShadow: `0 0 15px ${color}20` }}
                >
                    {/* Scanline effect */}
                    <div className="absolute inset-0 bg-[linear-gradient(rgba(0,0,0,0)_50%,rgba(0,0,0,0.2)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] bg-[length:100%_2px,3px_100%] pointer-events-none opacity-50"></div>
                    
                    <div className="flex items-center gap-2 mb-1 border-b border-white/10 pb-1">
                        <Activity className="w-3 h-3 animate-pulse" style={{ color }} />
                        <span className="text-[10px] font-mono font-bold tracking-wider text-zinc-300">SYSTEM_FEED</span>
                    </div>
                    <div className="text-xs text-white font-sans leading-tight relative z-10">
                        {text}
                    </div>
                </div>
                {/* Holographic Beam */}
                <div 
                    className="absolute top-full left-1/2 -translate-x-1/2 w-8 h-8 opacity-50 blur-md"
                    style={{ background: `conic-gradient(from 180deg at 50% 0%, transparent 45%, ${color} 50%, transparent 55%)` }}
                />
            </motion.div>
        )}
    </AnimatePresence>
);

const EveArm = ({ isLeft }: { isLeft: boolean }) => (
    <svg width="18" height="64" viewBox="0 0 18 64" fill="none" className="drop-shadow-sm" style={{ transform: isLeft ? 'scaleX(1)' : 'scaleX(-1)' }}>
        <defs>
            <linearGradient id="armGrad" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="#ffffff" />
                <stop offset="40%" stopColor="#eef2ff" />
                <stop offset="100%" stopColor="#dbeafe" />
            </linearGradient>
        </defs>
        <path d="M16 2C16 2 4 10 4 28C4 50 12 60 16 62C17 62.5 18 60 18 56C18 56 18 10 16 2Z" fill="url(#armGrad)" />
        <path d="M16 2C16 2 4 10 4 28C4 50 12 60 16 62" stroke="white" strokeWidth="0.5" strokeOpacity="0.8" fill="none" />
        <path d="M16 2C16 2 4 10 4 28C4 50 12 60 16 62C17 62.5 18 60 18 56C18 56 18 10 16 2Z" stroke="rgba(0,0,0,0.05)" strokeWidth="0.5" />
    </svg>
);

const DigitalEye = ({ expression, color }: { expression: 'normal' | 'happy' | 'blink' | 'focused' | 'scanning' | 'scared' | 'wink'; color: string }) => {
    const variants = {
        normal: { scaleY: 1, scaleX: 1, borderRadius: "50%", height: "16px" },
        blink: { scaleY: 0.1, scaleX: 1.1, borderRadius: "50%", height: "16px" },
        happy: { scaleY: 0.6, scaleX: 1.1, borderRadius: "50% 50% 20% 20%", height: "16px" }, // Upside down U
        focused: { scaleY: 0.7, scaleX: 0.9, borderRadius: "30%", height: "14px" }, 
        scanning: { scaleY: 1.1, scaleX: 0.8, borderRadius: "50%", height: "18px" },
        scared: { scaleY: 1.3, scaleX: 0.7, borderRadius: "40%", height: "20px" },
        wink: { scaleY: 0.1, scaleX: 1.1, borderRadius: "50%", height: "16px" } // Only one eye usually winks, handled by parent
    };

    return (
        <motion.div 
            className="relative w-6 bg-[#001020] overflow-hidden transition-colors duration-1000"
            style={{ 
                boxShadow: `0 0 5px ${color}80`, 
                border: `1px solid ${color}40`,
            }}
            animate={variants[expression === 'wink' ? 'blink' : expression]} // Map wink to blink shape for the closed eye
            transition={{ type: "spring", stiffness: 300, damping: 20 }}
        >
             {/* Happy Eye Mask */}
             <motion.div 
                className="absolute inset-0 bg-black"
                initial={{ opacity: 0 }}
                animate={{ opacity: expression === 'happy' ? 1 : 0 }}
                style={{ clipPath: 'polygon(0% 50%, 100% 50%, 100% 100%, 0% 100%)' }}
             />
             
             {/* Scanline for Scanning Mode */}
             {expression === 'scanning' && (
                 <motion.div 
                    className="absolute inset-0 bg-white/50 h-[2px]"
                    animate={{ top: ['0%', '100%', '0%'] }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                 />
             )}

            <div className="absolute inset-0 flex flex-col justify-center gap-[1px] opacity-90">
                {[...Array(5)].map((_, i) => (
                    <div 
                        key={i} 
                        className="w-full h-[2px] transition-colors duration-1000"
                        style={{ 
                            backgroundColor: color, 
                            boxShadow: `0 0 2px ${color}`,
                            opacity: 1 - Math.abs(2 - i) * 0.25
                        }} 
                    />
                ))}
            </div>
            <div 
                className="absolute inset-0 blur-sm transition-colors duration-1000" 
                style={{ backgroundColor: `${color}40` }} 
            />
        </motion.div>
    );
};

// Types for robot behavior
type BotMode = 'flying' | 'falling' | 'idle_base' | 'idle_wave' | 'idle_dance' | 'idle_scan' | 'idle_news' | 'idle_spin';

const EveBot: React.FC<{ 
    mode: BotMode;
    flightAngle: number;
    scrollTilt: number;
    velocity: number;
    isHovered: boolean;
    newsText: string;
}> = ({ mode, flightAngle, scrollTilt, velocity, isHovered, newsText }) => {
    
    const [eyeExpression, setEyeExpression] = useState<'normal' | 'happy' | 'blink' | 'focused' | 'scanning' | 'scared'>('normal');
    const [eyeColor, setEyeColor] = useState('#00FFFF');
    const [spinRotation, setSpinRotation] = useState(0);

    // Color Cycling
    useEffect(() => {
        const colors = ['#00FFFF', '#A855F7', '#22C55E', '#F97316', '#3B82F6'];
        let colorIndex = 0;
        const interval = setInterval(() => {
            colorIndex = (colorIndex + 1) % colors.length;
            setEyeColor(colors[colorIndex]);
        }, 4000);
        return () => clearInterval(interval);
    }, []);

    // Logic to determine Eye Expression based on Mode
    useEffect(() => {
        // Prioritize hover happiness
        if (isHovered) { setEyeExpression('happy'); return; }

        if (mode === 'falling') { setEyeExpression('scared'); return; }
        if (mode === 'flying') { setEyeExpression('focused'); return; }
        if (mode === 'idle_scan') { setEyeExpression('scanning'); return; }
        if (mode === 'idle_wave') { setEyeExpression('happy'); return; }
        if (mode === 'idle_dance') { setEyeExpression('happy'); return; }
        if (mode === 'idle_news') { setEyeExpression('focused'); return; }
        
        // Random Blinking in base idle
        const blinkLoop = () => {
            if (mode === 'idle_base' && !isHovered) {
                setEyeExpression('blink');
                setTimeout(() => setEyeExpression('normal'), 150);
            }
            setTimeout(blinkLoop, 2000 + Math.random() * 3000);
        };
        const timer = setTimeout(blinkLoop, 2000);
        return () => clearTimeout(timer);
    }, [mode, isHovered]);

    // Spin Logic
    useEffect(() => {
        if (mode === 'idle_spin') {
            setSpinRotation(prev => prev + 360);
        }
    }, [mode]);

    // --- Animation Variants ---

    const bodyVariants = {
        idle_base: { 
            y: [0, -8, 0], 
            rotate: 0,
            transition: { y: { repeat: Infinity, duration: 2.5, ease: "easeInOut" as const } } 
        },
        idle_scan: {
            y: -5,
            rotate: [0, -5, 5, 0],
            transition: { rotate: { duration: 2, ease: "easeInOut" as const } }
        },
        idle_wave: {
            y: -5,
            rotate: -2,
        },
        idle_dance: {
            y: [0, -15, 0],
            rotate: [-3, 3, -3],
            transition: { 
                y: { repeat: Infinity, duration: 0.4, ease: "easeOut" as const },
                rotate: { repeat: Infinity, duration: 0.8, ease: "linear" as const }
            }
        },
        idle_news: {
            y: 0,
            rotate: 0,
        },
        idle_spin: {
            rotateY: 360,
            transition: { duration: 0.8, ease: "easeInOut" as const }
        },
        flying: { rotate: flightAngle, y: -20 },
        falling: { rotate: -15, y: 30 },
    };

    const leftArmVariants = {
        idle_base: { x: -6, y: 10, rotate: 5 },
        idle_scan: { x: -6, y: 10, rotate: 5 },
        idle_wave: { x: -6, y: 10, rotate: 5 },
        idle_dance: { 
            x: -12, y: 5, 
            rotate: [0, 45, 0],
            transition: { repeat: Infinity, duration: 0.4 } 
        },
        idle_news: { x: -8, y: 8, rotate: 10 },
        flying: { x: -12, y: 25, rotate: 35 },
        falling: { x: -25, y: -25, rotate: 150 }, // Flailing arms up
    };

    const rightArmVariants = {
        idle_base: { x: 6, y: 10, rotate: -5 },
        idle_scan: { x: 6, y: 10, rotate: -5 },
        idle_wave: { 
            x: 6, y: 10, // Adjusted to keep shoulder attached to body (previously x:15, y:-15)
            rotate: [-140, -110, -140], // Natural wave angle
            transition: { repeat: Infinity, duration: 1, ease: "easeInOut" as const }
        },
        idle_dance: { 
            x: 12, y: 5, 
            rotate: [0, -45, 0],
            transition: { repeat: Infinity, duration: 0.4, delay: 0.2 } 
        },
        idle_news: { x: 8, y: 8, rotate: -10 },
        flying: { x: 12, y: 25, rotate: -35 },
        falling: { x: 25, y: -25, rotate: -150 }, // Flailing arms up
    };

    return (
        <motion.div 
            className="relative w-32 h-44 flex flex-col items-center justify-center preserve-3d"
            style={{ rotateX: scrollTilt }}
            animate={{ rotateY: spinRotation }}
            transition={{ rotateY: { duration: 1, ease: "backOut" } }}
        >
            <motion.div 
                 className="relative w-full h-full flex flex-col items-center justify-center preserve-3d"
                 variants={bodyVariants}
                 animate={mode === 'idle_spin' ? undefined : mode} // Spin is handled by parent rotation
                 transition={{ type: "spring", stiffness: 100, damping: 20 }}
            >
                {/* Hologram */}
                <NewsHologram active={mode === 'idle_news'} text={newsText} color={eyeColor} />

                {/* --- HEAD --- */}
                <motion.div 
                    className="relative z-30 w-[4.4rem] h-[3.2rem] bg-white rounded-[50%_50%_45%_45%] shadow-[inset_0_-2px_6px_rgba(0,0,0,0.15),0_5px_15px_rgba(0,0,0,0.1)] overflow-hidden flex items-center justify-center"
                    style={{ background: 'radial-gradient(circle at 50% 10%, #ffffff 0%, #eef2ff 60%, #dbeafe 100%)' }}
                    animate={{
                        y: mode === 'idle_dance' ? -2 : -8,
                    }}
                >
                    <div className="absolute top-1 left-1/4 w-1/2 h-1/2 bg-white opacity-60 rounded-full blur-[2px]" />
                    <div className="w-[88%] h-[75%] bg-black rounded-[45%_45%_50%_50%] flex items-center justify-center gap-3 relative shadow-[inset_0_0_10px_rgba(255,255,255,0.15)] overflow-hidden border border-zinc-800/50 mt-1">
                        <div className="flex gap-3">
                            <DigitalEye expression={eyeExpression} color={eyeColor} />
                            <DigitalEye expression={eyeExpression} color={eyeColor} />
                        </div>
                    </div>
                </motion.div>

                {/* --- NECK --- */}
                <NeuralNeck active={true} color={eyeColor} />

                {/* --- BODY --- */}
                <div className="relative z-20 w-[4rem] h-[5.5rem] mt-[-10px]">
                    <div 
                        className="w-full h-full bg-white relative overflow-hidden"
                        style={{ 
                            background: 'radial-gradient(circle at 30% 50%, #ffffff 0%, #f0f9ff 50%, #dbeafe 100%',
                            borderRadius: '30% 30% 50% 50% / 20% 20% 80% 80%', 
                            boxShadow: 'inset -5px -5px 15px rgba(0,0,0,0.05), inset 5px 5px 15px rgba(255,255,255,1), 0 10px 25px rgba(0,0,0,0.1)'
                        }}
                    >
                        {/* Body Details */}
                        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[90%] h-5 bg-gradient-to-b from-[#cbd5e1] to-transparent rounded-b-full opacity-40 blur-[1px]" />
                        <div className="absolute top-[-2px] left-1/2 -translate-x-1/2 w-[80%] h-3 bg-zinc-200/50 rounded-b-full blur-[2px]" />
                        
                        {/* Center Core */}
                        <div className={`absolute top-[45%] left-1/2 -translate-x-1/2 w-8 h-8 flex items-center justify-center transition-opacity duration-700 opacity-100`}>
                            <div 
                                className="w-2 h-2 rounded-full animate-pulse transition-colors duration-1000"
                                style={{ backgroundColor: eyeColor, boxShadow: `0 0 10px ${eyeColor}` }}
                            />
                            <div className="absolute w-full h-[1px] bg-black/5 top-1/2 -translate-y-1/2" />
                            <div className="absolute h-full w-[1px] bg-black/5 left-1/2 -translate-x-1/2" />
                        </div>
                    </div>
                </div>

                {/* --- ARMS --- */}
                <motion.div className="absolute left-[22px] top-[46px] z-10 origin-[16px_8px]" variants={leftArmVariants} animate={mode}>
                    <EveArm isLeft={true} />
                </motion.div>

                <motion.div className="absolute right-[22px] top-[46px] z-10 origin-[2px_8px]" variants={rightArmVariants} animate={mode}>
                    <EveArm isLeft={false} />
                </motion.div>

                {/* --- THRUSTER --- */}
                <motion.div 
                    className="absolute top-[88%] left-[49%] -translate-x-1/2 -z-10"
                    animate={{ 
                        opacity: (mode === 'flying' || mode === 'idle_dance') ? 0.8 : 0.4, 
                        scaleY: (mode === 'flying') ? 1.5 : 0.8
                    }}
                >
                    <div 
                        className="w-6 h-12 rounded-full blur-[6px] transition-colors duration-1000" 
                        style={{ background: `linear-gradient(to top, transparent, ${eyeColor}, white)` }}
                    />
                </motion.div>
            </motion.div>
        </motion.div>
    );
};

// --- News Data Snippets (Localized) ---
const NEWS_SNIPPETS = [
    "正在优化神经权重...",
    "扫描全球流量节点...",
    "检测到加密市场波动...",
    "已集成 Llama-3 模型...",
    "Telegram API 更新检测...",
    "正在压缩系统日志...",
    "系统安全等级：绝密",
    "正在分析用户情绪...",
    "获取每日股市趋势...",
    "流量矩阵运行中..."
];

export const AISprite: React.FC = () => {
    const { openChat } = useAIChat();
    const { scrollY } = useScroll();
    
    // Main Mode State
    const [mode, setMode] = useState<BotMode>('idle_base');
    const [newsText, setNewsText] = useState('');
    
    const [isHovered, setIsHovered] = useState(false);
    // Use ref to access latest hover state in useAnimationFrame closure
    const isHoveredRef = useRef(false);
    
    const [zIndex, setZIndex] = useState(50); 
    const [velocity, setVelocity] = useState(0);
    const [tilt, setTilt] = useState(0);
    const [flightAngle, setFlightAngle] = useState(0); 

    const springScrollVelocity = useVelocity(scrollY);
    
    // Interaction Physics
    const clickX = useSpring(0, { stiffness: 60, damping: 15 });
    const clickY = useSpring(0, { stiffness: 60, damping: 15 });
    const flightVelX = useVelocity(clickX);
    const flightVelY = useVelocity(clickY);

    // Collision avoidance offset
    const avoidX = useSpring(0, { stiffness: 100, damping: 20 });
    const avoidY = useSpring(0, { stiffness: 100, damping: 20 });

    // Increase the drag distance to make "falling" more apparent
    const rawDragY = useTransform(springScrollVelocity, [-3000, 3000], [-150, 150]);
    const smoothDragY = useSpring(rawDragY, { stiffness: 100, damping: 20 });
    
    const combinedY = useMotionTemplate`calc(${clickY}px + ${smoothDragY}px + ${avoidY}px)`;
    const combinedX = useMotionTemplate`calc(${clickX}px + ${avoidX}px)`;

    // --- Lively Idle Loop ---
    useEffect(() => {
        const loop = setInterval(() => {
            // Don't interrupt physics or hover interaction
            if (velocity > 100 || Math.abs(flightVelX.get()) > 10 || isHoveredRef.current) return;

            const rand = Math.random();
            let nextMode: BotMode = 'idle_base';
            
            if (rand > 0.95) nextMode = 'idle_spin';
            else if (rand > 0.90) nextMode = 'idle_dance';
            else if (rand > 0.80) nextMode = 'idle_wave';
            else if (rand > 0.65) {
                nextMode = 'idle_news';
                setNewsText(NEWS_SNIPPETS[Math.floor(Math.random() * NEWS_SNIPPETS.length)]);
            }
            else if (rand > 0.50) nextMode = 'idle_scan';
            else nextMode = 'idle_base';

            setMode(nextMode);

            if (nextMode !== 'idle_base') {
                const duration = nextMode === 'idle_dance' ? 4000 : 
                                 nextMode === 'idle_news' ? 5000 : 
                                 nextMode === 'idle_spin' ? 1500 : 3000;
                
                setTimeout(() => {
                    setMode(prev => {
                        // Only reset if we haven't started moving in the meantime
                        if (prev === nextMode) return 'idle_base';
                        return prev;
                    });
                }, duration);
            }

        }, 6000); 

        return () => clearInterval(loop);
    }, [velocity]); 

    // --- Collision Detection Helper ---
    const checkCollision = (robotX: number, robotY: number, robotWidth: number = 128, robotHeight: number = 176): { hasCollision: boolean; adjustX: number; adjustY: number } => {
        const avoidElements = document.querySelectorAll('[data-robot-avoid="true"]');
        let hasCollision = false;
        let adjustX = 0;
        let adjustY = 0;
        const padding = 20; // 额外的安全距离

        avoidElements.forEach((element) => {
            const rect = element.getBoundingClientRect();
            const elementCenterX = rect.left + rect.width / 2;
            const elementCenterY = rect.top + rect.height / 2;
            
            // 机器人中心位置
            const robotCenterX = robotX + robotWidth / 2;
            const robotCenterY = robotY + robotHeight / 2;
            
            // 计算距离
            const distanceX = robotCenterX - elementCenterX;
            const distanceY = robotCenterY - elementCenterY;
            const distance = Math.sqrt(distanceX * distanceX + distanceY * distanceY);
            
            // 碰撞检测：机器人边界 + padding 与元素边界重叠
            const minDistance = (robotWidth / 2 + rect.width / 2 + padding);
            
            if (distance < minDistance) {
                hasCollision = true;
                // 计算避让方向（远离元素）
                const angle = Math.atan2(distanceY, distanceX);
                const pushDistance = minDistance - distance + 10; // 额外推离距离
                adjustX += Math.cos(angle) * pushDistance;
                adjustY += Math.sin(angle) * pushDistance;
            }
        });

        return { hasCollision, adjustX, adjustY };
    };

    // --- Global Click & Physics Loop ---
    useEffect(() => {
        const handleClick = (e: MouseEvent) => {
            const target = e.target as HTMLElement;
            if (target.closest('.ai-sprite-container') || target.closest('.ai-chat-window')) return;
            
            // 如果点击的是需要避开的元素，不移动机器人
            if (target.closest('[data-robot-avoid="true"]')) {
                return;
            }

            const robotCenterX = window.innerWidth - 32 - 64; 
            const robotCenterY = window.innerHeight - 32 - 88; 
            const offsetX = e.clientX - robotCenterX;
            const offsetY = e.clientY - robotCenterY;
            clickX.set(offsetX);
            clickY.set(offsetY);
        };
        window.addEventListener('click', handleClick);
        return () => window.removeEventListener('click', handleClick);
    }, [clickX, clickY]);

    useAnimationFrame(() => {
        const v = springScrollVelocity.get();
        const fvx = flightVelX.get();
        const fvy = flightVelY.get();
        const flightSpeed = Math.sqrt(fvx*fvx + fvy*fvy);

        // Tilt Calculation: 
        // When scrolling down (v > 0), robot falls -> Tilt forward (positive x)
        // When scrolling up (v < 0), robot flies up -> Tilt backward (negative x)
        const t = Math.max(Math.min(v * 0.05, 30), -30);
        
        if (Math.abs(v - velocity) > 10 || Math.abs(t - tilt) > 1) {
            setVelocity(v);
            setTilt(t);
        }
        
        // Flight Angle
        if (flightSpeed > 50) {
            const lean = Math.max(Math.min(fvx * 0.05, 30), -30);
            setFlightAngle(lean);
        } else {
             setFlightAngle(prev => prev * 0.9);
        }

        // Collision Detection and Avoidance
        if (robotRef.current) {
            const robotRect = robotRef.current.getBoundingClientRect();
            const robotX = robotRect.left;
            const robotY = robotRect.top;
            
            const collision = checkCollision(robotX, robotY);
            
            if (collision.hasCollision) {
                // 应用避让偏移
                avoidX.set(collision.adjustX);
                avoidY.set(collision.adjustY);
            } else {
                // 逐渐回到原位置
                avoidX.set(0);
                avoidY.set(0);
            }
        }

        // Mode Logic: Physics vs Interaction
        const SCROLL_ACTION_THRESHOLD = 500; 
        const FLIGHT_THRESHOLD = 50; 
        
        if (v > SCROLL_ACTION_THRESHOLD) {
             // Falling due to scroll down
             if (mode !== 'falling') setMode('falling');
        } else if (v < -SCROLL_ACTION_THRESHOLD) {
             // Flying up due to scroll up
             if (mode !== 'flying') setMode('flying');
        } else if (flightSpeed > FLIGHT_THRESHOLD) {
             if (mode !== 'flying') setMode('flying');
        } else {
            // Not in extreme physics
            if (isHoveredRef.current) {
                // If hovering, force wave mode unless we are clicking away
                if (mode !== 'idle_wave') setMode('idle_wave');
            } else {
                // Recovery from physics modes to base
                if (mode === 'falling' || mode === 'flying') {
                    setMode('idle_base');
                }
            }
        }

        // Z-Index
        if (isHovered && zIndex !== 100) setZIndex(100);
        else if (!isHovered && zIndex === 100) setZIndex(50);
    });

    const robotRef = useRef<HTMLDivElement>(null);

    return (
        <motion.div 
            ref={robotRef}
            className="fixed bottom-8 right-8 hidden md:block perspective-[1000px] pointer-events-none ai-sprite-container"
            style={{ 
                zIndex: zIndex,
                x: combinedX,
                y: combinedY 
            }}
        >
            <motion.div
                className="cursor-pointer pointer-events-auto"
                onMouseEnter={() => { setIsHovered(true); isHoveredRef.current = true; }}
                onMouseLeave={() => { setIsHovered(false); isHoveredRef.current = false; }}
                onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    // Default Context: Product Recommendation
                    let triggerPrompt = "用户点击了机器人。你需要扮演产品顾问。首先介绍热门产品，然后询问用户需求（流量/设备/AI），逐步引导用户。";
                    
                    const hotProducts = [
                        "1. 🚀 WhatsApp 官方 API (防封号)",
                        "2. 📱 云手机集群 (万人群控)",
                        "3. 🗣️ AI 语音克隆 (拟真度99%)",
                        "4. 🕸️ Telegram 获客矩阵"
                    ];
                    
                    let aiMsg = `系统核心已连接。我是 EVE。\n\n为您检索到本周 **热门黑科技**：\n\n${hotProducts.join('\n')}\n\n请问您的核心目标是什么？`;
                    let suggestions = "我要搞流量|我要群控设备|降低人工成本";

                    // Contextual overrides
                    if (mode === 'idle_news') {
                        triggerPrompt = `用户对新闻 "${newsText}" 感兴趣，并希望了解相关产品方案。`;
                        aiMsg = `正在分析资讯流：${newsText}\n\n基于此趋势，我为您推荐以下解决方案：\n\n${hotProducts[0]}\n${hotProducts[3]}\n\n您想深入了解哪一个？`;
                        suggestions = "了解 WhatsApp|了解 Telegram|其他方案";
                    } else if (mode === 'idle_dance') {
                         triggerPrompt = "用户在机器人跳舞时点击。以轻松幽默的口吻推荐转化率最高的产品。";
                         aiMsg = "系统心情指数：100% ⚡\n\n趁我心情好，给您透露点内部数据。\n目前 **WhatsApp API** 和 **云手机** 的转化率最高。\n\n您想看实测数据吗？";
                         suggestions = "看转化数据|推荐适合我的|无需推荐";
                    }

                    const fullMsg = `${aiMsg}|||${suggestions}`;
                    openChat(triggerPrompt, fullMsg, e.currentTarget as HTMLElement);
                }}
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
                initial={{ y: 200, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ type: "spring", stiffness: 50, damping: 20, delay: 0.5 }}
            >
                <EveBot 
                    mode={mode} 
                    flightAngle={flightAngle} 
                    scrollTilt={tilt} 
                    velocity={velocity}
                    isHovered={isHovered}
                    newsText={newsText}
                />
            </motion.div>
        </motion.div>
    );
};
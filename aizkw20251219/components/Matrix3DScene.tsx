import React, { useEffect, useRef, useMemo, useState } from 'react';
import { motion, useSpring, useMotionValue, useTransform, AnimatePresence, useAnimationFrame } from 'framer-motion';
import { MessageCircle, Send, CreditCard, Cpu, Activity, Globe, Lock, ShieldCheck, Zap } from 'lucide-react';

// --- Types & Configuration ---

type AppType = 'wechat' | 'telegram' | 'whatsapp' | 'alipay' | 'system';

interface IDeviceNode {
  id: number;
  app: AppType;
  // Spherical Coordinates
  phi: number;
  theta: number;
  // Metadata
  countryCode?: string;
}

const APP_CONFIG: Record<AppType, { label: string; color: string; icon: any }> = {
  wechat: { label: 'WeChat', color: '#07c160', icon: MessageCircle },
  telegram: { label: 'Telegram', color: '#229ED9', icon: Send },
  whatsapp: { label: 'WhatsApp', color: '#25D366', icon: MessageCircle },
  alipay: { label: 'Alipay', color: '#1677FF', icon: CreditCard },
  system: { label: 'SYS_CORE', color: '#00FFFF', icon: Cpu },
};

const CHAT_LOGS: Record<AppType, string[]> = {
  wechat: ["User: Pricing?", "Bot: Sent PDF", "Sys: Friend req acc", "Pay: +8800 CNY", "Grp: Ad removed", "Mmt: Like task done"],
  telegram: ["Bot: User joined", "Sys: Fwd 50 msgs", "Alert: Kw 'Price'", "Bot: Auto-reply", "Admin: W/D appr", "Sys: Burst active"],
  whatsapp: ["Msg: Hello info?", "Bot: Sent Cat V2", "Sys: Num verified", "Broadcast: 10k sent", "Status: Online", "Lead: High Prio"],
  alipay: ["Notif: Success", "Bal: +12.5k", "Risk: Normal", "Sys: Auto-wd", "Order: New merch", "Flow: 1.5M Daily"],
  system: ["Kernel: ACK", "Net: 2ms", "Sec: Firewall", "DB: Syncing", "CPU: 45%", "Proxy: Rotated"]
};

// --- Part 1: Background Elements ---

const GlobeWireframe = () => {
  return (
    <div className="absolute inset-0 pointer-events-none flex items-center justify-center preserve-3d">
      {/* Core Glow */}
      <div className="absolute w-[300px] h-[300px] bg-cyan-500/5 rounded-full blur-2xl" />
      
      {/* Outer Ring */}
      <div className="absolute w-[450px] h-[450px] border border-cyan-500/10 rounded-full animate-[spin_60s_linear_infinite]" />
      <div className="absolute w-[440px] h-[440px] border border-dashed border-cyan-500/10 rounded-full animate-[spin_40s_linear_infinite_reverse]" />

      {/* Sphere Wireframe Rings (CSS 3D Rotated) */}
      <div className="absolute w-[400px] h-[400px] rounded-full border border-cyan-500/20 shadow-[0_0_15px_rgba(0,255,255,0.1)] preserve-3d" style={{ transform: 'rotateX(90deg)' }} />
      <div className="absolute w-[400px] h-[400px] rounded-full border border-cyan-500/20 preserve-3d" style={{ transform: 'rotateY(90deg)' }} />
      <div className="absolute w-[400px] h-[400px] rounded-full border border-white/5 preserve-3d" />
      
      {/* Diagonal Rings */}
      <div className="absolute w-[398px] h-[398px] rounded-full border border-cyan-500/10 preserve-3d" style={{ transform: 'rotateX(45deg)' }} />
      <div className="absolute w-[398px] h-[398px] rounded-full border border-cyan-500/10 preserve-3d" style={{ transform: 'rotateX(-45deg)' }} />
    </div>
  );
};

// --- Part 2: Chat Popup (Optimized) ---
const ChatWindow = ({ app }: { app: AppType }) => {
    const [logs, setLogs] = useState<string[]>(CHAT_LOGS[app].slice(0, 3));
    
    useEffect(() => {
        const interval = setInterval(() => {
            setLogs(prev => {
                const nextMsg = CHAT_LOGS[app][Math.floor(Math.random() * CHAT_LOGS[app].length)];
                return [...prev.slice(1), nextMsg];
            });
        }, 1500);
        return () => clearInterval(interval);
    }, [app]);

    return (
        <div className="flex flex-col gap-1 w-full h-full p-2 overflow-hidden font-mono bg-black/60">
            {logs.map((log, i) => (
                <div key={i} className="flex items-center gap-2 text-[9px] text-zinc-300 border-l border-cyan-500/30 pl-2 py-0.5 animate-fade-in-up">
                    <span className="text-cyan-500/80 font-bold">{'>'}</span>
                    <span className="truncate opacity-90">{log}</span>
                </div>
            ))}
        </div>
    )
}

// --- Part 3: The Globe Point (Node) ---
const GlobeNode: React.FC<{ 
  node: IDeviceNode; 
  radius: number;
  rotation: { x: number, y: number }; // Current rotation of the globe container
  isActive: boolean;
  onSelect: () => void;
}> = ({ node, radius, rotation, isActive, onSelect }) => {
    const config = APP_CONFIG[node.app];
    const Icon = config.icon;

    // Convert Spherical (phi, theta) to Cartesian (x, y, z)
    // phi: polar angle (from y axis), theta: azimuthal angle (from z axis)
    const x = radius * Math.sin(node.phi) * Math.cos(node.theta);
    const y = radius * Math.cos(node.phi);
    const z = radius * Math.sin(node.phi) * Math.sin(node.theta);

    // Billboarding Logic: Counter-rotate element so it always faces screen
    // We apply the globe's rotation in reverse to the element
    const billboardTransform = `rotateY(${-rotation.y}deg) rotateX(${-rotation.x}deg)`;

    return (
        <div
            className="absolute top-1/2 left-1/2 will-change-transform preserve-3d"
            style={{
                transform: `translate3d(${x}px, ${y}px, ${z}px)`,
                zIndex: isActive ? 1000 : undefined
            }}
        >
            <div 
                className="preserve-3d transition-all duration-500 ease-out"
                style={{ transform: billboardTransform }}
                onClick={(e) => { e.stopPropagation(); onSelect(); }}
            >
                {/* Active Card State */}
                <AnimatePresence>
                {isActive && (
                    <motion.div 
                        initial={{ scale: 0, opacity: 0, y: 0 }}
                        animate={{ 
                            scale: 1, 
                            opacity: 1, 
                            y: -80, // Shift up so the "connector" points to the node location
                            boxShadow: [
                                "0 0 20px rgba(0,255,255,0.2)",
                                "0 0 40px rgba(0,255,255,0.4)",
                                "0 0 20px rgba(0,255,255,0.2)"
                            ]
                        }}
                        transition={{ 
                            scale: { type: "spring", stiffness: 260, damping: 20 },
                            opacity: { duration: 0.2 },
                            boxShadow: { duration: 2, repeat: Infinity, ease: "easeInOut" }
                        }}
                        exit={{ scale: 0, opacity: 0, y: 0 }}
                        className="w-56 bg-zinc-950/90 border border-cyan-500/50 rounded-xl backdrop-blur-md overflow-hidden flex flex-col relative cursor-default origin-bottom shadow-2xl"
                    >
                        {/* Header */}
                        <div className="flex items-center justify-between px-3 py-2 border-b border-cyan-500/20 bg-gradient-to-r from-cyan-950/50 to-transparent">
                            <div className="flex items-center gap-2">
                                <div className="p-1 rounded bg-black/40 border border-cyan-500/30">
                                    <Icon className="w-3 h-3" style={{ color: config.color }} />
                                </div>
                                <span className="text-[10px] font-bold text-white tracking-widest font-mono uppercase">{config.label}</span>
                            </div>
                            <div className="flex items-center gap-1.5">
                                <span className="text-[8px] text-cyan-500 font-mono">LIVE</span>
                                <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse shadow-[0_0_5px_#22c55e]" />
                            </div>
                        </div>
                        
                        {/* Body */}
                        <div className="h-32 bg-black/40 relative">
                             {/* Scanline */}
                             <div className="absolute inset-0 bg-[linear-gradient(transparent_50%,rgba(0,0,0,0.5)_50%)] bg-[length:100%_4px] pointer-events-none opacity-20"></div>
                             <ChatWindow app={node.app} />
                        </div>

                        {/* Connector Line to surface */}
                        <div className="absolute top-full left-1/2 w-[1px] h-12 bg-gradient-to-b from-cyan-500 to-transparent -translate-x-1/2 opacity-70" />
                        
                        {/* Anchor Point with Pulse */}
                        <div className="absolute top-[calc(100%+48px)] left-1/2 -translate-x-1/2 flex items-center justify-center pointer-events-none">
                            <div className="w-2 h-2 bg-white rounded-full shadow-[0_0_10px_#fff] relative z-10" />
                            <div className="absolute w-8 h-8 bg-cyan-500/40 rounded-full animate-ping" />
                            <div className="absolute w-16 h-16 bg-cyan-500/10 rounded-full animate-pulse" />
                        </div>
                    </motion.div>
                )}
                </AnimatePresence>

                {/* Inactive Point State */}
                {!isActive && (
                    <div className="group cursor-pointer relative flex items-center justify-center">
                        {/* Glow Halo */}
                        <div className="absolute w-8 h-8 bg-cyan-500/20 rounded-full blur-md scale-0 group-hover:scale-100 transition-transform duration-300" />
                        
                        {/* The Dot */}
                        <div 
                            className="w-1.5 h-1.5 rounded-full bg-white shadow-[0_0_5px_#00FFFF] transition-all duration-300 group-hover:bg-cyan-400 group-hover:scale-150" 
                            style={{ 
                                backgroundColor: node.app === 'system' ? '#ff0050' : (Math.random() > 0.5 ? '#00FFFF' : 'white') 
                            }}
                        />
                        
                        {/* Tooltip on Hover */}
                        <div className="absolute bottom-full mb-3 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-all duration-200 transform translate-y-2 group-hover:translate-y-0 px-2 py-1 bg-black/90 border border-cyan-500/30 rounded text-[9px] text-cyan-300 whitespace-nowrap pointer-events-none backdrop-blur-sm shadow-[0_0_10px_rgba(0,255,255,0.2)]">
                            ID: {node.id} // {config.label}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

// --- Main Scene ---

export const Matrix3DScene: React.FC = () => {
    const containerRef = useRef<HTMLDivElement>(null);
    const [activeIndex, setActiveIndex] = useState<number | null>(null);
    const [rotation, setRotation] = useState({ x: 0, y: 0 });
    const [targetRotation, setTargetRotation] = useState<{x: number, y: number} | null>(null);
    const [isHovering, setIsHovering] = useState(false);

    // Mouse Interaction
    const mouseX = useMotionValue(0);
    const mouseY = useMotionValue(0);
    const dampX = useSpring(mouseX, { stiffness: 30, damping: 20 });
    const dampY = useSpring(mouseY, { stiffness: 30, damping: 20 });
    
    // Zoom Animation
    const sceneScale = useSpring(1, { stiffness: 100, damping: 20 });

    // Generate Globe Nodes (Fibonacci Sphere)
    const nodes = useMemo(() => {
        const count = 60; // Number of points
        const result: IDeviceNode[] = [];
        const apps: AppType[] = ['wechat', 'telegram', 'whatsapp', 'alipay'];
        const goldenRatio = (1 + 5 ** 0.5) / 2;

        for (let i = 0; i < count; i++) {
            const i2 = i + 0.5;
            const phi = Math.acos(1 - 2 * i2 / count);
            const theta = 2 * Math.PI * i2 / goldenRatio;
            
            result.push({
                id: i,
                app: i % 15 === 0 ? 'system' : apps[i % apps.length],
                phi,
                theta
            });
        }
        return result;
    }, []);

    // Handle Selection & Auto-Centering
    const handleSelectNode = (node: IDeviceNode) => {
        setActiveIndex(node.id);
        sceneScale.set(1.3); // Zoom in
        
        // Calculate Target Rotation to center the node
        // Theta = Longitude (0..2PI)
        // Phi = Latitude (0..PI, 0 is North Pole)
        
        // Target Y: We want the node's theta to be at -90deg (facing front Z+) relative to rotation
        const thetaDeg = (node.theta * 180) / Math.PI;
        let targetY = 90 - thetaDeg;
        
        // Normalize nearest rotation to avoid wild spins
        const currentY = rotation.y;
        const cycle = Math.floor(currentY / 360);
        targetY += cycle * 360;
        
        // Find shortest path
        const diff = targetY - currentY;
        if (diff > 180) targetY -= 360;
        else if (diff < -180) targetY += 360;
        
        // Target X: 
        // Phi=0 (North) -> needs X=90 to face front?
        // Default View (X=0) looks at Equator (Phi=90).
        // If node is at Phi (e.g. 45), we need to tilt up by (90-45) = 45.
        // So RotX should be Phi_deg - 90.
        const phiDeg = (node.phi * 180) / Math.PI;
        const targetX = phiDeg - 90;

        setTargetRotation({ x: targetX, y: targetY });
    };

    const handleDeselect = () => {
        if (activeIndex !== null) {
            setActiveIndex(null);
            setTargetRotation(null);
            sceneScale.set(1); // Zoom out
        }
    };

    // Animation Loop
    useAnimationFrame((t) => {
        if (activeIndex !== null && targetRotation) {
            // Auto-Center Animation (Smooth Lerp)
            setRotation(prev => ({
                x: prev.x + (targetRotation.x - prev.x) * 0.05,
                y: prev.y + (targetRotation.y - prev.y) * 0.05
            }));
        } else if (!isHovering) {
            // Auto Rotate
            setRotation(prev => ({
                x: dampY.get() * 20,
                y: (prev.y + 0.2) % 360
            }));
        } else {
            // Mouse Control
            setRotation(prev => ({
                x: dampY.get() * 45,
                y: prev.y + (dampX.get() * 2)
            }));
        }
    });

    const handleMouseMove = (e: React.MouseEvent) => {
        if (!containerRef.current) return;
        const rect = containerRef.current.getBoundingClientRect();
        const x = (e.clientX - rect.left) / rect.width - 0.5;
        const y = (e.clientY - rect.top) / rect.height - 0.5;
        mouseX.set(x);
        mouseY.set(y);
    };

    return (
        <div 
            ref={containerRef}
            className="relative w-full h-[600px] overflow-hidden bg-black border border-white/5 rounded-2xl group cursor-move perspective-container"
            onMouseMove={handleMouseMove}
            onMouseEnter={() => setIsHovering(true)}
            onMouseLeave={() => {
                setIsHovering(false);
                mouseX.set(0);
                mouseY.set(0);
            }}
            onClick={handleDeselect}
            style={{ perspective: '1000px' }}
        >
            {/* Background Grid */}
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(6,182,212,0.15)_0%,transparent_70%)] pointer-events-none" />

            {/* 3D Scene Container */}
            <motion.div
                className="w-full h-full relative preserve-3d flex items-center justify-center"
                style={{
                    scale: sceneScale,
                    rotateX: rotation.x, // Using Framer Motion style prop for rotation would be better for performance, but we are using state for global rotation logic
                    rotateY: rotation.y,
                    transform: `rotateX(${rotation.x}deg) rotateY(${rotation.y}deg)`, // Explicit transform string for React state
                    transition: isHovering ? 'transform 0.1s linear' : 'none'
                }}
            >
                {/* 1. Wireframe Skeleton */}
                <GlobeWireframe />

                {/* 2. Nodes Distributed on Sphere */}
                {nodes.map((node) => (
                    <GlobeNode
                        key={node.id}
                        node={node}
                        radius={200}
                        rotation={rotation}
                        isActive={activeIndex === node.id}
                        onSelect={() => handleSelectNode(node)}
                    />
                ))}
                
                {/* 3. Internal Core */}
                <div className="absolute w-20 h-20 bg-cyan-500 rounded-full blur-xl opacity-20 animate-pulse" />
                <div className="absolute w-4 h-4 bg-white rounded-full blur-sm opacity-80" />
            </motion.div>

            {/* UI Overlay */}
            <div className="absolute bottom-6 left-6 z-20 font-mono text-xs pointer-events-none select-none">
                 <div className="flex items-center gap-2 text-cyan-400 mb-1">
                    <Globe className="w-4 h-4 animate-spin-slow" />
                    <span className="tracking-widest">GLOBAL_NET_MATRIX</span>
                 </div>
                 <div className="text-zinc-500">NODES_ONLINE: {nodes.length}</div>
                 <div className="text-zinc-500 flex items-center gap-2">
                    STATUS: <span className="text-green-500">SECURE</span>
                    <ShieldCheck className="w-3 h-3 text-green-500" />
                 </div>
            </div>

            <div className="absolute top-6 right-6 z-20 font-mono text-[10px] text-cyan-500/50 pointer-events-none text-right">
                <div>LAT: {rotation.x.toFixed(1)}°</div>
                <div>LNG: {rotation.y.toFixed(1)}°</div>
                <div>ZOOM: {Math.round(sceneScale.get() * 100)}%</div>
            </div>

             <style>{`
                .preserve-3d { transform-style: preserve-3d; }
                .perspective-container { perspective: 1000px; }
            `}</style>
        </div>
    );
};

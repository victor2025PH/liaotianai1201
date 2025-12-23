import React, { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';

const FutureParticles: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const mouseRef = useRef({ x: -1000, y: -1000 });

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const handleMouseMove = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      mouseRef.current = {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top
      };
    };

    container.addEventListener('mousemove', handleMouseMove);
    return () => container.removeEventListener('mousemove', handleMouseMove);
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let particles: Particle[] = [];
    
    // Set canvas size
    const setSize = () => {
      const parent = canvas.parentElement;
      if (parent) {
        canvas.width = parent.clientWidth;
        canvas.height = parent.clientHeight;
      }
    };
    setSize();

    class Particle {
      x: number;
      y: number;
      vx: number;
      vy: number;
      size: number;
      color: string;
      baseX: number;
      baseY: number;

      constructor() {
        this.x = Math.random() * canvas.width;
        this.y = Math.random() * canvas.height;
        this.baseX = this.x;
        this.baseY = this.y;
        this.vx = (Math.random() - 0.5) * 0.5;
        this.vy = (Math.random() - 0.5) * 0.5;
        this.size = Math.random() * 2 + 1;
        // Cyberpunk colors: Cyan and Purple
        this.color = Math.random() > 0.5 ? '#00f3ff' : '#bc13fe'; 
      }

      update() {
        this.x += this.vx;
        this.y += this.vy;

        // Bounce off edges
        if (this.x < 0 || this.x > canvas.width) this.vx *= -1;
        if (this.y < 0 || this.y > canvas.height) this.vy *= -1;
      }

      draw() {
        if (!ctx) return;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fillStyle = this.color;
        ctx.fill();
      }
    }

    const init = () => {
      particles = [];
      const density = 8000; 
      const numberOfParticles = Math.floor((canvas.width * canvas.height) / density);
      
      for (let i = 0; i < numberOfParticles; i++) {
        particles.push(new Particle());
      }
    };

    const animate = () => {
      if (!ctx) return;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      // Draw connections
      ctx.lineWidth = 0.5;
      
      // Connect to other particles
      for (let i = 0; i < particles.length; i++) {
        const p1 = particles[i];
        
        // Connect to mouse
        const dxMouse = mouseRef.current.x - p1.x;
        const dyMouse = mouseRef.current.y - p1.y;
        const distMouse = Math.sqrt(dxMouse*dxMouse + dyMouse*dyMouse);
        if (distMouse < 150) {
            ctx.beginPath();
            ctx.strokeStyle = `rgba(255, 255, 255, ${1 - distMouse/150})`;
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(mouseRef.current.x, mouseRef.current.y);
            ctx.stroke();
        }

        for (let j = i; j < particles.length; j++) {
          const p2 = particles[j];
          const dx = p1.x - p2.x;
          const dy = p1.y - p2.y;
          const distance = Math.sqrt(dx * dx + dy * dy);
          const maxDistance = 120;

          if (distance < maxDistance) {
            ctx.beginPath();
            const opacity = 1 - distance / maxDistance;
            ctx.strokeStyle = `rgba(0, 243, 255, ${opacity * 0.2})`;
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();
          }
        }
      }

      particles.forEach(p => {
        p.update();
        p.draw();
      });
      
      animationFrameId = requestAnimationFrame(animate);
    };

    const handleResize = () => {
      setSize();
      init();
    };

    window.addEventListener('resize', handleResize);
    init();
    animate();

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <section ref={containerRef} className="relative h-[400px] md:h-[500px] w-full bg-black overflow-hidden flex items-center justify-center border-t border-b border-white/5 group cursor-crosshair">
        <canvas ref={canvasRef} className="absolute inset-0" />
        
        {/* Vignette & Scanlines */}
        <div className="absolute inset-0 bg-gradient-to-t from-dark-bg via-transparent to-dark-bg pointer-events-none" />
        <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 pointer-events-none"></div>

        <div className="relative z-10 text-center px-4 mix-blend-screen pointer-events-none">
            <motion.h2 
                initial={{ opacity: 0, scale: 0.9, filter: 'blur(10px)' }}
                whileInView={{ opacity: 1, scale: 1, filter: 'blur(0px)' }}
                viewport={{ once: true }}
                transition={{ duration: 0.8 }}
                className="text-5xl md:text-7xl lg:text-8xl font-black mb-6 tracking-tighter text-white"
                style={{ 
                    textShadow: "0 0 40px rgba(0, 243, 255, 0.5)",
                }}
            >
                <motion.span
                    animate={{ 
                        textShadow: [
                            "0 0 20px rgba(0, 243, 255, 0.5)",
                            "2px 2px 0px rgba(188, 19, 254, 0.5)",
                            "-2px -2px 0px rgba(0, 243, 255, 0.5)",
                            "0 0 20px rgba(0, 243, 255, 0.5)"
                        ]
                    }}
                    transition={{
                        duration: 3,
                        repeat: Infinity,
                        repeatType: "reverse"
                    }}
                >
                THE FUTURE IS NOW
                </motion.span>
            </motion.h2>
            <motion.p
                 initial={{ opacity: 0, y: 20 }}
                 whileInView={{ opacity: 1, y: 0 }}
                 viewport={{ once: true }}
                 transition={{ duration: 0.8, delay: 0.2 }}
                 className="text-neon-blue font-mono text-sm md:text-lg tracking-[0.2em] uppercase border border-neon-blue/30 inline-block px-6 py-2 rounded-full bg-neon-blue/5 backdrop-blur-md"
            >
                Experience the cutting edge of Web3 and Telegram Mini Apps
            </motion.p>
        </div>
    </section>
  );
};

export default FutureParticles;
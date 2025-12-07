#!/bin/bash
# Fix slider component issue and deploy frontend

set -e

echo "========================================"
echo "Fix Slider Component and Deploy"
echo "========================================"
echo ""

cd ~/liaotian || exit 1

# Step 1: Ensure slider component exists
echo "=== Step 1: Check Slider Component ==="
SLIDER_PATH="saas-demo/src/components/ui/slider.tsx"

if [[ -f "$SLIDER_PATH" ]]; then
    echo "✅ Slider component file exists"
    cat "$SLIDER_PATH" | head -5
else
    echo "❌ Slider component missing, creating..."
    mkdir -p saas-demo/src/components/ui
    
    cat > "$SLIDER_PATH" << 'EOF'
"use client"

import * as React from "react"
import * as SliderPrimitive from "@radix-ui/react-slider"

import { cn } from "@/lib/utils"

const Slider = React.forwardRef<
  React.ElementRef<typeof SliderPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof SliderPrimitive.Root>
>(({ className, ...props }, ref) => (
  <SliderPrimitive.Root
    ref={ref}
    className={cn(
      "relative flex w-full touch-none select-none items-center",
      className
    )}
    {...props}
  >
    <SliderPrimitive.Track className="relative h-1.5 w-full grow overflow-hidden rounded-full bg-primary/20">
      <SliderPrimitive.Range className="absolute h-full bg-primary" />
    </SliderPrimitive.Track>
    <SliderPrimitive.Thumb className="block h-4 w-4 rounded-full border border-primary/50 bg-background shadow transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50" />
  </SliderPrimitive.Root>
))
Slider.displayName = SliderPrimitive.Root.displayName

export { Slider }
EOF
    echo "✅ Slider component created"
fi

# Step 2: Ensure slider dependency in package.json
echo ""
echo "=== Step 2: Check Slider Dependency ==="
cd saas-demo

if grep -q "@radix-ui/react-slider" package.json; then
    echo "✅ @radix-ui/react-slider already in package.json"
else
    echo "⚠️  @radix-ui/react-slider not in package.json, adding..."
    npm install @radix-ui/react-slider --save
    echo "✅ Dependency added"
fi

# Step 3: Install all dependencies
echo ""
echo "=== Step 3: Install All Dependencies ==="
npm install

# Step 4: Clean and build
echo ""
echo "=== Step 4: Clean and Build ==="
rm -rf .next node_modules/.cache

echo "Building frontend..."
if npm run build; then
    echo "✅ Frontend build successful"
    BUILD_SUCCESS=true
else
    echo "❌ Frontend build failed"
    BUILD_SUCCESS=false
    exit 1
fi

# Step 5: Start frontend service
if [[ "$BUILD_SUCCESS" == true ]]; then
    echo ""
    echo "=== Step 5: Start Frontend Service ==="
    
    # Clean old processes
    pkill -f "next-server" 2>/dev/null || true
    pkill -f "node.*next" 2>/dev/null || true
    sleep 3
    
    # Start service
    nohup npm start > /tmp/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo "✅ Frontend service started, PID: $FRONTEND_PID"
    
    # Wait and verify
    sleep 10
    
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo "✅ Frontend process is running"
        
        # Check port
        if ss -tlnp | grep :3000 > /dev/null 2>&1; then
            echo "✅ Port 3000 is listening"
        else
            echo "⚠️  Port 3000 not listening yet"
        fi
        
        # Check HTTP response
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "000")
        if [[ "$HTTP_CODE" = "200" ]] || [[ "$HTTP_CODE" = "301" ]] || [[ "$HTTP_CODE" = "302" ]]; then
            echo "✅ Frontend service responding (HTTP $HTTP_CODE)"
        else
            echo "⚠️  Frontend service not responding (HTTP $HTTP_CODE)"
            echo "Check logs: tail -f /tmp/frontend.log"
        fi
    else
        echo "❌ Frontend process exited"
        echo "Check logs:"
        tail -50 /tmp/frontend.log
    fi
fi

echo ""
echo "========================================"
echo "✅ Fix and Deploy Complete!"
echo "========================================"

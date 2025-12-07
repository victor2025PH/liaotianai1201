#!/bin/bash
# Complete fix for slider component and build issues

set -e

echo "========================================="
echo "Complete Fix and Build Script"
echo "========================================="
echo ""

cd ~/liaotian || exit 1

# Step 1: Fix multiple lockfile issue
echo "=== Step 1: Fix Multiple Lockfile Issue ==="
if [ -f "/home/ubuntu/package-lock.json" ]; then
    echo "⚠️  Found extra lockfile at /home/ubuntu/package-lock.json"
    echo "Moving it to backup..."
    mv /home/ubuntu/package-lock.json /home/ubuntu/package-lock.json.backup 2>/dev/null || true
    echo "✅ Extra lockfile moved"
fi

# Step 2: Ensure slider component exists
echo ""
echo "=== Step 2: Ensure Slider Component Exists ==="
SLIDER_PATH="saas-demo/src/components/ui/slider.tsx"
mkdir -p saas-demo/src/components/ui

# Try to checkout from Git first
if git checkout origin/main -- "$SLIDER_PATH" 2>/dev/null; then
    echo "✅ Slider component checked out from Git"
else
    echo "⚠️  Could not checkout from Git, creating manually..."
    
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
    echo "✅ Slider component created manually"
fi

# Verify file exists
if [ -f "$SLIDER_PATH" ]; then
    echo "✅ Slider component file verified: $(ls -lh "$SLIDER_PATH" | awk '{print $9, $5}')"
    echo "   First 3 lines:"
    head -3 "$SLIDER_PATH" | sed 's/^/   /'
else
    echo "❌ Slider component file still missing!"
    exit 1
fi

# Step 3: Ensure package.json has slider dependency
echo ""
echo "=== Step 3: Ensure Slider Dependency ==="
cd saas-demo

# Checkout package.json from Git to ensure it's up to date
git checkout origin/main -- package.json 2>/dev/null || true

if grep -q "@radix-ui/react-slider" package.json; then
    echo "✅ @radix-ui/react-slider already in package.json"
else
    echo "⚠️  Adding @radix-ui/react-slider to package.json..."
    npm install @radix-ui/react-slider --save
    echo "✅ Dependency added"
fi

# Step 4: Clean and reinstall dependencies
echo ""
echo "=== Step 4: Clean and Reinstall Dependencies ==="
rm -rf node_modules/.cache .next
echo "✅ Cache cleaned"

npm install
echo "✅ Dependencies installed"

# Step 5: Verify slider dependency is installed
echo ""
echo "=== Step 5: Verify Slider Dependency ==="
if npm list @radix-ui/react-slider > /dev/null 2>&1; then
    echo "✅ @radix-ui/react-slider is installed"
    npm list @radix-ui/react-slider | head -2
else
    echo "⚠️  Installing @radix-ui/react-slider..."
    npm install @radix-ui/react-slider --save
    echo "✅ Installed"
fi

# Step 6: Build frontend
echo ""
echo "=== Step 6: Build Frontend ==="
rm -rf .next node_modules/.cache

echo "Starting build..."
if npm run build; then
    echo ""
    echo "✅ Build successful!"
    
    # Verify .next directory exists
    if [ -d ".next" ]; then
        echo "✅ .next directory exists"
        echo "   Build output size: $(du -sh .next 2>/dev/null | cut -f1)"
    else
        echo "❌ .next directory missing after build!"
        exit 1
    fi
else
    echo ""
    echo "❌ Build failed!"
    echo "Please check the error messages above."
    exit 1
fi

# Step 7: Stop old processes and start frontend
echo ""
echo "=== Step 7: Start Frontend Service ==="
pkill -f "next-server" 2>/dev/null || true
pkill -f "node.*next" 2>/dev/null || true
sleep 3

echo "Starting frontend service..."
nohup npm start > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend started, PID: $FRONTEND_PID"

# Wait for service to start
echo "Waiting for service to start..."
sleep 15

# Step 8: Verify service
echo ""
echo "=== Step 8: Verify Service ==="

# Check process
if ps -p $FRONTEND_PID > /dev/null 2>&1; then
    echo "✅ Frontend process is running (PID: $FRONTEND_PID)"
else
    echo "❌ Frontend process exited"
    echo "Last 50 lines of log:"
    tail -50 /tmp/frontend.log
    exit 1
fi

# Check port
if ss -tlnp | grep :3000 > /dev/null 2>&1; then
    echo "✅ Port 3000 is listening"
else
    echo "⚠️  Port 3000 not listening yet, waiting 10 more seconds..."
    sleep 10
    if ss -tlnp | grep :3000 > /dev/null 2>&1; then
        echo "✅ Port 3000 is now listening"
    else
        echo "❌ Port 3000 still not listening"
    fi
fi

# Check HTTP response
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "000")
if [[ "$HTTP_CODE" = "200" ]] || [[ "$HTTP_CODE" = "301" ]] || [[ "$HTTP_CODE" = "302" ]]; then
    echo "✅ Frontend service responding (HTTP $HTTP_CODE)"
else
    echo "⚠️  Frontend service not responding yet (HTTP $HTTP_CODE)"
    echo "   This might be normal if it's still starting. Check logs:"
    echo "   tail -f /tmp/frontend.log"
fi

echo ""
echo "========================================="
echo "✅ All Steps Completed!"
echo "========================================="
echo ""
echo "Frontend URL: http://localhost:3000"
echo "Network URL: http://10.56.130.4:3000"
echo "Log file: /tmp/frontend.log"
echo ""
echo "To check logs: tail -f /tmp/frontend.log"
echo "To check status: ps aux | grep 'node.*next' | grep -v grep"

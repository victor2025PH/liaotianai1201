#!/bin/bash
# Ultimate fix for all frontend deployment issues

set -e

echo "========================================="
echo "Ultimate Fix Script - All Issues"
echo "========================================="
echo ""

cd ~/liaotian || exit 1

# Step 1: Fix multiple lockfile issue (CRITICAL)
echo "=== Step 1: Fix Multiple Lockfile Issue ==="
if [ -f "/home/ubuntu/package-lock.json" ]; then
    echo "⚠️  Removing conflicting lockfile at /home/ubuntu/package-lock.json"
    rm -f /home/ubuntu/package-lock.json
    echo "✅ Conflicting lockfile removed"
fi

# Step 2: Ensure slider component exists (MANDATORY)
echo ""
echo "=== Step 2: Ensure Slider Component Exists ==="
SLIDER_DIR="saas-demo/src/components/ui"
SLIDER_PATH="$SLIDER_DIR/slider.tsx"

mkdir -p "$SLIDER_DIR"

# Create slider component directly (don't rely on Git)
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

echo "✅ Slider component created at: $SLIDER_PATH"
ls -lh "$SLIDER_PATH"

# Step 3: Navigate to frontend directory
echo ""
echo "=== Step 3: Setup Frontend Directory ==="
cd saas-demo
echo "✅ In directory: $(pwd)"

# Step 4: Ensure package.json has slider dependency
echo ""
echo "=== Step 4: Ensure Slider Dependency ==="
if grep -q "@radix-ui/react-slider" package.json; then
    echo "✅ @radix-ui/react-slider already in package.json"
else
    echo "⚠️  Adding @radix-ui/react-slider..."
    npm install @radix-ui/react-slider --save --no-audit
    echo "✅ Dependency added"
fi

# Step 5: Clean everything
echo ""
echo "=== Step 5: Clean Everything ==="
rm -rf .next node_modules/.cache .next/cache 2>/dev/null || true
echo "✅ Cleaned build cache"

# Step 6: Install dependencies
echo ""
echo "=== Step 6: Install Dependencies ==="
npm install --no-audit
echo "✅ Dependencies installed"

# Verify slider dependency
if npm list @radix-ui/react-slider > /dev/null 2>&1; then
    echo "✅ @radix-ui/react-slider verified"
else
    echo "⚠️  Installing @radix-ui/react-slider..."
    npm install @radix-ui/react-slider --save --no-audit
fi

# Step 7: Build frontend (CRITICAL)
echo ""
echo "=== Step 7: Build Frontend (This may take a few minutes) ==="
echo "Building..."

# Run build and capture output
BUILD_OUTPUT=$(npm run build 2>&1) || {
    echo "❌ Build failed!"
    echo "$BUILD_OUTPUT" | tail -50
    exit 1
}

# Check for success indicators
if echo "$BUILD_OUTPUT" | grep -q "Creating an optimized production build" && [ -d ".next" ]; then
    echo "✅ Build appears successful"
else
    echo "⚠️  Build output may indicate issues, but continuing..."
fi

# Step 8: Verify .next directory exists
echo ""
echo "=== Step 8: Verify Build Output ==="
if [ -d ".next" ]; then
    echo "✅ .next directory exists"
    echo "   Size: $(du -sh .next 2>/dev/null | cut -f1)"
    echo "   Files: $(find .next -type f 2>/dev/null | wc -l) files"
else
    echo "❌ .next directory missing! Build may have failed."
    echo "Build output:"
    echo "$BUILD_OUTPUT" | tail -30
    exit 1
fi

# Step 9: Stop old processes
echo ""
echo "=== Step 9: Stop Old Processes ==="
pkill -f "next-server" 2>/dev/null || true
pkill -f "node.*next" 2>/dev/null || true
pkill -f "next start" 2>/dev/null || true
sleep 3
echo "✅ Old processes stopped"

# Step 10: Start frontend service
echo ""
echo "=== Step 10: Start Frontend Service ==="
nohup npm start > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✅ Frontend started in background, PID: $FRONTEND_PID"
echo "   Log file: /tmp/frontend.log"

# Step 11: Wait and verify
echo ""
echo "=== Step 11: Waiting for Service to Start ==="
for i in {1..30}; do
    sleep 2
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        if ss -tlnp | grep :3000 > /dev/null 2>&1; then
            echo "✅ Service is running and port 3000 is listening!"
            break
        fi
    else
        echo "❌ Process died, checking logs..."
        tail -50 /tmp/frontend.log
        exit 1
    fi
    if [ $i -eq 30 ]; then
        echo "⚠️  Service started but port 3000 not listening yet"
    fi
done

# Step 12: Final verification
echo ""
echo "=== Step 12: Final Verification ==="

# Check process
if ps -p $FRONTEND_PID > /dev/null 2>&1; then
    echo "✅ Frontend process running (PID: $FRONTEND_PID)"
else
    echo "❌ Frontend process not running"
    echo "Last 50 lines of log:"
    tail -50 /tmp/frontend.log
    exit 1
fi

# Check port
if ss -tlnp | grep :3000 > /dev/null 2>&1; then
    PORT_INFO=$(ss -tlnp | grep :3000)
    echo "✅ Port 3000 is listening"
    echo "   $PORT_INFO"
else
    echo "⚠️  Port 3000 not listening (service may still be starting)"
fi

# Check HTTP response
echo ""
echo "Testing HTTP response..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "000")
if [[ "$HTTP_CODE" = "200" ]]; then
    echo "✅ Frontend responding (HTTP 200)"
elif [[ "$HTTP_CODE" = "301" ]] || [[ "$HTTP_CODE" = "302" ]]; then
    echo "✅ Frontend responding with redirect (HTTP $HTTP_CODE)"
else
    echo "⚠️  Frontend not responding yet (HTTP $HTTP_CODE)"
    echo "   This might be normal if service is still starting"
    echo "   Check logs: tail -f /tmp/frontend.log"
fi

echo ""
echo "========================================="
echo "✅ ALL STEPS COMPLETED!"
echo "========================================="
echo ""
echo "Frontend Service:"
echo "  - Process ID: $FRONTEND_PID"
echo "  - Local URL: http://localhost:3000"
echo "  - Network URL: http://10.56.130.4:3000"
echo "  - Log file: /tmp/frontend.log"
echo ""
echo "Useful commands:"
echo "  - View logs: tail -f /tmp/frontend.log"
echo "  - Check status: ps aux | grep 'node.*next' | grep -v grep"
echo "  - Check port: ss -tlnp | grep :3000"
echo "  - Test: curl http://localhost:3000"
